# app/core/security.py
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt
from app.core.config import settings


#Creates a password hashing configuration - Argon2 Hashing algorithm
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


#Hashes a plain text password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)



#Verifies a plain text password against the hash $argon2id$v=19$m=65536,t=3,p=4$...
def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


#Creates a JSON Web Token (JWT)
#Subject (who the token belongs to).
def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        {"sub": subject, "exp": expire},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


#Decodes a JWT token and returns the subject (user_id)-after exp time
def decode_token(token: str) -> str:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    return payload["sub"]  # returns user_id
