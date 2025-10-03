from cryptography.fernet import Fernet
import os
import bcrypt
import base64

# Get Fernet key from environment
FERNET_SECRET = os.getenv("FERNET_SECRET")

# Validate and initialize Fernet
if not FERNET_SECRET:
    raise ValueError(
        "FERNET_SECRET environment variable is not set. "
        "Please set it to a 32-byte base64-encoded key. "
        "Run 'python generate_fernet_key.py' to generate one."
    )

try:
    fernet = Fernet(FERNET_SECRET.encode())
except Exception as e:
    raise ValueError(
        f"Invalid FERNET_SECRET: {e}. "
        "The key must be 32 url-safe base64-encoded bytes. "
        "Run 'python generate_fernet_key.py' to generate a valid key."
    )

def encrypt_token(token: str) -> str:
    """Encrypt a token using Fernet"""
    try:
        return fernet.encrypt(token.encode()).decode()
    except Exception as e:
        raise ValueError(f"Failed to encrypt token: {e}")

def decrypt_token(encrypted: str) -> str:
    """Decrypt a token using Fernet"""
    try:
        return fernet.decrypt(encrypted.encode()).decode()
    except Exception as e:
        raise ValueError(f"Failed to decrypt token: {e}")

def encrypt_data(data: str) -> str:
    """Encrypt any string data"""
    try:
        return fernet.encrypt(data.encode()).decode()
    except Exception as e:
        raise ValueError(f"Failed to encrypt data: {e}")

def decrypt_data(encrypted_data: str) -> str:
    """Decrypt any string data"""
    try:
        return fernet.decrypt(encrypted_data.encode()).decode()
    except Exception as e:
        raise ValueError(f"Failed to decrypt data: {e}")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
