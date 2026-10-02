"""RSA helpers. Private key material is never embedded in source code."""

import base64
import logging

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

from config import settings


logger = logging.getLogger(__name__)


def get_private_key():
    path = settings.rsa_private_key_path
    try:
        key_data = path.read_bytes()
    except FileNotFoundError as exc:
        logger.error("RSA private key file is missing: %s", path)
        raise RuntimeError(f"RSA private key file is missing: {path}") from exc
    except PermissionError as exc:
        logger.error("RSA private key file is not readable: %s", path)
        raise RuntimeError(f"RSA private key file is not readable: {path}") from exc
    except OSError as exc:
        logger.error("RSA private key file could not be read: %s (%s)", path, type(exc).__name__)
        raise RuntimeError(f"RSA private key file could not be read: {path}") from exc

    try:
        private_key = serialization.load_pem_private_key(
            key_data, password=None, backend=default_backend()
        )
    except (TypeError, ValueError) as exc:
        logger.error("RSA private key file is invalid or unsupported: %s", path)
        raise RuntimeError(f"RSA private key file is invalid or unsupported: {path}") from exc

    if not isinstance(private_key, RSAPrivateKey):
        logger.error("Configured private key is not an RSA key: %s", path)
        raise RuntimeError(f"Configured private key is not an RSA key: {path}")

    return private_key


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
