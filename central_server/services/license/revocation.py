from web3 import Web3
import os
import json

class BlockchainLedger:
    def __init__(self, node_url: str):
        self.web3 = Web3(Web3.HTTPProvider(node_url))
        self.contract = self._load_contract()
    
    def _load_contract(self):
        return self.web3.eth.contract(
            address=os.getenv('CONTRACT_ADDR'),
            abi=json.load(open('license_abi.json'))
        )
    
    def revoke_license(self, license_id: str) -> str:
        tx_hash = self.contract.functions.revoke(license_id).transact()
        return tx_hash.hex()
    
    def is_revoked(self, license_id: str) -> bool:
        return self.contract.functions.isRevoked(license_id).call()