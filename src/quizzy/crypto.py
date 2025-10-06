from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES
import base64

from .config import config


# Helper functions for padding
def pad(s: bytes) -> bytes:
    return s + (16 - len(s) % 16) * chr(16 - len(s) % 16).encode()


def unpad(s: str) -> str:
    return s[: -ord(s[-1:])]


# AES encryption
def encrypt_payload(plaintext: str) -> str:
    key = config.AES_SECRET.encode()  # Ensure 32 bytes (AES-256)
    iv = get_random_bytes(16)  # Random IV
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(plaintext.encode()))
    return base64.b64encode(iv + ciphertext).decode()


# AES decryption
def decrypt_payload(cipher: str) -> str:
    key = config.AES_SECRET.encode()  # Ensure 32 bytes (AES-256)
    ciphertext = base64.b64decode(cipher)
    iv = ciphertext[:16]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = cipher.decrypt(ciphertext[16:])
    return unpad(plaintext.decode())
