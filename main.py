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
from roaters.user_router import user_router
from roaters.auth_router import auth_router
from roaters.protected_routes import protected_router
from utils.email_service import email_service

# Настройки JWT
SECRET_KEY = "your-secret-key-here"  # В продакшене использовать безопасный ключ
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 часа

# Контекст для хеширования паролей

app = FastAPI(title="Promo Calendar API", version="1.0.0")

# Подключаем роутеры

app.include_router(promo_fields_router)
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(protected_router)

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
        "https://promo-gb.duckdns.org",
        "https://promo-gb.netlify.app"

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
    project: List[str]  # Список проектов
    promo_type: str
    promo_kind: str = ""
    start_date: str
    end_date: str
    name: str
    comment: Optional[str] = ""
    segments: str = "СНГ"
    info_channels: List[InfoChannelInput] = []  # Изменяем с dict на List[InfoChannelInput]
    link: Optional[str] = ""
    responsible_id: Optional[int] = None  # ID ответственного пользователя
    
    @validator('project')
    def validate_project_list(cls, v):
        if not v or len(v) == 0:
            raise ValueError('Список проектов не может быть пустым')
        # Проверяем, что каждый проект не пустая строка
        for project in v:
            if not project or not project.strip():
                raise ValueError('Название проекта не может быть пустым')
        return [project.strip() for project in v]

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
    responsible_id: Optional[int] = None  # ID ответственного пользователя
    responsible_name: Optional[str] = None  # Имя ответственного пользователя

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
    project: List[str] 
    promo_type: str
    promo_kind: str
    start_date: str
    end_date: str
    name: str
    comment: Optional[str] = ""
    segments: str
    link: Optional[str] = ""
    info_channels: List[InfoChannelInput] = []  # Список каналов информирования
    responsible_id: Optional[int] = None  # ID ответственного пользователя
    
    @validator('project')
    def validate_project_list(cls, v):
        if not v or len(v) == 0:
            raise ValueError('Список проектов не может быть пустым')
        # Проверяем, что каждый проект не пустая строка
        for project in v:
            if not project or not project.strip():
                raise ValueError('Название проекта не может быть пустым')
        return [project.strip() for project in v]

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

class DeleteEventRequest(BaseModel):
    is_recurring: bool = False


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

async def send_responsible_notification(
    responsible_id: int, 
    promo_name: str, 
    project: str, 
    promo_type: str, 
    start_date: str, 
    end_date: str, 
    notification_type: str = "assignment",
    assigned_by: str = "Система"
):
    """
    Отправить уведомление ответственному пользователю
    
    Args:
        responsible_id: ID ответственного пользователя
        promo_name: Название промо-акции
        project: Проект
        promo_type: Тип промо-акции
        start_date: Дата начала
        end_date: Дата окончания
        notification_type: Тип уведомления ("assignment" или "update")
        assigned_by: Кто назначил/обновил
    """
    try:
        # Получаем репозитории
        promo_repo, informing_repo, occurrence_repo, user_repo = get_repos()
        
        # Получаем данные пользователя
        user = user_repo.get_user_by_id(responsible_id)
        if not user:
            print(f"⚠️ Пользователь с ID {responsible_id} не найден")
            return
        
        user_email = user.get('mail')
        user_login = user.get('login', 'Пользователь')
        
        if not user_email:
            print(f"⚠️ У пользователя {user_login} не указан email")
            return
        
        # Отправляем уведомление в зависимости от типа
        if notification_type == "assignment":
            success = email_service.send_responsible_assignment_notification(
                to_email=user_email,
                responsible_name=user_login,
                promo_name=promo_name,
                project=project,
                promo_type=promo_type,
                start_date=start_date,
                end_date=end_date,
                assigned_by=assigned_by
            )
        elif notification_type == "update":
            success = email_service.send_responsible_update_notification(
                to_email=user_email,
                responsible_name=user_login,
                promo_name=promo_name,
                project=project,
                promo_type=promo_type,
                start_date=start_date,
                end_date=end_date,
                updated_by=assigned_by
            )
        else:
            print(f"⚠️ Неизвестный тип уведомления: {notification_type}")
            return
        
        if success:
            print(f"✅ Email уведомление отправлено на {user_email}")
        else:
            print(f"❌ Ошибка отправки email уведомления на {user_email}")
            
    except Exception as e:
        print(f"❌ Ошибка при отправке уведомления: {e}")

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
async def get_events(month: Optional[str] = None):
    """Получить события из базы данных за указанный месяц или все события"""
    try:
        # Получаем репозитории
        promo_repo, informing_repo, occurrence_repo, user_repo = get_repos()
        
        # Если месяц не указан, используем текущий месяц по умолчанию
        if not month:
            current_date = datetime.now()
            month = f"{current_date.year}-{current_date.month:02d}"
        
        # Валидация формата месяца
        try:
            year, month_num = month.split('-')
            year, month_num = int(year), int(month_num)
            if not (1 <= month_num <= 12):
                raise ValueError("Месяц должен быть от 1 до 12")
        except (ValueError, IndexError):
            raise HTTPException(
                status_code=400, 
                detail="Неверный формат месяца. Используйте формат YYYY-MM (например, 2025-09)"
            )
        
        # Получаем обычные промо-акции за указанный месяц
        promotions = promo_repo.get_promotions_by_month(month)
        
        # Получаем рекуррентные события за указанный месяц
        occurrences = occurrence_repo.get_occurrences_by_month(month)
        
        # Объединяем данные
        aggregated_data = []
        
        # Добавляем обычные промо-акции
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
                    'info_channels': promo.get('info_channels', []),  # Уже включены в результат JOIN
                    'responsible_id': promo.get('responsible_id'),
                    'responsible_name': promo.get('responsible_name'),
                    'is_recurring': False  # Флаг для отличия от рекуррентных событий
                }
                
                aggregated_data.append(event)
            except Exception as row_error:
                print(f"Ошибка при обработке промо-акции {promo.get('id')}: {str(row_error)}")
                continue
        
        # Добавляем рекуррентные события
        for occurrence in occurrences:
            try:
                event = {
                    'id': occurrence.get('id', ''),  # Уже содержит префикс "occ_"
                    'promo_id': occurrence.get('promo_id'),
                    'occurrence_id': occurrence.get('occurrence_id'),
                    'occurrence_key': occurrence.get('occurrence_key'),
                    'project': occurrence.get('project', ''),
                    'promo_type': occurrence.get('promo_type', ''),
                    'promo_kind': occurrence.get('promo_kind', ''),
                    'start_date': occurrence.get('start_date', ''),
                    'end_date': occurrence.get('end_date', ''),
                    'name': occurrence.get('name', ''),
                    'comment': occurrence.get('comment', ''),
                    'segments': occurrence.get('segment', ''),
                    'link': occurrence.get('link', ''),
                    'info_channels': occurrence.get('info_channels', []),
                    'responsible_id': occurrence.get('responsible_id'),
                    'responsible_name': occurrence.get('responsible_name'),
                    'is_recurring': True  # Флаг для отличия от обычных событий
                }
                
                aggregated_data.append(event)
            except Exception as row_error:
                print(f"Ошибка при обработке рекуррентного события {occurrence.get('occurrence_id')}: {str(row_error)}")
                continue
        
        # Сортируем по дате начала
        aggregated_data.sort(key=lambda x: x.get('start_date', ''))
        
        print(f"✅ Загружено {len(aggregated_data)} событий за {month} (обычных: {len(promotions)}, рекуррентных: {len(occurrences)})")
        return {"events": aggregated_data}
        
    except Exception as e:
        print(f"Критическая ошибка: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных: {str(e)}")

