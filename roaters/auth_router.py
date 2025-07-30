from fastapi import APIRouter, HTTPException, Depends, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import jwt
from database import get_repositories
import logging

logger = logging.getLogger(__name__)

# Создаем роутер
auth_router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Настройки JWT
SECRET_KEY = "your-secret-key-here"  # В продакшене использовать безопасный ключ
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 часа
REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 дней

# Схема безопасности
security = HTTPBearer()

# Pydantic модели
class UserLogin(BaseModel):
    username: str
    password: str

class UserLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict

class TokenRefresh(BaseModel):
    refresh_token: str

class TokenRefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class LogoutResponse(BaseModel):
    message: str

class UserInfo(BaseModel):
    id: int
    username: str
    role: str
    email: Optional[str] = None

# Функции для работы с JWT токенами
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Создает JWT access токен"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """Создает JWT refresh токен"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, token_type: str = "access"):
    """Проверяет JWT токен"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type_check: str = payload.get("type")
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недействительный токен",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if token_type_check != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный тип токена",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен истек",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Получает текущего пользователя из токена"""
    payload = verify_token(credentials.credentials, "access")
    username: str = payload.get("sub")
    user_id: int = payload.get("user_id")
    role: str = payload.get("role")
    
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "username": username,
        "user_id": user_id,
        "role": role
    }

# Роуты аутентификации
@auth_router.post("/login", response_model=UserLoginResponse)
async def login(user_data: UserLogin, response: Response):
    """Аутентификация пользователя с выдачей JWT токенов"""
    try:
        logger.info(f"🔐 Попытка входа пользователя: {user_data.username}")
        
        # Получаем репозитории
        promo_repo, informing_repo, user_repo = get_repositories()
        
        # Поиск пользователя в базе данных
        user = user_repo.get_user_by_credentials(user_data.username, user_data.password)
        
        if not user:
            logger.warning(f"❌ Неудачная попытка входа для пользователя: {user_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверное имя пользователя или пароль"
            )
        
        # Создаем данные для токенов
        token_data = {
            "sub": user.get('login'),
            "user_id": user.get('id'),
            "role": user.get('role', 'user')
        }
        
        # Создаем токены
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # Вычисляем время истечения access токена
        expires_in = ACCESS_TOKEN_EXPIRE_MINUTES * 60  # в секундах
        
        # Устанавливаем cookies для автоматической аутентификации
        response.set_cookie(
            key="access_token",
            value=access_token,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # в секундах
            httponly=True,
            secure=False,  # установите True для HTTPS
            samesite="lax"
        )
        
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # в секундах
            httponly=True,
            secure=False,  # установите True для HTTPS
            samesite="lax"
        )
        
        logger.info(f"✅ Успешный вход пользователя: {user_data.username}")
        
        return UserLoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=expires_in,
            user={
                "id": user.get('id'),
                "username": user.get('login'),
                "role": user.get('role', 'user'),
                "email": user.get('mail')
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при попытке входа: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при попытке входа: {str(e)}"
        )

@auth_router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(token_data: TokenRefresh, response: Response = None):
    """Обновление access токена с помощью refresh токена"""
    try:
        logger.info("🔄 Попытка обновления токена")
        
        # Проверяем refresh токен
        payload = verify_token(token_data.refresh_token, "refresh")
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        role: str = payload.get("role")
        
        # Создаем новый access токен
        token_data_new = {
            "sub": username,
            "user_id": user_id,
            "role": role
        }
        
        access_token = create_access_token(token_data_new)
        expires_in = ACCESS_TOKEN_EXPIRE_MINUTES * 60  # в секундах
        
        # Обновляем cookie с новым access токеном
        if response:
            response.set_cookie(
                key="access_token",
                value=access_token,
                max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                httponly=True,
                secure=False,
                samesite="lax"
            )
        
        logger.info(f"✅ Токен успешно обновлен для пользователя: {username}")
        
        return TokenRefreshResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обновлении токена: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении токена: {str(e)}"
        )

@auth_router.post("/refresh-cookie", response_model=TokenRefreshResponse)
async def refresh_token_from_cookie(request: Request, response: Response):
    """Обновление access токена с помощью refresh токена из cookies"""
    try:
        logger.info("🔄 Попытка обновления токена из cookies")
        
        # Получаем refresh токен из cookies
        refresh_token_cookie = request.cookies.get("refresh_token")
        
        if not refresh_token_cookie:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh токен отсутствует"
            )
        
        # Проверяем refresh токен
        payload = verify_token(refresh_token_cookie, "refresh")
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        role: str = payload.get("role")
        
        # Создаем новый access токен
        token_data_new = {
            "sub": username,
            "user_id": user_id,
            "role": role
        }
        
        access_token = create_access_token(token_data_new)
        expires_in = ACCESS_TOKEN_EXPIRE_MINUTES * 60  # в секундах
        
        # Обновляем cookie с новым access токеном
        response.set_cookie(
            key="access_token",
            value=access_token,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            httponly=True,
            secure=False,
            samesite="lax"
        )
        
        logger.info(f"✅ Токен успешно обновлен из cookies для пользователя: {username}")
        
        return TokenRefreshResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обновлении токена из cookies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении токена: {str(e)}"
        )

