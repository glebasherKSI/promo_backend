from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Literal
import os
import uuid
from datetime import datetime, date, timedelta
import calendar
from pydantic import BaseModel, validator
import pandas as pd
from roaters.promo_fields import router as promo_fields_router
from database import get_repositories


# Настройки JWT
SECRET_KEY = "your-secret-key-here"  # В продакшене использовать безопасный ключ
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 часа

# Контекст для хеширования паролей

app = FastAPI(title="Promo Calendar API", version="1.0.0")

# Подключаем роутеры
app.include_router(promo_fields_router)

# CORS middleware для работы сReact
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",
        "http://localhost:3000",     # React dev server
        "http://localhost:5173",     # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://192.168.168.14:3000",
        "http://192.168.168.14:5173",
        "https://delicate-cat-e905cc.netlify.app",
        "https://promo-gb.duckdns.org"

    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Pydantic модели

def validate_id_field(v):
    """Валидатор для ID полей - принимает числа и UUID"""
    if v:
        # Проверяем если это число (автоинкрементный ID из БД)
        if str(v).isdigit():
            return str(v)
        
        # Проверяем если это UUID (старый формат)
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('ID должен быть числом или валидным UUID')
    return v

class InfoChannelInput(BaseModel):
    id: Optional[str] = None  # None для новых каналов
    type: str
    start_date: str
    name: str
    comment: Optional[str] = ""
    segments: str = "СНГ"
    link: Optional[str] = ""
    project: Optional[str] = None  # Делаем опциональным
    
    @validator('id')
    def validate_id(cls, v):
        return validate_id_field(v)

class PromoEventCreate(BaseModel):
    project: str
    promo_type: str
    promo_kind: str = ""
    start_date: str
    end_date: str
    name: str
    comment: Optional[str] = ""
    segments: str = "СНГ"
    info_channels: List[InfoChannelInput] = []  # Изменяем с dict на List[InfoChannelInput]
    link: Optional[str] = ""

class PromoEvent(BaseModel):
    id: str
    project: str
    promo_type: str
    promo_kind: str
    start_date: str
    end_date: str
    name: str
    comment: str
    segments: str
    info_channels: List[dict] = []
    link: str = ""

class InfoEvent(BaseModel):
    id: str
    info_type: str
    project: str
    start_date: str
    name: str
    comment: str
    segments: str
    promo_id: str
    link: str = ""

class CalendarData(BaseModel):
    year: int
    month: int
    events: List[dict]

class PromoEventUpdate(BaseModel):
    project: str
    promo_type: str
    promo_kind: str
    start_date: str
    end_date: str
    name: str
    comment: Optional[str] = ""
    segments: str
    link: Optional[str] = ""
    info_channels: List[InfoChannelInput] = []  # Список каналов информирования

class InfoChannelUpdate(BaseModel):
    type: str
    project: str
    start_date: str
    name: str
    comment: str
    segments: str
    promo_id: str
    link: Optional[str] = ""

class InfoChannelCreate(BaseModel):
    type: Literal["E-mail", "MSGR", "BPS", "PUSH", "SMM", "Баннер", "Страница", "Новости"]
    project: str
    start_date: str
    name: str
    comment: Optional[str] = ""
    segments: str = "СНГ"
    link: Optional[str] = ""
    promo_id: Optional[str] = None
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Название не может быть пустым')
        return v.strip()
    
    @validator('start_date')
    def validate_start_date(cls, v):
        if not v:
            return v
        try:
            # Поддержка разных форматов дат для совместимости с фронтендом
            if 'T' in v:
                # ISO формат с T
                datetime.fromisoformat(v.replace('Z', '+00:00'))
            elif ' ' in v:
                # Формат с пробелом
                datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
            else:
                # Простой формат даты
                datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Дата должна быть в формате ISO datetime, YYYY-MM-DD HH:MM:SS или YYYY-MM-DD')
    
    @validator('promo_id')
    def validate_promo_id(cls, v):
        return validate_id_field(v)
    
    @validator('comment', 'link', pre=True)
    def empty_str_to_none(cls, v):
        return v if v is not None else ""

