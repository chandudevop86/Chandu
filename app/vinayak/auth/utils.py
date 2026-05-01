from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["django_pbkdf2_sha256"],  # ✅ THIS is the key
    deprecated="auto",
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

