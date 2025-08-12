from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from database import get_repositories
import logging

logger = logging.getLogger(__name__)

# Создаем роутер
user_router = APIRouter(prefix="/api/users", tags=["users"])

# Pydantic модели
class UserResponse(BaseModel):
    """Модель ответа с данными пользователя"""
    id: int
    login: str
    token: Optional[str] = None
    mail: Optional[str] = None
    server: Optional[str] = None
    accountId: Optional[str] = None
    api_key: Optional[str] = None
    token_trello: Optional[str] = None

class UserBriefResponse(BaseModel):
    """Модель ответа с краткими данными пользователя"""
    id: int
    login: str
    mail: Optional[str] = None

class UserUpdate(BaseModel):
    """Модель для обновления пользователя"""
    login: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None
    mail: Optional[str] = None
    server: Optional[str] = None
    accountId: Optional[str] = None
    api_key: Optional[str] = None
    token_trello: Optional[str] = None

@user_router.get("/{login}", response_model=UserResponse)
async def get_user_by_login(login: str):
    """Получить данные пользователя по логину"""
    try:
        logger.info(f"🔍 Запрос пользователя по логину: '{login}'")
        promo_repo, informing_repo, occurrence_repo, user_repo = get_repositories()
        
        # Получаем пользователя по логину
        user = user_repo.get_user_by_login(login)
        logger.info(f"📋 Результат поиска: {user}")
        
        if not user:
            logger.warning(f"❌ Пользователь с логином '{login}' не найден в базе данных")
            raise HTTPException(status_code=404, detail=f"Пользователь с логином '{login}' не найден")
        
        # Возвращаем данные пользователя
        return UserResponse(
            id=user.get('id'),
            login=user.get('login', ''),
            token=user.get('token'),
            mail=user.get('mail'),
            server=user.get('server'),
            accountId=user.get('accountId'),
            api_key=user.get('api_key'),
            token_trello=user.get('token_trello')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения пользователя {login}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных пользователя: {str(e)}")

@user_router.get("/", response_model=List[UserResponse])
async def get_all_users():
    """Получить список всех пользователей (для диагностики)"""
    try:
        promo_repo, informing_repo, occurrence_repo, user_repo = get_repositories()
        
        # Получаем всех пользователей
        users = user_repo.get_all_users()
        
        result = []
        for user in users:
            result.append(UserResponse(
                id=user.get('id'),
                login=user.get('login', ''),
                password=user.get('password', ''),
                token=user.get('token'),
                mail=user.get('mail'),
                server=user.get('server'),
                accountId=user.get('accountId'),
                api_key=user.get('api_key'),
                token_trello=user.get('token_trello')
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Ошибка получения списка пользователей: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения списка пользователей: {str(e)}")

@user_router.get("/list/brief", response_model=List[UserBriefResponse])
async def get_users_brief():
    """Получить краткий список всех пользователей (id, login, mail)"""
    try:
        logger.info("🔍 Запрос краткого списка пользователей")
        promo_repo, informing_repo, occurrence_repo, user_repo = get_repositories()
        
        # Получаем всех пользователей
        users = user_repo.get_all_users()
        
        result = []
        for user in users:
            result.append(UserBriefResponse(
                id=user.get('id'),
                login=user.get('login', ''),
                mail=user.get('mail')
            ))
        
        logger.info(f"✅ Возвращено {len(result)} пользователей")
        return result
        
    except Exception as e:
        logger.error(f"Ошибка получения краткого списка пользователей: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения списка пользователей: {str(e)}")

@user_router.put("/{user_id}")
async def update_user(user_id: int, user_data: UserUpdate):
    """Обновить данные пользователя по ID"""
    try:
        promo_repo, informing_repo, occurrence_repo, user_repo = get_repositories()
        
        # Проверяем существование пользователя
        existing_user = user_repo.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail=f"Пользователь с ID {user_id} не найден")
        
        # Обновляем пользователя
        success = user_repo.update_user(user_id, user_data.dict(exclude_unset=True))
        
        if not success:
            raise HTTPException(status_code=500, detail="Не удалось обновить пользователя")
        
        return {"message": f"Пользователь {user_id} успешно обновлен"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка обновления пользователя {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка обновления пользователя: {str(e)}") 