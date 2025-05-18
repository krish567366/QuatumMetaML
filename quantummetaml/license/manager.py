# quantumml/license/manager.py
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend
import base64
import hashlib
import requests
import os
from datetime import datetime, timedelta
from pydantic import BaseModel

class QuantumLicense(BaseModel):
    features: list
    expiry: datetime
    hw_signature: str
    max_instances: int = 1

class QuantumLicenseManager:
    def __init__(self, master_key: bytes):
        self.private_key = x25519.X25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        self.master_key = master_key
        
    def generate_license(self, features: list, days: int, machine_id: str) -> str:
        hw_key = self._derive_hardware_key(machine_id)
        fernet = Fernet(hw_key)
        
        license_data = QuantumLicense(
            features=features,
            expiry=datetime.utcnow() + timedelta(days=days),
            hw_signature=self._create_hw_signature(machine_id)
        )
        
        encrypted = fernet.encrypt(license_data.json().encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def validate_license(self, license_key: str, machine_id: str) -> QuantumLicense:
        try:
            hw_key = self._derive_hardware_key(machine_id)
            fernet = Fernet(hw_key)
            decrypted = fernet.decrypt(base64.urlsafe_b64decode(license_key))
            license_data = QuantumLicense.parse_raw(decrypted)
            
            if datetime.utcnow() > license_data.expiry:
                raise ValueError("License expired")
                
            if not self._verify_hw_signature(machine_id, license_data.hw_signature):
                raise ValueError("Hardware mismatch")
                
            return license_data
        except Exception as e:
            raise ValueError(f"Invalid license: {str(e)}")

    def _derive_hardware_key(self, machine_id: str) -> bytes:
        shared_key = self.private_key.exchange(
            x25519.X25519PublicKey.from_public_bytes(machine_id.encode())
        )
        return HKDF(
            algorithm=hashes.SHA512(),
            length=32,
            salt=self.master_key,
            info=b'quantum_license'
        ).derive(shared_key)