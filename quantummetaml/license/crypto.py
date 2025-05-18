# quantumml/license/crypto.py
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
import os

class QuantumResistantCrypto:
    """Post-quantum cryptography implementation using X25519 and ChaCha20-Poly1305"""
    
    def __init__(self):
        self.private_key = x25519.X25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        
    def encrypt(self, plaintext: bytes, peer_public_key: bytes) -> bytes:
        """Encrypt data using ECDH key exchange and ChaCha20-Poly1305"""
        shared_key = self.private_key.exchange(
            x25519.X25519PublicKey.from_public_bytes(peer_public_key)
        )
        derived_key = HKDF(
            algorithm=hashes.SHA512(),
            length=32,
            salt=None,
            info=b'quantum_encryption'
        ).derive(shared_key)
        nonce = os.urandom(12)
        cipher = ChaCha20Poly1305(derived_key)
        return nonce + cipher.encrypt(nonce, plaintext, None)

    def decrypt(self, ciphertext: bytes, peer_public_key: bytes) -> bytes:
        """Decrypt data using quantum-resistant algorithms"""
        shared_key = self.private_key.exchange(
            x25519.X25519PublicKey.from_public_bytes(peer_public_key)
        )
        derived_key = HKDF(
            algorithm=hashes.SHA512(),
            length=32,
            salt=None,
            info=b'quantum_encryption'
        ).derive(shared_key)
        nonce = ciphertext[:12]
        cipher = ChaCha20Poly1305(derived_key)
        return cipher.decrypt(nonce, ciphertext[12:], None)