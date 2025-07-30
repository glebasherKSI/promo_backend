from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from roaters.auth_router import verify_token
import logging

logger = logging.getLogger(__name__)

# Схема безопасности
security = HTTPBearer()

async def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Middleware для проверки аутентификации пользователя"""
    try:
        # Проверяем токен
        payload = verify_token(credentials.credentials, "access")
        return payload
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется аутентификация",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def require_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Middleware для проверки прав администратора"""
    try:
        # Проверяем токен
        payload = verify_token(credentials.credentials, "access")
        
        # Проверяем роль пользователя
        role = payload.get("role")
        if role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для выполнения операции"
            )
        
        return payload
    except HTTPException:
        if isinstance(HTTPException, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется аутентификация",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Получает ID текущего пользователя из токена"""
    try:
        payload = verify_token(credentials.credentials, "access")
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недействительный токен",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется аутентификация",
            headers={"WWW-Authenticate": "Bearer"},
        ) 