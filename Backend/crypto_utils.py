"""RSA helpers. Private key material is never embedded in source code."""

import base64

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from config import settings


def get_private_key():
    path = settings.rsa_private_key_path
    if not path.is_file():
        raise RuntimeError(
            f"RSA private key not found at {path}. Generate a new project key and set RSA_PRIVATE_KEY_PATH."
        )
    return serialization.load_pem_private_key(path.read_bytes(), password=None, backend=default_backend())


def get_public_key():
    return get_private_key().public_key()


def decrypt_data(encrypted_data: str) -> str:
    if not encrypted_data:
        return encrypted_data
    try:
        encrypted_bytes = base64.b64decode(encrypted_data, validate=True)
        private_key = get_private_key()
        if len(encrypted_bytes) != private_key.key_size // 8:
            raise ValueError("Encrypted credential has an invalid length")
        decrypted = private_key.decrypt(
            encrypted_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return decrypted.decode("utf-8")
    except Exception as exc:
        raise ValueError("Credential decryption failed") from exc
