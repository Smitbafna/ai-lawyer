from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # bcrypt has a 72-byte limit on password length; truncate if necessary
    if len(plain_password.encode("utf-8")) > 72:
        plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    """Create access token - simplified for demo."""
    import jwt
    from datetime import datetime, timedelta

    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded = jwt.encode(to_encode, "secret-key", algorithm="HS256")
    return encoded


def get_current_user(user_email: str = "") -> dict:
    """Get current user - simplified for demo."""
    return {"email": user_email, "full_name": ""}