# Модели для аутентификации
class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    username: str
    role: str
    token: str

# Удалено - используем базу данных вместо Google Sheets



def get_repos():
    """Хелпер для получения репозиториев с обработкой ошибок"""
    try:
        return get_repositories()
    except Exception as e:
        # В случае недоступности БД, выводим детальную ошибку
        print(f"❌ База данных недоступна: {e}")
        print("💡 Проверьте:")
        print("   1. Запущен ли MySQL сервер")
        print("   2. Правильные ли настройки в .env файле:")
        print("      MYSQL_HOST=91.209.226.31")
        print("      MYSQL_USER=promo_user") 
        print("      MYSQL_PASSWORD=789159987Cs")
        print("      MYSQL_DATABASE=promo_db")
        print("      MYSQL_PORT=3306")
        print("   3. Доступен ли сервер по сети")
        raise HTTPException(
            status_code=503, 
            detail="База данных временно недоступна. Проверьте подключение к MySQL серверу."
        )

@app.get("/")
async def root():
    return {"message": "Promo Calendar API"}

def convert_date_to_iso(date_str: str) -> str:
    """Конвертирует дату из различных форматов в ISO формат"""
    if not date_str:
        return ""
    try:
        # Убираем возможное время и пробелы
        date_str = date_str.strip()
        
        # Пробуем разные форматы дат
        if 'T' in date_str:
            # Уже в ISO формате
            parsed_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        elif ' ' in date_str:
            # Формат DD.MM.YYYY HH:MM:SS или YYYY-MM-DD HH:MM:SS
            if '.' in date_str.split()[0]:
                parsed_date = datetime.strptime(date_str.split()[0], "%d.%m.%Y")
            else:
                parsed_date = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
        elif '.' in date_str:
            # Формат DD.MM.YYYY
            parsed_date = datetime.strptime(date_str, "%d.%m.%Y")
        else:
            # Формат YYYY-MM-DD
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
        
        # Возвращаем в ISO формате
        return parsed_date.isoformat() + "Z"
    except Exception as e:
        print(f"Ошибка конвертации даты '{date_str}': {str(e)}")
        return date_str

@app.get("/api/events")
async def get_events():
    """Получить все события из базы данных (оптимизированная версия)"""
    try:
        # Получаем репозитории
        promo_repo, informing_repo, user_repo = get_repos()
        
        # Получаем все промо-акции с информированиями одним запросом (вместо N+1)
        promotions = promo_repo.get_all_promotions_with_informing()
        
        if not promotions:
            return {"events": []}
        
        # Преобразуем данные в формат, ожидаемый фронтендом
        aggregated_data = []
        for promo in promotions:
            try:
                event = {
                    'id': str(promo['id']),  # Конвертируем в строку для совместимости
                    'project': promo.get('project', ''),
                    'promo_type': promo.get('promo_type', ''),
                    'promo_kind': promo.get('promo_kind', ''),
                    'start_date': promo.get('start_date', ''),
                    'end_date': promo.get('end_date', ''),
                    'name': promo.get('title', ''),  # В БД это title
                    'comment': promo.get('comment', ''),
                    'segments': promo.get('segment', ''),  # В БД это segment
                    'link': promo.get('link', ''),
                    'info_channels': promo.get('info_channels', [])  # Уже включены в результат JOIN
                }
                
                aggregated_data.append(event)
            except Exception as row_error:
                print(f"Ошибка при обработке промо-акции {promo.get('id')}: {str(row_error)}")
                continue
        
        print(f"✅ Загружено {len(aggregated_data)} событий оптимизированным методом")
        return {"events": aggregated_data}
        
    except Exception as e:
        print(f"Критическая ошибка: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных: {str(e)}")

