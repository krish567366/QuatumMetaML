from hyqcopt import create_solver
from ..license.validator import LicenseValidator
import numpy as np

class QuantumInferenceEngine:
    def __init__(self, config):
        self.config = config
        self.license = LicenseValidator(config.license_key)
        self._kernel_solver = None

    def predict(self, model, X):
        if self.config.enable_quantum_kernel:
            if not self.license.validate("quantum_inference"):
                raise PermissionError("Quantum kernel requires inference license")
                
            if self._kernel_solver is None:
                self._kernel_solver = create_solver(
                    "quantum_kernel",
                    n_shots=1024
                )
            return self._kernel_solver.predict(model, X)
        else:
            return model.predict(X)

    def hybrid_predict(self, model, X):
        if not self.license.validate("hybrid_inference"):
            raise PermissionError("Hybrid inference requires enterprise license")
            
        classical_pred = model.predict(X)
        quantum_pred = self.predict(model, X)
        return 0.7 * classical_pred + 0.3 * quantum_pred