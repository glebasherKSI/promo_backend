from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Literal
import gspread
import os
import uuid
from datetime import datetime, date, timedelta
import calendar
from pydantic import BaseModel, validator
import pandas as pd


# Настройки JWT
SECRET_KEY = "your-secret-key-here"  # В продакшене использовать безопасный ключ
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 часа

# Контекст для хеширования паролей

app = FastAPI(title="Promo Calendar API", version="1.0.0")

# CORS middleware для работы с React
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
        "https://delicate-cat-e905cc.netlify.app"  
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Pydantic модели
class InfoChannelInput(BaseModel):
    id: Optional[str] = None  # None для новых каналов
    type: str
    start_date: str
    name: str
    comment: Optional[str] = ""
    segments: str = "СНГ"
    link: Optional[str] = ""
    project: Optional[str] = None  # Делаем опциональным

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
        if v:
            try:
                uuid.UUID(v)
            except ValueError:
                raise ValueError('promo_id должен быть валидным UUID')
        return v
    
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

# Google Sheets клиент
def get_google_sheets_client():
    """Получить клиент Google Sheets"""
    try:
        if not os.path.exists('../data/data.json'):
            raise HTTPException(status_code=500, detail="Файл аутентификации не найден")
        
        gc = gspread.service_account(filename='../data/data.json')
        spreadsheet = gc.open_by_key('1LrJyEzeyM5ULgR1QjWXcHW_jM2RsYPxOo2RqjQB8URw')
        return spreadsheet
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка подключения к Google Sheets: {str(e)}")



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
    """Получить все события из Google Sheets"""
    try:
        spreadsheet = get_google_sheets_client()
        
        try:
            # Проверяем наличие листов
            promo_sheet = spreadsheet.worksheet('ПРОМО')
            info_sheet = spreadsheet.worksheet('ИНФОРМИРОВАНИЕ')
            
            # Получаем данные промо
            promo_data = promo_sheet.get_all_records()
            if not promo_data:
                return {"events": []}
            
            # Получаем данные информирования
            try:
                info_data = info_sheet.get_all_records()
            except:
                info_data = []
            
            # Группируем информирования по промо ID
            info_by_promo = {}
            for info_row in info_data:
                promo_id = info_row.get('Идентификатор промо')
                if promo_id:
                    if promo_id not in info_by_promo:
                        info_by_promo[promo_id] = []
                    
                    info_by_promo[promo_id].append({
                        'id': info_row.get('id', ''),
                        'type': info_row.get('Информирование', ''),
                        'project': info_row.get('Проект', ''),
                        'start_date': convert_date_to_iso(info_row.get('Дата старта', '')),
                        'name': info_row.get('Название', ''),
                        'comment': info_row.get('Комментарий', ''),
                        'segments': info_row.get('Сегмент', ''),
                        'promo_id': promo_id,
                        'link': info_row.get('Ссылка', '')
                    })
            
            # Формируем агрегированные данные
            aggregated_data = []
            for promo_row in promo_data:
                try:
                    promo_id = promo_row.get('id')
                    if not promo_id:  # Пропускаем строки без id
                        continue
                        
                    event = {
                        'id': promo_id,
                        'project': promo_row.get('Проект', ''),
                        'promo_type': promo_row.get('Тип промо', ''),
                        'promo_kind': promo_row.get('Вид промо', ''),
                        'start_date': convert_date_to_iso(promo_row.get('Дата старта', '')),
                        'end_date': convert_date_to_iso(promo_row.get('Дата конца', '')),
                        'name': promo_row.get('Название', ''),
                        'comment': promo_row.get('Комментарий', ''),
                        'segments': promo_row.get('Сегмент', ''),
                        'link': promo_row.get('Ссылка', ''),
                        'info_channels': info_by_promo.get(promo_id, [])
                    }
                    
                    aggregated_data.append(event)
                except Exception as row_error:
                    print(f"Ошибка при обработке строки промо: {str(row_error)}")
                    continue
            
            return {"events": aggregated_data}
            
        except Exception as sheet_error:
            print(f"Ошибка при работе с таблицей: {str(sheet_error)}")
            return {"events": []}
            
    except Exception as e:
        print(f"Критическая ошибка: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных: {str(e)}")

