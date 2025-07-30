from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List
from roaters.middleware import require_auth, require_admin, get_current_user_id
from roaters.auth_router import get_current_user
from database import get_repositories
import logging

logger = logging.getLogger(__name__)

# Создаем роутер для защищенных маршрутов
protected_router = APIRouter(prefix="/api/protected", tags=["protected"])

# Pydantic модели
class ProtectedData(BaseModel):
    message: str
    user_id: int

class AdminData(BaseModel):
    admin_message: str
    user_count: int

# Пример защищенного роута (требует аутентификации)
@protected_router.get("/data", response_model=ProtectedData)
async def get_protected_data(current_user: dict = Depends(get_current_user)):
    """Получение защищенных данных (требует аутентификации)"""
    try:
        logger.info(f"🔒 Запрос защищенных данных от пользователя: {current_user['username']}")
        
        return ProtectedData(
            message="Это защищенные данные, доступные только аутентифицированным пользователям",
            user_id=current_user['user_id']
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения защищенных данных: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения данных: {str(e)}"
        )

# Пример роута только для администраторов
@protected_router.get("/admin/data", response_model=AdminData)
async def get_admin_data(current_user: dict = Depends(require_admin)):
    """Получение данных администратора (требует роль admin)"""
    try:
        logger.info(f"👑 Запрос данных администратора от пользователя: {current_user['sub']}")
        
        # Получаем репозитории
        promo_repo, informing_repo, user_repo = get_repositories()
        
        # Получаем количество пользователей (пример административной функции)
        users = user_repo.get_all_users()
        user_count = len(users) if users else 0
        
        return AdminData(
            admin_message="Это данные администратора, доступные только пользователям с ролью admin",
            user_count=user_count
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения данных администратора: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения данных администратора: {str(e)}"
        )

# Пример роута с получением ID пользователя
@protected_router.get("/user/profile")
async def get_user_profile(user_id: int = Depends(get_current_user_id)):
    """Получение профиля пользователя по ID из токена"""
    try:
        logger.info(f"👤 Запрос профиля пользователя с ID: {user_id}")
        
        # Получаем репозитории
        promo_repo, informing_repo, user_repo = get_repositories()
        
        # Получаем данные пользователя
        user = user_repo.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        return {
            "id": user.get('id'),
            "username": user.get('login'),
            "role": user.get('role', 'user'),
            "email": user.get('mail'),
            "server": user.get('server'),
            "accountId": user.get('accountId')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения профиля пользователя: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения профиля: {str(e)}"
        )

# Пример роута для создания событий с аутентификацией
@protected_router.post("/events/create")
async def create_protected_event(
    event_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Создание события с проверкой аутентификации"""
    try:
        logger.info(f"📝 Создание события пользователем: {current_user['username']}")
        
        # Здесь можно добавить логику создания события
        # с привязкой к пользователю, который его создал
        
        return {
            "message": "Событие успешно создано",
            "created_by": current_user['username'],
            "user_id": current_user['user_id'],
            "event_data": event_data
        }
        
    except Exception as e:
        logger.error(f"Ошибка создания события: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка создания события: {str(e)}"
        )

# Пример роута для получения статистики (только для администраторов)
@protected_router.get("/admin/statistics")
async def get_admin_statistics(current_user: dict = Depends(require_admin)):
    """Получение статистики (только для администраторов)"""
    try:
        logger.info(f"📊 Запрос статистики от администратора: {current_user['sub']}")
        
        # Получаем репозитории
        promo_repo, informing_repo, user_repo = get_repositories()
        
        # Получаем статистику
        users = user_repo.get_all_users()
        promotions = promo_repo.get_all_promotions_with_informing()
        
        statistics = {
            "total_users": len(users) if users else 0,
            "total_promotions": len(promotions) if promotions else 0,
            "admin_username": current_user['sub'],
            "requested_at": "2024-01-01T00:00:00Z"  # В реальном приложении использовать datetime.now()
        }
        
        return statistics
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения статистики: {str(e)}"
        ) 