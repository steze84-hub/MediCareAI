from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.core.config import settings
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None, platform: str = "patient") -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    to_encode.update({"exp": expire, "type": "access", "platform": platform})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def create_refresh_token(data: dict, platform: str = "patient") -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh", "platform": platform})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role", "patient")  # Default to patient for backward compatibility
        platform: str = payload.get("platform", "patient")  # Default to patient for backward compatibility
        token_type_claim: str = payload.get("type")
        
        if user_id is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if token_type_claim != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return {"user_id": uuid.UUID(user_id), "email": email, "role": role, "platform": platform}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_platform_token(token: str, expected_platform: str = None) -> dict:
    """
    Verify platform access token and validate platform permissions
    验证平台访问令牌并验证平台权限
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        platform: str = payload.get("platform", "patient")  # Default to patient for backward compatibility
        
        if expected_platform and platform != expected_platform:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Expected platform: {expected_platform}, got: {platform}",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return {"platform": platform, "valid": True}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate platform token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_token_for_user(user_id: uuid.UUID, email: str, role: str = "patient", platform: str = "patient") -> dict:
    """Create tokens for user with role and platform information / 为用户创建包含角色和平台信息的令牌"""
    access_token = create_access_token(
        data={"sub": str(user_id), "email": email, "role": role}, 
        platform=platform
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user_id), "email": email, "role": role}, 
        platform=platform
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.jwt_access_token_expire_minutes * 60,
        "role": role,
        "platform": platform
    }