@app.post("/api/events")
async def create_event(event: PromoEventCreate):
    """Создать новое промо событие"""
    try:
        # Получаем репозитории
        promo_repo, informing_repo, user_repo = get_repos()
        
        # Валидация обязательных полей
        if not event.project or not event.promo_type or not event.name:
            raise HTTPException(status_code=400, detail="Не все обязательные поля заполнены")
        
        # Формируем данные для создания промо-акции
        promo_data = {
            'project': event.project,
            'promo_type': event.promo_type,
            'promo_kind': event.promo_kind,
            'start_date': event.start_date,
            'end_date': event.end_date,
            'name': event.name,  # В репозитории будет сохранено в поле title
            'comment': event.comment or '',
            'segments': event.segments or 'СНГ',  # В репозитории будет сохранено в поле segment
            'link': event.link or '',
            'responsible_id': None  # Можно добавить логику определения ответственного
        }
        
        # Создаем промо-акцию
        promotion_id = promo_repo.create_promotion(promo_data)
        
        # Обрабатываем информирования
        if event.info_channels:
            for channel in event.info_channels:
                if channel.start_date:  # Проверяем наличие даты
                    info_data = {
                        'type': channel.type,  # В репозитории будет сохранено в поле informing_type
                        'project': channel.project or event.project,
                        'start_date': channel.start_date,
                        'name': channel.name,  # В репозитории будет сохранено в поле title
                        'comment': channel.comment or '',
                        'segments': channel.segments or 'СНГ',  # В репозитории будет сохранено в поле segment
                        'promo_id': promotion_id,
                        'link': channel.link or ''
                    }
                    
                    # Создаем информирование
                    informing_repo.create_informing(info_data)
        
        return {"message": "Событие успешно создано", "id": str(promotion_id)}
        
    except Exception as e:
        print(f"Ошибка при создании события: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Ошибка создания события: {str(e)}")

