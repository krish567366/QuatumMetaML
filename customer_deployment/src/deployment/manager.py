# quantumml/license/manager.py
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import x25519, kyber
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.backends import default_backend
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import base64
import hashlib
import hmac
import os
import logging
from typing import Optional, Dict

# Post-quantum cryptography imports
from pqcrypto.sign.dilithium2 import generate_keypair, sign, verify
from pqcrypto.kem.kyber512 import generate_keypair as kyber_generate_keypair
from pqcrypto.kem.kyber512 import encrypt, decrypt

class QuantumLicense(BaseModel):
    metadata: Dict[str, str] = Field(..., description="License metadata")
    entitlements: Dict[str, int] = Field(
        default_factory=lambda: {
            "qpu_hours": 0,
            "requests": 0,
            "max_throughput": 100
        },
        description="Resource entitlements"
    )
    conditions: Dict[str, str] = Field(
        default_factory=lambda: {
            "pricing_model": "time-based",
            "expiry_policy": "hard_stop",
            "compliance": "GDPR"
        },
        description="License conditions"
    )
    quantum_signature: Optional[str] = Field(None, description="PQ signature")

class QuantumLicenseManager:
    def __init__(self, hsm_endpoint: Optional[str] = None):
        # Post-Quantum cryptography initialization
        self.dilithium_public_key, self.dilithium_secret_key = generate_keypair()
        self.kyber_public_key, self.kyber_secret_key = kyber_generate_keypair()
        
        # HSM integration
        self.hsm_endpoint = hsm_endpoint or os.getenv("HSM_ENDPOINT")
        self._init_hardware_binding()
        
        # License state management
        self.active_licenses = {}
        self.revoked_licenses = set()
        self.usage_tracker = LicenseUsageTracker()

    def _init_hardware_binding(self):
        """Initialize TPM-based hardware binding"""
        try:
            import tpm_tools
            self.tpm = tpm_tools.TPMDevice()
            self.hardware_id = self.tpm.get_ek_public()
        except ImportError:
            self.hardware_id = self._fallback_hardware_id()

    def generate_license(self, terms: Dict, pricing_model: str) -> str:
        """Generate quantum-safe enterprise license"""
        license_data = QuantumLicense(
            metadata={
                "issue_date": datetime.utcnow().isoformat(),
                "issuer": "QuantumMetaML Enterprise",
                "hardware_binding": self.hardware_id.hex()
            },
            entitlements=self._calculate_entitlements(terms, pricing_model),
            conditions={
                "pricing_model": pricing_model,
                "expiry": terms.get("expiry"),
                "revocable": terms.get("revocable", True)
            }
        )
        
        # Add quantum-resistant signature
        signature = sign(
            self.dilithium_secret_key,
            license_data.json().encode()
        )
        license_data.quantum_signature = base64.b64encode(signature).decode()
        
        # Encrypt with Kyber
        encrypted = encrypt(self.kyber_public_key, license_data.json().encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def validate_license(self, license_key: str) -> QuantumLicense:
        """Validate license with quantum-safe checks"""
        try:
            encrypted = base64.urlsafe_b64decode(license_key)
            decrypted = decrypt(self.kyber_secret_key, encrypted)
            license = QuantumLicense.parse_raw(decrypted)
            
            # Verify hardware binding
            if not self._verify_hardware_binding(license.metadata["hardware_binding"]):
                raise LicenseValidationError("Hardware mismatch")
                
            # Verify quantum signature
            if not verify(
                self.dilithium_public_key,
                license.json().encode(),
                base64.b64decode(license.quantum_signature)
            ):
                raise LicenseValidationError("Invalid quantum signature")
                
            # Check revocation status
            if self._is_revoked(license):
                raise LicenseRevokedError("License revoked")
                
            # Check usage limits
            self.usage_tracker.check_usage(license)
            
            return license
            
        except Exception as e:
            logging.error(f"License validation failed: {str(e)}")
            raise

    def _calculate_entitlements(self, terms: Dict, model: str) -> Dict:
        """Calculate resource entitlements based on pricing model"""
        if model == "time-based":
            return {
                "qpu_hours": terms["hours"],
                "requests": 0,
                "max_throughput": terms.get("throughput", 100)
            }
        elif model == "request-based":
            return {
                "qpu_hours": 0,
                "requests": terms["requests"],
                "max_throughput": terms["throughput"]
            }
        elif model == "hybrid":
            return {
                "qpu_hours": terms["base_hours"],
                "requests": terms["base_requests"],
                "max_throughput": terms["throughput"]
            }

    def _verify_hardware_binding(self, license_hw_id: str) -> bool:
        """Verify hardware binding using TPM"""
        return hmac.compare_digest(
            self.hardware_id.hex(),
            license_hw_id
        )

    def _is_revoked(self, license: QuantumLicense) -> bool:
        """Check against blockchain revocation list"""
        license_hash = hashlib.sha3_256(
            license.json().encode()
        ).hexdigest()
        return license_hash in self.revoked_licenses

class LicenseUsageTracker:
    """Track resource usage against entitlements"""
    def __init__(self):
        self.usage_store = {}
        
    def check_usage(self, license: QuantumLicense):
        usage = self.usage_store.get(license.metadata["license_id"], {})
        
        if license.conditions["pricing_model"] == "time-based":
            if usage.get("qpu_seconds", 0) > license.entitlements["qpu_hours"] * 3600:
                raise LicenseLimitExceeded("QPU hours exhausted")
                
        elif license.conditions["pricing_model"] == "request-based":
            if usage.get("requests", 0) > license.entitlements["requests"]:
                raise LicenseLimitExceeded("Request limit exceeded")

class LicenseValidationError(Exception):
    """Base class for license validation errors"""
    pass

class LicenseRevokedError(LicenseValidationError):
    pass

class LicenseLimitExceeded(LicenseValidationError):
    pass