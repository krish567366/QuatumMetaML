from cryptography.hazmat.primitives.asymmetric import kyber

class OfflineValidator:
    def __init__(self, license_key: str):
        self.license = self._decrypt_license(license_key)
        
    def _decrypt_license(self, key: str) -> dict:
        ciphertext = base64.b64decode(key)[:kyber.CIPHERTEXT_BYTES]
        shared_secret = base64.b64decode(key)[kyber.CIPHERTEXT_BYTES:]
        return json.loads(kyber.dec(ciphertext, self._get_hw_key(), shared_secret))
    
    def check_entitlement(self, feature: str) -> bool:
        return feature in self.license["features"]
    
    def deduct_credits(self, amount: float) -> bool:
        if self.license["quantum_credits"] >= amount:
            self.license["quantum_credits"] -= amount
            return True
        return False