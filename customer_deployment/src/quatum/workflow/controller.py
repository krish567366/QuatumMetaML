# quantumml/workflow/controller.py
from enum import Enum, auto
from pydantic import BaseModel, validator
from typing import Dict, Any, Optional, List
import networkx as nx

class WorkflowStep(Enum):
    PREPROCESS = auto()
    MODEL_SELECTION = auto()
    TRAIN = auto()
    DEPLOY = auto()

class StepConfig(BaseModel):
    steps: List[WorkflowStep] = [
        WorkflowStep.PREPROCESS,
        WorkflowStep.MODEL_SELECTION,
        WorkflowStep.TRAIN,
        WorkflowStep.DEPLOY
    ]
    dependencies: Optional[Dict[WorkflowStep, List[WorkflowStep]]] = None
    
    @validator('dependencies', always=True)
    def set_default_dependencies(cls, v, values):
        return v or {
            WorkflowStep.MODEL_SELECTION: [WorkflowStep.PREPROCESS],
            WorkflowStep.TRAIN: [WorkflowStep.MODEL_SELECTION],
            WorkflowStep.DEPLOY: [WorkflowStep.TRAIN]
        }

class WorkflowState:
    def __init__(self):
        self.data = None
        self.features = None
        self.model = None
        self.deployment = None
        self.metrics = {}

class QuantumWorkflow:
    def __init__(self, config: StepConfig):
        self.config = config
        self.state = WorkflowState()
        self.graph = self._build_dependency_graph()
        
    def _build_dependency_graph(self) -> nx.DiGraph:
        """Build workflow DAG from dependencies"""
        G = nx.DiGraph()
        for step in self.config.steps:
            G.add_node(step)
            if step in self.config.dependencies:
                for dep in self.config.dependencies[step]:
                    if dep in self.config.steps:
                        G.add_edge(dep, step)
        return G

    async def execute(self, raw_data: Any) -> Dict[str, Any]:
        """Execute selected workflow steps in topological order"""
        from .steps import (
            preprocess_step,
            model_selection_step,
            train_step,
            deploy_step
        )
        
        step_handlers = {
            WorkflowStep.PREPROCESS: preprocess_step,
            WorkflowStep.MODEL_SELECTION: model_selection_step,
            WorkflowStep.TRAIN: train_step,
            WorkflowStep.DEPLOY: deploy_step
        }
        
        for step in nx.topological_sort(self.graph):
            if step not in self.config.steps:
                continue
                
            handler = step_handlers[step]
            self.state = await handler(self.state, raw_data)
            
            if self.state.error:
                raise WorkflowError(f"Step {step.name} failed: {self.state.error}")
                
        return self._format_output()

    def _format_output(self) -> Dict[str, Any]:
        """Generate output based on executed steps"""
        output = {}
        if WorkflowStep.PREPROCESS in self.config.steps:
            output['features'] = self.state.features
        if WorkflowStep.TRAIN in self.config.steps:
            output['model'] = self.state.model
        if WorkflowStep.DEPLOY in self.config.steps:
            output['deployment'] = self.state.deployment
        output['metrics'] = self.state.metrics
        return output

# Step implementations (quantumml/workflow/steps.py)
async def preprocess_step(state: WorkflowState, raw_data: Any) -> WorkflowState:
    """Quantum-enhanced preprocessing"""
    from .preprocessing import QuantumFeatureEngineer
    
    if state.data is None:
        state.data = raw_data
        
    engineer = QuantumFeatureEngineer()
    state.features = engineer.fit_transform(state.data)
    state.metrics['preprocess'] = engineer.get_metrics()
    return state

async def model_selection_step(state: WorkflowState, _) -> WorkflowState:
    """Quantum-aware model selection"""
    from .selection import QuantumModelSelector
    
    selector = QuantumModelSelector(state.features)
    state.model = selector.best_model()
    state.metrics['model_selection'] = selector.get_metrics()
    return state

async def train_step(state: WorkflowState, _) -> WorkflowState:
    """Quantum-optimized training"""
    from .training import QuantumTrainer
    
    trainer = QuantumTrainer(state.model)
    state.model = trainer.fit(state.features)
    state.metrics['training'] = trainer.get_metrics()
    return state

async def deploy_step(state: WorkflowState, _) -> WorkflowState:
    """Flexible deployment handler"""
    from ..deployment import DeploymentManager
    
    manager = DeploymentManager()
    state.deployment = await manager.deploy(state.model)
    state.metrics['deployment'] = manager.get_metrics()
    return state