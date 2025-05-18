class HSMClient:
    """Mock HSM client for secure key operations"""
    def __init__(self, hsm_config: dict):
        self.hsm_connection = self._connect_hsm(hsm_config)
        
    def _connect_hsm(self, config):
        # Implementation would vary based on HSM vendor
        return MockHSMConnection(config)
    
    def get_master_key(self, key_id: str) -> bytes:
        """Retrieve master key from HSM without exposing it"""
        return self.hsm_connection.derive_key(key_id)