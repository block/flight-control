from cryptography.fernet import Fernet

from orchestrator.config import settings


def _get_fernet() -> Fernet:
    key = settings.master_key
    if not key:
        raise ValueError("ORCH_MASTER_KEY must be set for credential encryption")
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_value(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    return _get_fernet().decrypt(ciphertext.encode()).decode()


def generate_key() -> str:
    return Fernet.generate_key().decode()