@app.get("/api/calendar/{year}/{month}")
async def get_calendar_data(year: int, month: int):
    """Получить данные календаря для конкретного месяца"""
    try:
        # Получаем все события
        events_response = await get_events()
        events = events_response["events"]
        
        # Фильтруем события по месяцу
        _, num_days = calendar.monthrange(year, month)
        
        # Группируем события по проектам и типам
        projects = set()
        events_by_project_type = {}
        
        for event in events:
            project = event.get('project')
            if not project:
                continue
            projects.add(project)
            
            # Основное событие
            promo_type = event.get('promo_type')
            if promo_type and event_intersects_month(event, year, month):
                key = (project, promo_type)
                if key not in events_by_project_type:
                    events_by_project_type[key] = []
                events_by_project_type[key].append(event)
            
            # Информирования
            for info in event.get('info_channels', []):
                info_type = info.get('type')
                info_project = info.get('project', project)
                if info_type and info_intersects_month(info, year, month):
                    projects.add(info_project)
                    key = (info_project, info_type)
                    if key not in events_by_project_type:
                        events_by_project_type[key] = []
                    events_by_project_type[key].append(info)
        
        return {
            "year": year,
            "month": month,
            "num_days": num_days,
            "projects": sorted(list(projects)),
            "events_by_project_type": events_by_project_type
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения календаря: {str(e)}")

def event_intersects_month(event, year, month):
    """Проверяет, пересекает ли событие указанный месяц"""
    start_str = event.get('start_date')
    end_str = event.get('end_date') or start_str
    
    if not start_str:
        return False
    
    try:
        # Для обратной совместимости проверяем оба формата
        try:
            start = datetime.strptime(start_str.split()[0], "%d.%m.%Y").date()
        except ValueError:
            start = datetime.strptime(start_str.split('T')[0], "%Y-%m-%d").date()
            
        if end_str:
            try:
                end = datetime.strptime(end_str.split()[0], "%d.%m.%Y").date()
            except ValueError:
                end = datetime.strptime(end_str.split('T')[0], "%Y-%m-%d").date()
        else:
            end = start
    except Exception:
        return False
    
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    
    return not (end < first_day or start > last_day)

def info_intersects_month(info, year, month):
    """Проверяет, пересекает ли информирование указанный месяц"""
    start_str = info.get('start_date')
    
    if not start_str:
        return False
    
    try:
        # Для обратной совместимости проверяем оба формата
        try:
            start = datetime.strptime(start_str.split()[0], "%d.%m.%Y").date()
        except ValueError:
            start = datetime.strptime(start_str.split('T')[0], "%Y-%m-%d").date()
    except Exception:
        return False
    
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    
    return first_day <= start <= last_day

@app.put("/api/events/{event_id}")
async def update_event(event_id: str, event: PromoEventUpdate):
    """Обновить промо событие и его каналы информирования"""
    try:
        # Получаем репозитории
        promo_repo, informing_repo, user_repo = get_repos()
        
        promotion_id = int(event_id)
        
        # Проверяем существование промо-акции
        existing_promotion = promo_repo.get_promotion_by_id(promotion_id)
        if not existing_promotion:
            raise HTTPException(status_code=404, detail="Промо событие не найдено")
        
        # Обновляем данные промо-акции
        promo_data = {
            'project': event.project,
            'promo_type': event.promo_type,
            'promo_kind': event.promo_kind,
            'start_date': event.start_date,
            'end_date': event.end_date,
            'name': event.name,  # В репозитории будет сохранено в поле title
            'comment': event.comment,
            'segments': event.segments,  # В репозитории будет сохранено в поле segment
            'link': event.link,
            'responsible_id': existing_promotion.get('responsible_id')  # Сохраняем существующего ответственного
        }
        
        # Обновляем промо-акцию
        promo_repo.update_promotion(promotion_id, promo_data)
        
        # Обработка каналов информирования
        
        # 1. Получаем существующие каналы для этого промо
        existing_channels = informing_repo.get_informing_by_promo_id(promotion_id)
        existing_channel_ids = {str(ch['id']): ch['id'] for ch in existing_channels}
        
        # 2. Обрабатываем каждый канал из запроса
        processed_channel_ids = set()
        
        for channel in event.info_channels:
            if channel.id and str(channel.id) in existing_channel_ids:
                # Обновляем существующий канал
                channel_data = {
                    'type': channel.type,
                    'project': event.project,
                    'start_date': channel.start_date,
                    'name': channel.name,
                    'comment': channel.comment,
                    'segments': channel.segments,
                    'promo_id': promotion_id,
                    'link': channel.link
                }
                
                informing_repo.update_informing(existing_channel_ids[str(channel.id)], channel_data)
                processed_channel_ids.add(str(channel.id))
            else:
                # Добавляем новый канал
                channel_data = {
                    'type': channel.type,
                    'project': event.project,
                    'start_date': channel.start_date,
                    'name': channel.name,
                    'comment': channel.comment,
                    'segments': channel.segments,
                    'promo_id': promotion_id,
                    'link': channel.link
                }
                
                informing_repo.create_informing(channel_data)
        
        # 3. Удаляем каналы, которые не были обновлены (были удалены на фронтенде)
        for channel_id_str, channel_id in existing_channel_ids.items():
            if channel_id_str not in processed_channel_ids:
                informing_repo.delete_informing(channel_id)
        
        return {
            "message": "Промо событие и каналы информирования успешно обновлены",
            "id": event_id
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат ID события")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка обновления промо события: {str(e)}"
        )

@app.put("/api/channels/{channel_id}")
async def update_channel(channel_id: str, channel: InfoChannelUpdate):
    """Обновить канал информирования"""
    try:
        # Получаем репозитории
        promo_repo, informing_repo, user_repo = get_repos()
        
        informing_id = int(channel_id)
        promo_id = int(channel.promo_id) if channel.promo_id else None
        
        # Формируем данные для обновления
        channel_data = {
            'type': channel.type,
            'project': channel.project,
            'start_date': channel.start_date,
            'name': channel.name,
            'comment': channel.comment,
            'segments': channel.segments,
            'promo_id': promo_id,
            'link': channel.link
        }
        
        # Обновляем канал информирования
        success = informing_repo.update_informing(informing_id, channel_data)
        
        if not success:
            raise HTTPException(status_code=404, detail="Канал информирования не найден")
        
        return {"message": "Канал информирования успешно обновлен"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат ID канала")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Ошибка обновления канала информирования: {str(e)}")

@app.delete("/api/events/{event_id}")
async def delete_event(event_id: str):
    """Удалить промо событие и все связанные с ним каналы информирования"""
    try:
        # Получаем репозитории
        promo_repo, informing_repo, user_repo = get_repos()
        
        promotion_id = int(event_id)
        
        # Проверяем существование промо-акции
        existing_promotion = promo_repo.get_promotion_by_id(promotion_id)
        if not existing_promotion:
            raise HTTPException(status_code=404, detail="Промо событие не найдено")
        
        # Получаем количество связанных информирований для отчета
        existing_channels = informing_repo.get_informing_by_promo_id(promotion_id)
        channels_count = len(existing_channels)
        
        # Удаляем промо-акцию (информирования удалятся автоматически благодаря каскадному удалению в репозитории)
        success = promo_repo.delete_promotion(promotion_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Промо событие не найдено")
        
        return {
            "message": "Промо событие и связанные каналы информирования успешно удалены",
            "deleted_channels_count": channels_count
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат ID события")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Ошибка удаления промо события: {str(e)}")

@app.delete("/api/channels/{channel_id}")
async def delete_channel(channel_id: str):
    """Удалить канал информирования"""
    try:
        # Получаем репозитории
        promo_repo, informing_repo, user_repo = get_repos()
        
        informing_id = int(channel_id)
        
        # Удаляем канал информирования
        success = informing_repo.delete_informing(informing_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Канал информирования не найден")
        
        return {"message": "Канал информирования успешно удален"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат ID канала")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Ошибка удаления канала информирования: {str(e)}")

@app.post("/api/channels", status_code=status.HTTP_201_CREATED)
async def create_channel(channel: InfoChannelCreate):
    """Создать новый канал информирования"""
    try:
        # Получаем репозитории
        promo_repo, informing_repo, user_repo = get_repos()
        
        # Валидация обязательных полей
        if not channel.type or not channel.project or not channel.name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не все обязательные поля заполнены"
            )
        
        # Формируем данные канала
        channel_data = {
            'type': channel.type,
            'project': channel.project,
            'start_date': channel.start_date,
            'name': channel.name,
            'comment': channel.comment or '',
            'segments': channel.segments or 'СНГ',
            'promo_id': int(channel.promo_id) if channel.promo_id else None,
            'link': channel.link or ''
        }
        
        # Создаем канал информирования
        informing_id = informing_repo.create_informing(channel_data)
        
        return {
            "message": "Канал информирования успешно создан",
            "id": str(informing_id),
            "channel": {
                "id": str(informing_id),
                "type": channel.type,
                "project": channel.project,
                "start_date": channel.start_date,
                "name": channel.name,
                "comment": channel.comment or '',
                "segments": channel.segments or 'СНГ',
                "link": channel.link or '',
                "promo_id": channel.promo_id
            }
        }
        
    except Exception as e:
        print(f"Ошибка при создании канала: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка создания канала информирования: {str(e)}"
        )

@app.post("/api/auth/login")
async def login(user_data: UserLogin):
    """Аутентификация пользователя"""
    try:
        # Получаем репозитории
        promo_repo, informing_repo, user_repo = get_repos()
        
        # Поиск пользователя в базе данных
        user = user_repo.get_user_by_credentials(user_data.username, user_data.password)
        
        if user:
            return {
                "user": {
                    "username": user.get('login'),
                    "role": user.get('role', 'user')
                }
            }
        
        raise HTTPException(
            status_code=401,
            detail="Неверное имя пользователя или пароль"
        )
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при попытке входа: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 