@app.post("/api/events")
async def create_event(event: PromoEventCreate):
    """Создать новое промо событие"""
    try:
        spreadsheet = get_google_sheets_client()
        promo_sheet = spreadsheet.worksheet('ПРОМО')
        info_sheet = spreadsheet.worksheet('ИНФОРМИРОВАНИЕ')
        
        # Создаем уникальный ID для промо
        unique_id = str(uuid.uuid4())
        
        # Валидация обязательных полей
        if not event.project or not event.promo_type  or not event.name:
            raise HTTPException(status_code=400, detail="Не все обязательные поля заполнены")
        
        # Формируем данные промо
        promo_data = {
            'id': unique_id,
            'Проект': event.project,
            'Тип промо': event.promo_type,
            'Вид промо': event.promo_kind,
            'Дата старта': event.start_date,
            'Дата конца': event.end_date,
            'Название': event.name,
            'Комментарий': event.comment or '',
            'Сегмент': event.segments or 'СНГ',
            'Ссылка': event.link or ''
        }
        
        # Получаем заголовки из первой строки
        headers = promo_sheet.row_values(1)
        if not headers:
            raise HTTPException(status_code=500, detail="Отсутствуют заголовки в таблице ПРОМО")
            
        # Формируем список значений в том же порядке, что и заголовки
        promo_row = [promo_data.get(header, '') for header in headers]
        
        # Добавляем новое промо
        promo_sheet.append_row(promo_row)
        
        # Обрабатываем информирования
        if event.info_channels:
            # Получаем заголовки из таблицы информирования
            info_headers = info_sheet.row_values(1)
            if not info_headers:
                raise HTTPException(status_code=500, detail="Отсутствуют заголовки в таблице ИНФОРМИРОВАНИЕ")
            
            for channel in event.info_channels:
                if channel.start_date:  # Проверяем наличие даты
                    unique_id_info = str(uuid.uuid4())
                    info_data = {
                        'id': unique_id_info,
                        'Информирование': channel.type,
                        'Проект': channel.project or event.project,
                        'Дата старта': channel.start_date,
                        'Название': channel.name,
                        'Комментарий': channel.comment or '',
                        'Сегмент': channel.segments or 'СНГ',
                        'Идентификатор промо': unique_id,
                        'Ссылка': channel.link or ''
                    }
                    
                    # Формируем список значений для информирования
                    info_row = [info_data.get(header, '') for header in info_headers]
                    
                    # Добавляем новое информирование
                    info_sheet.append_row(info_row)
        
        return {"message": "Событие успешно создано", "id": unique_id}
        
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
        spreadsheet = get_google_sheets_client()
        promo_sheet = spreadsheet.worksheet('ПРОМО')
        info_sheet = spreadsheet.worksheet('ИНФОРМИРОВАНИЕ')
        
        # Получаем все записи
        promo_records = promo_sheet.get_all_records()
        info_records = info_sheet.get_all_records()
        
        # Ищем индекс записи для обновления промо
        promo_row_idx = None
        for idx, record in enumerate(promo_records, start=2):  # start=2 так как первая строка - заголовки
            if record.get('id') == event_id:
                promo_row_idx = idx
                break
        
        if not promo_row_idx:
            raise HTTPException(status_code=404, detail="Промо событие не найдено")
        
        # Обновляем данные промо
        update_data = {
            'id': event_id,
            'Проект': event.project,
            'Тип промо': event.promo_type,
            'Вид промо': event.promo_kind,
            'Дата старта': event.start_date,
            'Дата конца': event.end_date,
            'Название': event.name,
            'Комментарий': event.comment,
            'Сегмент': event.segments,
            'Ссылка': event.link
        }
        
        # Получаем заголовки промо
        promo_headers = promo_sheet.row_values(1)
        
        # Формируем список значений в том же порядке, что и заголовки
        promo_values = [update_data.get(header, '') for header in promo_headers]
        
        # Обновляем строку промо
        promo_sheet.update(f'A{promo_row_idx}:J{promo_row_idx}', [promo_values])
        
        # Обработка каналов информирования
        
        # 1. Получаем существующие каналы для этого промо
        existing_channels = {}
        channels_to_delete = []
        for idx, record in enumerate(info_records, start=2):
            if record.get('Идентификатор промо') == event_id:
                channel_id = record.get('id')
                existing_channels[channel_id] = idx
        
        # 2. Обрабатываем каждый канал из запроса
        info_headers = info_sheet.row_values(1)
        for channel in event.info_channels:
            channel_data = {
                'id': channel.id or str(uuid.uuid4()),
                'Информирование': channel.type,
                'Проект': event.project,
                'Дата старта': channel.start_date,
                'Название': channel.name,
                'Комментарий': channel.comment,
                'Сегмент': channel.segments,
                'Идентификатор промо': event_id,
                'Ссылка': channel.link
            }
            
            channel_values = [channel_data.get(header, '') for header in info_headers]
            
            if channel.id and channel.id in existing_channels:
                # Обновляем существующий канал
                row_idx = existing_channels[channel.id]
                info_sheet.update(f'A{row_idx}:I{row_idx}', [channel_values])
                del existing_channels[channel.id]
            else:
                # Добавляем новый канал
                info_sheet.append_row(channel_values)
        
        # 3. Удаляем каналы, которые не были обновлены (были удалены на фронтенде)
        for channel_id, row_idx in sorted(existing_channels.items(), key=lambda x: x[1], reverse=True):
            info_sheet.delete_rows(row_idx)
        
        return {
            "message": "Промо событие и каналы информирования успешно обновлены",
            "id": event_id
        }
        
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
        spreadsheet = get_google_sheets_client()
        info_sheet = spreadsheet.worksheet('ИНФОРМИРОВАНИЕ')
        
        # Получаем все записи
        records = info_sheet.get_all_records()
        
        # Ищем индекс записи для обновления
        row_idx = None
        for idx, record in enumerate(records, start=2):  # start=2 так как первая строка - заголовки
            if record.get('id') == channel_id:
                row_idx = idx
                break
        
        if not row_idx:
            raise HTTPException(status_code=404, detail="Канал информирования не найден")
        
        # Обновляем данные
        update_data = {
            'id': channel_id,
            'Информирование': channel.type,
            'Проект': channel.project,
            'Дата старта': channel.start_date,
            'Название': channel.name,
            'Комментарий': channel.comment,
            'Сегмент': channel.segments,
            'Идентификатор промо': channel.promo_id,
            'Ссылка': channel.link
        }
        
        # Получаем заголовки
        headers = info_sheet.row_values(1)
        
        # Формируем список значений в том же порядке, что и заголовки
        values = [update_data.get(header, '') for header in headers]
        
        # Обновляем строку
        info_sheet.update(f'A{row_idx}:I{row_idx}', [values])
        
        return {"message": "Канал информирования успешно обновлен"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления канала информирования: {str(e)}")

@app.delete("/api/events/{event_id}")
async def delete_event(event_id: str):
    """Удалить промо событие и все связанные с ним каналы информирования"""
    try:
        spreadsheet = get_google_sheets_client()
        promo_sheet = spreadsheet.worksheet('ПРОМО')
        info_sheet = spreadsheet.worksheet('ИНФОРМИРОВАНИЕ')
        
        # Поиск и удаление промо события
        promo_records = promo_sheet.get_all_records()
        promo_row_idx = None
        
        for idx, record in enumerate(promo_records, start=2):  # start=2 так как первая строка - заголовки
            if record.get('id') == event_id:
                promo_row_idx = idx
                break
        
        if not promo_row_idx:
            raise HTTPException(status_code=404, detail="Промо событие не найдено")
        
        # Удаляем промо событие
        promo_sheet.delete_rows(promo_row_idx)
        
        # Поиск и удаление связанных каналов информирования
        info_records = info_sheet.get_all_records()
        info_rows_to_delete = []
        
        for idx, record in enumerate(info_records, start=2):
            if record.get('Идентификатор промо') == event_id:
                info_rows_to_delete.append(idx)
        
        # Удаляем связанные каналы информирования в обратном порядке,
        # чтобы не нарушить индексацию при множественном удалении
        for row_idx in sorted(info_rows_to_delete, reverse=True):
            info_sheet.delete_rows(row_idx)
        
        return {
            "message": "Промо событие и связанные каналы информирования успешно удалены",
            "deleted_channels_count": len(info_rows_to_delete)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка удаления промо события: {str(e)}")

@app.delete("/api/channels/{channel_id}")
async def delete_channel(channel_id: str):
    """Удалить канал информирования"""
    try:
        spreadsheet = get_google_sheets_client()
        info_sheet = spreadsheet.worksheet('ИНФОРМИРОВАНИЕ')
        
        # Поиск канала информирования
        records = info_sheet.get_all_records()
        row_idx = None
        
        for idx, record in enumerate(records, start=2):  # start=2 так как первая строка - заголовки
            if record.get('id') == channel_id:
                row_idx = idx
                break
        
        if not row_idx:
            raise HTTPException(status_code=404, detail="Канал информирования не найден")
        
        # Удаляем канал информирования
        info_sheet.delete_rows(row_idx)
        
        return {"message": "Канал информирования успешно удален"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка удаления канала информирования: {str(e)}")

@app.post("/api/channels", status_code=status.HTTP_201_CREATED)
async def create_channel(channel: InfoChannelCreate):
    """Создать новый канал информирования"""
    try:
        spreadsheet = get_google_sheets_client()
        info_sheet = spreadsheet.worksheet('ИНФОРМИРОВАНИЕ')
        
        # Валидация обязательных полей
        if not channel.type or not channel.project or not channel.name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не все обязательные поля заполнены"
            )
        
        # Создаем уникальный ID для канала
        unique_id = str(uuid.uuid4())
        
        # Формируем данные канала
        channel_data = {
            'id': unique_id,
            'Информирование': channel.type,
            'Проект': channel.project,
            'Дата старта': channel.start_date,
            'Название': channel.name,
            'Комментарий': channel.comment or '',
            'Сегмент': channel.segments or 'СНГ',
            'Идентификатор промо': channel.promo_id or '',
            'Ссылка': channel.link or ''
        }
        
        # Получаем заголовки из первой строки
        headers = info_sheet.row_values(1)
        if not headers:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Отсутствуют заголовки в таблице ИНФОРМИРОВАНИЕ"
            )
            
        # Формируем список значений в том же порядке, что и заголовки
        channel_row = [channel_data.get(header, '') for header in headers]
        
        # Добавляем новый канал
        info_sheet.append_row(channel_row)
        
        return {
            "message": "Канал информирования успешно создан",
            "id": unique_id,
            "channel": {
                "id": unique_id,
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
        spreadsheet = get_google_sheets_client()
        users_sheet = spreadsheet.worksheet('USERS')
        users_data = users_sheet.get_all_records()
        print(users_data)
        # Поиск пользователя
        user = None
        for row in users_data:
            print(row.get('login'), user_data.username, row.get('password'), user_data.password)
            if row.get('login').strip().lower() == user_data.username.strip().lower() and str(row.get('password')).strip().lower() == str(user_data.password).strip().lower():
                return {
                    "user": {
                        "username": row.get('login'),
                        "role": row.get('role', 'user')
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