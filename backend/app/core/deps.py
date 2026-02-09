from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.models import User
from app.core.security import verify_token
import uuid

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    token_data = verify_token(token)
    
    stmt = select(User).where(User.id == token_data["user_id"])
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Store platform info on user object for later use
    user._platform = token_data.get("platform", "patient")
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not verified"
        )
    return current_user


# Role-based permission dependencies / 基于角色的权限依赖

async def require_role(required_roles: list[str]):
    """Generic role checker factory / 通用角色检查工厂"""
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(required_roles)}"
            )
        return current_user
    return role_checker


async def require_patient(current_user: User = Depends(get_current_user)) -> User:
    """Require patient role AND patient platform / 要求患者角色和患者平台"""
    if current_user.role != 'patient':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Patient role required."
        )
    
    current_platform = getattr(current_user, '_platform', 'patient')
    if current_platform != 'patient':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Patient platform required."
        )
    
    return current_user


async def require_doctor(current_user: User = Depends(get_current_user)) -> User:
    """Require doctor role AND doctor platform / 要求医生角色和医生平台"""
    if current_user.role not in ['doctor', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Doctor role required."
        )
    
    current_platform = getattr(current_user, '_platform', 'patient')
    if current_platform != 'doctor':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Doctor platform required."
        )
    
    return current_user


async def require_verified_doctor(current_user: User = Depends(get_current_active_user)) -> User:
    """Require verified doctor role / 要求已认证的医生角色"""
    if current_user.role != 'doctor':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Doctor role required."
        )
    if not current_user.is_verified_doctor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Doctor verification pending."
        )
    return current_user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role AND admin platform / 要求管理员角色和管理员平台"""
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin role required."
        )
    
    current_platform = getattr(current_user, '_platform', 'patient')
    if current_platform != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin platform required."
        )
    
    return current_user


async def require_patient_or_doctor(current_user: User = Depends(get_current_active_user)) -> User:
    """Require patient or doctor role / 要求患者或医生角色"""
    if current_user.role not in ['patient', 'doctor']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Patient or doctor role required."
        )
    return current_user


# Platform-based permission dependencies / 基于平台的权限依赖

async def get_current_platform(current_user: User = Depends(get_current_user)) -> str:
    """Get current platform from token / 从令牌获取当前平台"""
    return getattr(current_user, '_platform', 'patient')


async def require_platform(required_platforms: list[str]):
    """Generic platform checker factory / 通用平台检查工厂"""
    async def platform_checker(current_user: User = Depends(get_current_user)) -> User:
        current_platform = getattr(current_user, '_platform', 'patient')
        if current_platform not in required_platforms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required platforms: {', '.join(required_platforms)}"
            )
        return current_user
    return platform_checker


async def require_patient_platform(current_user: User = Depends(get_current_user)) -> User:
    """Require patient platform / 要求患者平台"""
    current_platform = getattr(current_user, '_platform', 'patient')
    if current_platform != 'patient':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Patient platform required."
        )
    return current_user


async def require_doctor_platform(current_user: User = Depends(get_current_user)) -> User:
    """Require doctor platform / 要求医生平台"""
    current_platform = getattr(current_user, '_platform', 'patient')
    if current_platform != 'doctor':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Doctor platform required."
        )
    return current_user


async def require_admin_platform(current_user: User = Depends(get_current_user)) -> User:
    """Require admin platform / 要求管理员平台"""
    current_platform = getattr(current_user, '_platform', 'patient')
    if current_platform != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin platform required."
        )
    return current_user


# New platform access decorators / 新的平台访问装饰器

async def require_platform_access(platform: str):
    """
    Generic platform access checker factory / 通用平台访问检查工厂
    Validates user has permission to access the specified platform
    验证用户是否有权限访问指定平台
    """
    async def platform_access_checker(current_user: User = Depends(get_current_user)) -> User:
        # Platform permission rules based on user role
        # 基于用户角色的平台权限规则
        
        if platform == "admin" and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问管理员平台"
            )
        elif platform == "doctor" and current_user.role not in ["doctor", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问医生平台"
            )
        elif platform == "patient" and current_user.role not in ["patient", "doctor", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问患者平台"
            )
        
        # Check current platform matches requested platform
        # 检查当前平台是否与请求平台匹配
        current_platform = getattr(current_user, '_platform', 'patient')
        if current_platform != platform:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"当前平台为 {current_platform}，无法访问 {platform} 平台。请切换平台。"
            )
        
        return current_user
    
    return platform_access_checker


async def allow_multi_platform(current_user: User = Depends(get_current_user)) -> User:
    """
    Allow admins to access multiple platforms / 允许管理员跨平台访问
    This decorator permits admin users to bypass strict platform checking
    此装饰器允许管理员用户绕过严格的平台检查
    """
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可进行跨平台访问"
        )
    
    return current_user


# Enhanced role dependencies with platform validation / 带平台验证的增强角色依赖

async def require_patient_role_and_platform(current_user: User = Depends(get_current_user)) -> User:
    """Require patient role AND patient platform / 要求患者角色和患者平台"""
    if current_user.role != 'patient':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Patient role required."
        )
    
    current_platform = getattr(current_user, '_platform', 'patient')
    if current_platform != 'patient':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Patient platform required."
        )
    
    return current_user


async def require_doctor_role_and_platform(current_user: User = Depends(get_current_user)) -> User:
    """Require doctor role AND doctor platform / 要求医生角色和医生平台"""
    if current_user.role not in ['doctor', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Doctor role required."
        )
    
    current_platform = getattr(current_user, '_platform', 'patient')
    if current_platform != 'doctor':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Doctor platform required."
        )
    
    return current_user


async def require_admin_role_and_platform(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role AND admin platform / 要求管理员角色和管理员平台"""
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin role required."
        )
    
    current_platform = getattr(current_user, '_platform', 'patient')
    if current_platform != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin platform required."
        )
    
    return current_user