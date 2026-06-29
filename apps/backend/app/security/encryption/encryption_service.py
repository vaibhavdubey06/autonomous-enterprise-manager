from cryptography.fernet import Fernet
from typing import Optional


class EncryptionService:
    def __init__(self, key: Optional[bytes] = None):
        # In a real app, this key should be managed securely (e.g., loaded from a KMS)
        # We generate a random key if none is provided, but it means encrypted data is lost on restart.
        self.key = key or Fernet.generate_key()
        self.fernet = Fernet(self.key)

    def encrypt(self, data: str) -> str:
        if not data:
            return data
        encrypted_bytes = self.fernet.encrypt(data.encode("utf-8"))
        return encrypted_bytes.decode("utf-8")

    def decrypt(self, encrypted_data: str) -> str:
        if not encrypted_data:
            return encrypted_data
        decrypted_bytes = self.fernet.decrypt(encrypted_data.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")

    def rotate_key(self, new_key: bytes):
        """Interface for future key rotation implementations"""
        pass


# Default service instance
encryption_service = EncryptionService()
