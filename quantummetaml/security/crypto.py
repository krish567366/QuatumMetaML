# quantumml/security/crypto.py
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

class QuantumResistantCrypto:
    def __init__(self):
        self.private_key = x25519.X25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()

    def encrypt_payload(self, data: bytes, peer_public_key: bytes) -> bytes:
        shared_key = self.private_key.exchange(
            x25519.X25519PublicKey.from_public_bytes(peer_public_key)
        )
        derived_key = HKDF(
            algorithm=hashes.SHA512(),
            length=32,
            salt=None,
            info=b'quantum_deployment'
        ).derive(shared_key)
        return ChaCha20Poly1305(derived_key).encrypt(
            nonce=os.urandom(12),
            data=data,
            associated_data=None
        )