@auth_router.post("/logout", response_model=LogoutResponse)
async def logout(request: Request, response: Response):
    """Выход из системы (удаляем токены из cookies)"""
    try:
        # Пытаемся получить информацию о пользователе из токена (если он есть)
        current_user = None
        try:
            auth_header = request.headers.get("Authorization")
            token = None
            
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
            else:
                token = request.cookies.get("access_token")
            
            if token:
                payload = verify_token(token, "access")
                current_user = {
                    "username": payload.get("sub"),
                    "user_id": payload.get("user_id")
                }
                logger.info(f"🚪 Выход пользователя: {current_user['username']}")
        except:
            logger.info("🚪 Выход пользователя без аутентификации")
        
        # Удаляем cookies в любом случае
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        
        # В реальном приложении здесь можно добавить токен в черный список
        # или сохранить информацию о выходе в базе данных
        
        return LogoutResponse(
            message="Успешный выход из системы"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при выходе: {str(e)}")
        # Даже если произошла ошибка, удаляем cookies
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        
        return LogoutResponse(
            message="Выход выполнен"
        )

@auth_router.post("/logout-force", response_model=LogoutResponse)
async def logout_force(response: Response):
    """Принудительный выход из системы (без проверки аутентификации)"""
    try:
        logger.info("🚪 Принудительный выход из системы")
        
        # Удаляем cookies в любом случае
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        
        return LogoutResponse(
            message="Выход выполнен"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при принудительном выходе: {str(e)}")
        # Даже если произошла ошибка, удаляем cookies
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        
        return LogoutResponse(
            message="Выход выполнен"
        )

@auth_router.get("/me", response_model=UserInfo)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Получение информации о текущем пользователе"""
    try:
        logger.info(f"👤 Запрос информации о пользователе: {current_user['username']}")
        
        # Получаем репозитории
        promo_repo, informing_repo, user_repo = get_repositories()
        
        # Получаем полную информацию о пользователе
        user = user_repo.get_user_by_id(current_user['user_id'])
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        return UserInfo(
            id=user.get('id'),
            username=user.get('login'),
            role=user.get('role', 'user'),
            email=user.get('mail')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения информации о пользователе: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения информации о пользователе: {str(e)}"
        )

@auth_router.post("/verify")
async def verify_access_token(current_user: dict = Depends(get_current_user)):
    """Проверка валидности access токена"""
    try:
        logger.info(f"✅ Проверка токена для пользователя: {current_user['username']}")
        
        return {
            "valid": True,
            "user": current_user
        }
        
    except Exception as e:
        logger.error(f"Ошибка проверки токена: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка проверки токена: {str(e)}"
        )

@auth_router.get("/check")
async def check_auth_status(request: Request):
    """Проверка статуса аутентификации (для фронтенда)"""
    try:
        # Сначала пробуем получить токен из заголовка Authorization
        auth_header = request.headers.get("Authorization")
        token = None
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            logger.info("🔍 Токен получен из заголовка Authorization")
        else:
            # Если нет в заголовке, пробуем из cookies
            token = request.cookies.get("access_token")
            if token:
                logger.info("🔍 Токен получен из cookies")
        
        if not token:
            logger.info("🔍 Токен отсутствует")
            return {
                "authenticated": False,
                "user": None,
                "message": "Токен отсутствует"
            }
        
        # Проверяем токен
        payload = verify_token(token, "access")
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        
        logger.info(f"🔍 Проверка статуса аутентификации для пользователя: {username}")
        
        # Получаем репозитории для получения полной информации о пользователе
        promo_repo, informing_repo, user_repo = get_repositories()
        
        # Получаем полную информацию о пользователе
        user = user_repo.get_user_by_id(user_id)
        
        if not user:
            return {
                "authenticated": False,
                "user": None,
                "message": "Пользователь не найден в базе данных"
            }
        
        return {
            "authenticated": True,
            "user": {
                "id": user.get('id'),
                "username": user.get('login'),
                "role": user.get('role', 'user'),
                "email": user.get('mail'),
                "server": user.get('server'),
                "accountId": user.get('accountId'),
                "api_key": user.get('api_key'),
                "token_trello": user.get('token_trello')
            }
        }
        
    except HTTPException as e:
        # Если токен невалидный, возвращаем статус неаутентифицированного пользователя
        logger.info("🔍 Токен невалидный")
        return {
            "authenticated": False,
            "user": None,
            "message": "Токен невалидный"
        }
    except Exception as e:
        logger.error(f"Ошибка проверки статуса аутентификации: {str(e)}")
        return {
            "authenticated": False,
            "user": None,
            "error": str(e)
        } 