import hmac
import hashlib
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import requests
from pydantic import BaseModel

class LicenseRequest(BaseModel):
    machine_id: str
    features: list
    expiration: datetime

class QuantumLicenseValidator:
    def __init__(self, master_key: str):
        self.kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(),
            length=32,
            salt=b"quantum_ent_salt",
            iterations=600000
        )
        self.fernet = Fernet(base64.urlsafe_b64encode(self.kdf.derive(master_key.encode())))
        
    def generate_license(self, request: LicenseRequest) -> str:
        license_data = request.json().encode()
        return self.fernet.encrypt(license_data).decode()

    def validate_license(self, license_key: str, machine_id: str) -> bool:
        try:
            data = self.fernet.decrypt(license_key.encode()).decode()
            license = LicenseRequest.parse_raw(data)
            return (
                license.machine_id == machine_id and
                license.expiration > datetime.utcnow()
            )
        except Exception as e:
            return False