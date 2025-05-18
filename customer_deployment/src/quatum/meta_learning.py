# quantumml/meta_learning.py
from Meta_Learn import MAML, PrototypicalNetwork
from qiskit_machine_learning.neural_networks import QuantumNeuralNetwork
import torch
import torch.nn as nn

class QuantumMetaLearner:
    """Quantum-enhanced meta-learning with hardware adaptation"""
    
    def __init__(self, n_qubits, license_manager):
        self.license = license_manager
        self.qnn = QuantumNeuralNetwork(n_qubits)
        self.classical_nn = self._create_hybrid_model(n_qubits)
        
    def _create_hybrid_model(self, n_qubits):
        return nn.Sequential(
            QuantumEmbeddingLayer(self.qnn),
            nn.Linear(2**n_qubits, 128),
            nn.ReLU(),
            nn.Linear(128, 10)
        )

    def adapt(self, model, tasks):
        """Hardware-aware meta-learning adaptation"""
        if not self.license.validate("quantum_meta"):
            raise PermissionError("Quantum meta-learning requires enterprise license")
            
        # Quantum attention mechanism
        attention_weights = self._quantum_attention(tasks)
        return MAML(model).adapt_with_attention(tasks, attention_weights)

    def _quantum_attention(self, tasks):
        """Quantum-enhanced attention mechanism"""
        encoded_tasks = self.qnn.encode(tasks)
        return torch.sigmoid(self.qnn(encoded_tasks))