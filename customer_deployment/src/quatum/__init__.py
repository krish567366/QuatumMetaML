# QuantumMetaML-Commercial/quantumml/__init__.py
__version__ = "2.0.0"
__license__ = "Commercial"
__all__ = ['config', 'data_fetcher', 'automl', 'meta_learning', 'quantum', 'billing', 'license', 'api']

from .config import CommercialConfig
from .data_fetcher import EnterpriseDataLoader
from .automl import AutoMLEngine
from .meta_learning import MetaLearner
from .quantum import QuantumOptimizer