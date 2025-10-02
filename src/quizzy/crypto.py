import jwt

from .config import config


# Helper functions for padding
def pad(s: bytes) -> bytes:
    return s + (16 - len(s) % 16) * chr(16 - len(s) % 16).encode()


def unpad(s: str) -> str:
    return s[: -ord(s[-1:])]


# AES encryption
def encrypt_AES(plaintext: str) -> str:
    key = config.SECRET.encode()  # Ensure 32 bytes (AES-256)
    encoded = jwt.encode(plaintext, key, algorithm="HS256")
    return encoded


# AES decryption
def decrypt_AES(ciphertext_b64: str) -> str:
    key = config.SECRET.encode()  # Ensure 32 bytes (AES-256)
    dat = jwt.decode(ciphertext_b64, key, algorithms="HS256")
    return dat
