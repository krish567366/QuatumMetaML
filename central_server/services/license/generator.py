from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from pydantic import BaseModel
import base64
from datetime import datetime, timedelta
from ..security.crypto import derive_hardware_key, verify_hardware_signature

class QuantumLicense(BaseModel):
    features: list
    expiry: datetime
    hw_signature: str
    max_instances: int = 1

class QuantumLicenseManager:
    def __init__(self, master_key: bytes):
        self.master_key = master_key
        
    def generate_license(self, features: list, days: int, machine_id: str) -> str:
        hw_key = derive_hardware_key(machine_id, self.master_key)
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
            hw_key = derive_hardware_key(machine_id, self.master_key)
            fernet = Fernet(hw_key)
            decrypted = fernet.decrypt(base64.urlsafe_b64decode(license_key))
            license_data = QuantumLicense.parse_raw(decrypted)
            
            if datetime.utcnow() > license_data.expiry:
                raise ValueError("License expired")
                
            if not verify_hardware_signature(machine_id, license_data.hw_signature):
                raise ValueError("Hardware mismatch")
                
            return license_data
        except Exception as e:
            raise ValueError(f"Invalid license: {str(e)}")