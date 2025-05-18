from pydantic import BaseSettings
from typing import Optional

class QuantumConfig(BaseSettings):
    quantum_hardware: Optional[str] = None
    max_shots: int = 100000
    error_mitigation: bool = True
    auto_scale: bool = True
    
    class Config:
        env_file = ".env.quantum"
        secrets_dir = "/run/secrets/quantum"

class SecurityConfig(BaseSettings):
    hsm_module: str = "/usr/lib/softhsm/libsofthsm2.so"
    fips_mode: bool = True
    quantum_encryption: bool = False
    
    class Config:
        env_file = ".env.security"