@app.post("/api/events")
async def create_event(event: PromoEventCreate):
    """Создать промо события для всех проектов из списка (оптимизированная версия с batch insert)"""
    try:
        # Получаем репозитории
        promo_repo, informing_repo, occurrence_repo, user_repo = get_repos()
        
        # Валидация обязательных полей
        if not event.project or not event.promo_type or not event.name:
            raise HTTPException(status_code=400, detail="Не все обязательные поля заполнены")
        
        # Подготавливаем данные для batch создания промо-акций
        promotions_data = []
        for project in event.project:
            promo_data = {
                'project': project,
                'promo_type': event.promo_type,
                'promo_kind': event.promo_kind,
                'start_date': event.start_date,
                'end_date': event.end_date,
                'name': event.name,  # В репозитории будет сохранено в поле title
                'comment': event.comment or '',
                'segments': event.segments or 'СНГ',  # В репозитории будет сохранено в поле segment
                'link': event.link or '',
                'responsible_id': event.responsible_id
            }
            promotions_data.append(promo_data)
        
        # Создаем все промо-акции одним batch запросом
        promotion_ids = promo_repo.create_promotions_batch(promotions_data)
        
        # Подготавливаем данные для batch создания информирований
        if event.info_channels:
            informings_data = []
            for i, project in enumerate(event.project):
                promotion_id = promotion_ids[i]
                
                for channel in event.info_channels:
                    if channel.start_date:  # Проверяем наличие даты
                        info_data = {
                            'type': channel.type,  # В репозитории будет сохранено в поле informing_type
                            'project': channel.project or project,  # Используем проект из цикла или из канала
                            'start_date': channel.start_date,
                            'name': channel.name,  # В репозитории будет сохранено в поле title
                            'comment': channel.comment or '',
                            'segments': channel.segments or 'СНГ',  # В репозитории будет сохранено в поле segment
                            'promo_id': promotion_id,
                            'link': channel.link or ''
                        }
                        informings_data.append(info_data)
            
            # Создаем все информирования одним batch запросом
            if informings_data:
                informing_repo.create_informings_batch(informings_data)
        
        # Отправляем уведомления ответственным (если назначены)
        if event.responsible_id:
            for i, project in enumerate(event.project):
                promotion_id = promotion_ids[i]
                # Отправляем уведомление асинхронно (не блокируем ответ)
                await send_responsible_notification(
                    responsible_id=event.responsible_id,
                    promo_name=event.name,
                    project=project,
                    promo_type=event.promo_type,
                    start_date=event.start_date,
                    end_date=event.end_date,
                    notification_type="assignment",
                    assigned_by="Система"
                )
        
        # Формируем ответ
        created_events = [
            {
                "project": project,
                "id": str(promotion_id)
            }
            for project, promotion_id in zip(event.project, promotion_ids)
        ]
        
        return {
            "message": f"Успешно создано {len(created_events)} событий (оптимизированным методом)",
            "created_events": created_events
        }
        
    except Exception as e:
        print(f"Ошибка при создании событий: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Ошибка создания событий: {str(e)}")



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
        promo_repo, informing_repo, occurrence_repo, user_repo = get_repos()
        
        promotion_id = int(event_id)
        
        # Проверяем существование промо-акции
        existing_promotion = promo_repo.get_promotion_by_id(promotion_id)
        if not existing_promotion:
            raise HTTPException(status_code=404, detail="Промо событие не найдено")
        
        # Обновляем данные промо-акции
        # Берем первый проект из списка (для совместимости с фронтендом)
        project = event.project[0] if event.project else existing_promotion.get('project', '')
        
        promo_data = {
            'project': project,
            'promo_type': event.promo_type,
            'promo_kind': event.promo_kind,
            'start_date': event.start_date,
            'end_date': event.end_date,
            'name': event.name,  # В репозитории будет сохранено в поле title
            'comment': event.comment,
            'segments': event.segments,  # В репозитории будет сохранено в поле segment
            'link': event.link,
            'responsible_id': event.responsible_id
        }
        
        # Проверяем, изменился ли ответственный
        old_responsible_id = existing_promotion.get('responsible_id')
        new_responsible_id = event.responsible_id
        
        # Обновляем промо-акцию
        promo_repo.update_promotion(promotion_id, promo_data)
        
        # Отправляем уведомление, если ответственный изменился или был назначен
        if new_responsible_id and new_responsible_id != old_responsible_id:
            await send_responsible_notification(
                responsible_id=new_responsible_id,
                promo_name=event.name,
                project=project,
                promo_type=event.promo_type,
                start_date=event.start_date,
                end_date=event.end_date,
                notification_type="assignment" if old_responsible_id is None else "update",
                assigned_by="Система"
            )
        
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
                    'project': project,  # Используем проект из списка
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
                    'project': project,  # Используем проект из списка
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
        promo_repo, informing_repo, occurrence_repo, user_repo = get_repos()
        
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
async def delete_event(event_id: str, delete_request: DeleteEventRequest):
    """Удалить промо событие и все связанные с ним каналы информирования"""
    try:
        print(f"🗑️ Запрос на удаление события ID: {event_id}, is_recurring: {delete_request.is_recurring}")
        
        # Получаем репозитории
        promo_repo, informing_repo, occurrence_repo, user_repo = get_repos()
        
        event_id_int = int(event_id)
    
        if delete_request.is_recurring:
            # Удаляем рекуррентное событие из promotion_occurrences
            print(f"🔍 Попытка удаления рекуррентного события с ID: {event_id_int}")
            
            # Проверяем существование вхождения по его ID
            target_occurrence = occurrence_repo.get_occurrence_by_id(event_id_int)
            
            if not target_occurrence:
                print(f"❌ Рекуррентное событие с ID {event_id_int} не найдено в базе данных")
                raise HTTPException(status_code=404, detail="Рекуррентное событие не найдено")
            
            print(f"✅ Найдено рекуррентное событие: {target_occurrence}")
            
            # Удаляем вхождение
            success = occurrence_repo.delete_occurrence(event_id_int)
            
            if not success:
                raise HTTPException(status_code=404, detail="Рекуррентное событие не найдено")
            
            return {
                "message": "Рекуррентное событие успешно удалено"
            }
        else:
            # Удаляем обычное событие из promotions (текущая логика)
            print(f"🔍 Попытка удаления обычного события с ID: {event_id_int}")
            
            # Проверяем существование промо-акции
            existing_promotion = promo_repo.get_promotion_by_id(event_id_int)
            if not existing_promotion:
                print(f"❌ Обычное событие с ID {event_id_int} не найдено в таблице promotions")
                raise HTTPException(status_code=404, detail="Промо событие не найдено")
            
            print(f"✅ Найдено обычное событие: {existing_promotion}")
            
            # Получаем количество связанных информирований для отчета
            existing_channels = informing_repo.get_informing_by_promo_id(event_id_int)
            channels_count = len(existing_channels)
            
            # Удаляем промо-акцию (информирования удалятся автоматически благодаря каскадному удалению в репозитории)
            success = promo_repo.delete_promotion(event_id_int)
            
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
        promo_repo, informing_repo, occurrence_repo, user_repo = get_repos()
        
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
        promo_repo, informing_repo, occurrence_repo, user_repo = get_repos()
        
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



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 