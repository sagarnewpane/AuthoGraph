"""Authenticated encryption for new images; read support for legacy CBC files."""
import base64
import hashlib
import os
from cryptography.fernet import Fernet, MultiFernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from django.conf import settings

MAGIC = b'AGCM1'


def key_cipher():
    master = settings.IMAGE_MASTER_KEY or settings.SECRET_KEY
    masters = [master]
    previous = getattr(settings, 'IMAGE_PREVIOUS_MASTER_KEY', '')
    if previous:
        masters.append(previous)
    return MultiFernet([Fernet(base64.urlsafe_b64encode(hashlib.sha256(value.encode()).digest())) for value in masters])


def wrap_key(key):
    return 'wrapped:' + key_cipher().encrypt(key).decode()


def unwrap_key(value):
    return key_cipher().decrypt(value[8:].encode()) if value.startswith('wrapped:') else bytes.fromhex(value)


def encrypt_image(data, key):
    nonce = os.urandom(12)
    return MAGIC + nonce + AESGCM(key).encrypt(nonce, data, MAGIC)


def decrypt_image(data, key):
    if data.startswith(MAGIC):
        return AESGCM(key).decrypt(data[5:17], data[17:], MAGIC)
    return decrypt_aes_cbc(data, key)


def encrypt_aes_cbc(data, key):
    """Legacy helper retained for migrations and compatibility tests only."""
    iv = os.urandom(16)
    padder = padding.PKCS7(128).padder()
    padded = padder.update(data) + padder.finalize()
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    return iv + encryptor.update(padded) + encryptor.finalize()


def decrypt_aes_cbc(data, key):
    decryptor = Cipher(algorithms.AES(key), modes.CBC(data[:16])).decryptor()
    padded = decryptor.update(data[16:]) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(padded) + unpadder.finalize()
