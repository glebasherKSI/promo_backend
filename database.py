import mysql.connector
from mysql.connector import pooling
import os
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
import logging
from dotenv import load_dotenv
import calendar

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Конфигурация базы данных"""
    
    def __init__(self):
        # Чтение настроек из .env файла
        self.host = os.getenv('MYSQL_HOST', 'localhost')
        self.user = os.getenv('MYSQL_USER', 'promo_user')
        self.password = os.getenv('MYSQL_PASSWORD', '789159987Cs')
        self.database = os.getenv('MYSQL_DATABASE', 'promo_db')
        self.port = int(os.getenv('MYSQL_PORT', '3306'))
        
        self.config = {
            'host': self.host,
            'user': self.user,
            'password': self.password,
            'database': self.database,
            'charset': 'utf8mb4',
            'autocommit': False,
            'port': self.port,
            'pool_name': 'promo_pool',
            'pool_size': 10,
            'pool_reset_session': True
        }
        
        print(f"🔧 Итоговая конфигурация БД:")
        print(f"   HOST: {self.config['host']}")
        print(f"   USER: {self.config['user']}")
        print(f"   DATABASE: {self.config['database']}")
        print(f"   PORT: {self.config['port']}")
        print(f"   PASSWORD установлен: {'Да' if self.config['password'] else 'Нет'}")
        
        # Дополнительная диагностика .env файла
        env_path = os.path.join(os.getcwd(), '.env')
        print(f"🔍 Поиск .env файла в: {env_path}")
        print(f"📁 Рабочая директория: {os.getcwd()}")
        print(f"📄 .env файл существует: {'Да' if os.path.exists('.env') else 'Нет'}")
        
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                content = f.read()
                print(f"📋 Размер .env файла: {len(content)} символов")
                # Исправляем синтаксическую ошибку - выносим обработку строк наружу
                env_variables = [line.split('=')[0] for line in content.split('\n') if '=' in line]
                print(f"🔑 Переменные в .env: {env_variables}")
    
    def get_pool_config(self):
        """Получить конфигурацию для пула соединений"""
        return self.config

class DatabaseManager:
    """Менеджер для работы с базой данных"""
    
    def __init__(self):
        self.config = DatabaseConfig()
        self.pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Инициализация пула соединений"""
        try:
            config = self.config.get_pool_config()
            logger.info(f"🔄 Попытка подключения к MySQL: {config['host']}:{config['port']}")
            logger.info(f"📋 Пользователь: {config['user']}, База данных: {config['database']}")
            
            self.pool = pooling.MySQLConnectionPool(**config)
            logger.info("✅ Пул соединений MySQL инициализирован")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации пула соединений: {e}")
            logger.error("💡 Проверьте:")
            logger.error("   - Запущен ли MySQL сервер")
            logger.error("   - Правильные ли настройки подключения в .env файле")
            logger.error("   - Доступен ли сервер по сети")
            raise
    
    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для получения соединения из пула"""
        connection = None
        try:
            connection = self.pool.get_connection()
            yield connection
        except Exception as e:
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                connection.close()
    
    @contextmanager
    def get_cursor(self, dictionary=True):
        """Контекстный менеджер для получения курсора"""
        with self.get_connection() as connection:
            cursor = connection.cursor(dictionary=dictionary)
            try:
                yield cursor, connection
            finally:
                cursor.close()

class PromoRepository:
    """Репозиторий для работы с промо-акциями"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_all_promotions(self) -> List[Dict[str, Any]]:
        """Получить все промо-акции"""
        try:
            with self.db.get_cursor() as (cursor, connection):
                query = """
                    SELECT p.*, u.login as responsible_name
                    FROM promotions p
                    LEFT JOIN users u ON p.responsible_id = u.id
                    ORDER BY p.start_date DESC
                """
                cursor.execute(query)
                promotions = cursor.fetchall()
                
                # Конвертируем даты в ISO формат для совместимости
                for promo in promotions:
                    if promo['start_date']:
                        promo['start_date'] = promo['start_date'].isoformat() + "Z"
                    if promo['end_date']:
                        promo['end_date'] = promo['end_date'].isoformat() + "Z"
                
                return promotions
        except Exception as e:
            logger.error(f"Ошибка получения промо-акций: {e}")
            raise
    
    def get_all_promotions_with_informing(self) -> List[Dict[str, Any]]:
        """Получить все промо-акции с информированиями одним запросом (оптимизированная версия)"""
        try:
            with self.db.get_cursor() as (cursor, connection):
                # Единый JOIN запрос вместо N+1 запросов
                query = """
                    SELECT 
                        p.id as promo_id,
                        p.project,
                        p.promo_type,
                        p.promo_kind,
                        p.start_date as promo_start_date,
                        p.end_date as promo_end_date,
                        p.title as promo_title,
                        p.comment as promo_comment,
                        p.segment as promo_segment,
                        p.link as promo_link,
                        p.responsible_id,
                        u.login as responsible_name,
                        i.id as info_id,
                        i.informing_type,
                        i.project as info_project,
                        i.start_date as info_start_date,
                        i.title as info_title,
                        i.comment as info_comment,
                        i.segment as info_segment,
                        i.link as info_link
                    FROM promotions p
                    LEFT JOIN users u ON p.responsible_id = u.id
                    LEFT JOIN informing i ON p.id = i.promo_id
                    ORDER BY p.start_date DESC, i.start_date ASC
                """
                
                cursor.execute(query)
                rows = cursor.fetchall()
                
                # Группируем результаты по промо-акциям
                promotions_map = {}
                
                for row in rows:
                    promo_id = row['promo_id']
                    
                    # Создаем промо-акцию если её ещё нет
                    if promo_id not in promotions_map:
                        promo_start_date = row['promo_start_date']
                        promo_end_date = row['promo_end_date']
                        
                        promotions_map[promo_id] = {
                            'id': promo_id,
                            'project': row['project'] or '',
                            'promo_type': row['promo_type'] or '',
                            'promo_kind': row['promo_kind'] or '',
                            'start_date': promo_start_date.isoformat() + "Z" if promo_start_date else '',
                            'end_date': promo_end_date.isoformat() + "Z" if promo_end_date else '',
                            'title': row['promo_title'] or '',
                            'comment': row['promo_comment'] or '',
                            'segment': row['promo_segment'] or '',
                            'link': row['promo_link'] or '',
                            'responsible_id': row['responsible_id'],
                            'responsible_name': row['responsible_name'],
                            'info_channels': []
                        }
                    
                    # Добавляем информирование если оно есть
                    if row['info_id']:
                        info_start_date = row['info_start_date']
                        
                        info_channel = {
                            'id': row['info_id'],
                            'type': row['informing_type'] or '',
                            'project': row['info_project'] or row['project'] or '',
                            'start_date': info_start_date.isoformat() + "Z" if info_start_date else '',
                            'name': row['info_title'] or '',
                            'comment': row['info_comment'] or '',
                            'segments': row['info_segment'] or '',
                            'promo_id': promo_id,
                            'link': row['info_link'] or ''
                        }
                        
                        promotions_map[promo_id]['info_channels'].append(info_channel)
                
                # Возвращаем список промо-акций
                promotions_list = list(promotions_map.values())
                
                logger.info(f"✅ Загружено {len(promotions_list)} промо-акций с информированиями одним запросом")
                return promotions_list
                
        except Exception as e:
            logger.error(f"Ошибка получения промо-акций с информированиями: {e}")
            raise

    def get_promotions_by_month(self, month: str) -> List[Dict[str, Any]]:
        """Получить промо-акции за конкретный месяц с информированиями"""
        try:
            # Парсим месяц в формате "YYYY-MM"
            year, month_num = month.split('-')
            year, month_num = int(year), int(month_num)
            
            # Вычисляем первый и последний день месяца
            first_day = date(year, month_num, 1)
            last_day = date(year, month_num, calendar.monthrange(year, month_num)[1])
            
            with self.db.get_cursor() as (cursor, connection):
                # Запрос для получения промо-акций, которые пересекаются с указанным месяцем
                query = """
                    SELECT 
                        p.id as promo_id,
                        p.project,
                        p.promo_type,
                        p.promo_kind,
                        p.start_date as promo_start_date,
                        p.end_date as promo_end_date,
                        p.title as promo_title,
                        p.comment as promo_comment,
                        p.segment as promo_segment,
                        p.link as promo_link,
                        p.responsible_id,
                        u.login as responsible_name,
                        i.id as info_id,
                        i.informing_type,
                        i.project as info_project,
                        i.start_date as info_start_date,
                        i.title as info_title,
                        i.comment as info_comment,
                        i.segment as info_segment,
                        i.link as info_link
                    FROM promotions p
                    LEFT JOIN users u ON p.responsible_id = u.id
                    LEFT JOIN informing i ON p.id = i.promo_id
                    WHERE (
                        -- Промо-акция начинается в указанном месяце
                        (p.start_date >= %s AND p.start_date <= %s)
                        OR 
                        -- Промо-акция заканчивается в указанном месяце
                        (p.end_date >= %s AND p.end_date <= %s)
                        OR
                        -- Промо-акция пересекает указанный месяц (начинается до и заканчивается после)
                        (p.start_date <= %s AND p.end_date >= %s)
                        OR
                        -- Есть информирование в указанном месяце
                        (i.start_date >= %s AND i.start_date <= %s)
                    )
                    ORDER BY p.start_date DESC, i.start_date ASC
                """
                
                cursor.execute(query, (
                    first_day, last_day,  # start_date в месяце
                    first_day, last_day,  # end_date в месяце
                    first_day, last_day,  # пересечение месяца
                    first_day, last_day   # информирование в месяце
                ))
                rows = cursor.fetchall()
                
                # Группируем результаты по промо-акциям
                promotions_map = {}
                
                for row in rows:
                    promo_id = row['promo_id']
                    
                    # Создаем промо-акцию если её ещё нет
                    if promo_id not in promotions_map:
                        promo_start_date = row['promo_start_date']
                        promo_end_date = row['promo_end_date']
                        
                        promotions_map[promo_id] = {
                            'id': promo_id,
                            'project': row['project'] or '',
                            'promo_type': row['promo_type'] or '',
                            'promo_kind': row['promo_kind'] or '',
                            'start_date': promo_start_date.isoformat() + "Z" if promo_start_date else '',
                            'end_date': promo_end_date.isoformat() + "Z" if promo_end_date else '',
                            'title': row['promo_title'] or '',
                            'comment': row['promo_comment'] or '',
                            'segment': row['promo_segment'] or '',
                            'link': row['promo_link'] or '',
                            'responsible_id': row['responsible_id'],
                            'responsible_name': row['responsible_name'],
                            'info_channels': []
                        }
                    
                    # Добавляем информирование если оно есть
                    if row['info_id']:
                        info_start_date = row['info_start_date']
                        
                        info_channel = {
                            'id': row['info_id'],
                            'type': row['informing_type'] or '',
                            'project': row['info_project'] or row['project'] or '',
                            'start_date': info_start_date.isoformat() + "Z" if info_start_date else '',
                            'name': row['info_title'] or '',
                            'comment': row['info_comment'] or '',
                            'segments': row['info_segment'] or '',
                            'promo_id': promo_id,
                            'link': row['info_link'] or ''
                        }
                        
                        promotions_map[promo_id]['info_channels'].append(info_channel)
                
                # Возвращаем список промо-акций
                promotions_list = list(promotions_map.values())
                
                logger.info(f"✅ Загружено {len(promotions_list)} промо-акций за {month} с информированиями")
                return promotions_list
                
        except Exception as e:
            logger.error(f"Ошибка получения промо-акций за месяц {month}: {e}")
            raise
    
    def get_promotion_by_id(self, promotion_id: int) -> Optional[Dict[str, Any]]:
        """Получить промо-акцию по ID"""
        try:
            with self.db.get_cursor() as (cursor, connection):
                query = """
                    SELECT p.*, u.login as responsible_name
                    FROM promotions p
                    LEFT JOIN users u ON p.responsible_id = u.id
                    WHERE p.id = %s
                """
                cursor.execute(query, (promotion_id,))
                promotion = cursor.fetchone()
                
                if promotion:
                    # Конвертируем даты
                    if promotion['start_date']:
                        promotion['start_date'] = promotion['start_date'].isoformat() + "Z"
                    if promotion['end_date']:
                        promotion['end_date'] = promotion['end_date'].isoformat() + "Z"
                
                return promotion
        except Exception as e:
            logger.error(f"Ошибка получения промо-акции {promotion_id}: {e}")
            raise
    
    def create_promotion(self, promotion_data: Dict[str, Any]) -> int:
        """Создать новую промо-акцию"""
        try:
            with self.db.get_cursor() as (cursor, connection):
                query = """
                    INSERT INTO promotions 
                    (project, promo_type, promo_kind, start_date, end_date, 
                     title, comment, segment, link, responsible_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                # Парсим даты
                start_date = self._parse_date(promotion_data.get('start_date'))
                end_date = self._parse_date(promotion_data.get('end_date'))
                
                cursor.execute(query, (
                    promotion_data.get('project'),
                    promotion_data.get('promo_type'),
                    promotion_data.get('promo_kind'),
                    start_date,
                    end_date,
                    promotion_data.get('name'),  # В БД это title
                    promotion_data.get('comment'),
                    promotion_data.get('segments'),  # В БД это segment
                    promotion_data.get('link'),
                    promotion_data.get('responsible_id')
                ))
                
                promotion_id = cursor.lastrowid
                connection.commit()
                logger.info(f"✅ Создана промо-акция с ID: {promotion_id}")
                return promotion_id
        except Exception as e:
            logger.error(f"Ошибка создания промо-акции: {e}")
            raise
    
    def create_promotions_batch(self, promotions_data: List[Dict[str, Any]]) -> List[int]:
        """Создать несколько промо-акций одним запросом (batch insert)"""
        try:
            with self.db.get_cursor() as (cursor, connection):
                query = """
                    INSERT INTO promotions 
                    (project, promo_type, promo_kind, start_date, end_date, 
                     title, comment, segment, link, responsible_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                # Подготавливаем данные для batch insert
                values = []
                for promo_data in promotions_data:
                    start_date = self._parse_date(promo_data.get('start_date'))
                    end_date = self._parse_date(promo_data.get('end_date'))
                    
                    values.append((
                        promo_data.get('project'),
                        promo_data.get('promo_type'),
                        promo_data.get('promo_kind'),
                        start_date,
                        end_date,
                        promo_data.get('name'),  # В БД это title
                        promo_data.get('comment'),
                        promo_data.get('segments'),  # В БД это segment
                        promo_data.get('link'),
                        promo_data.get('responsible_id')
                    ))
                
                # Выполняем batch insert
                cursor.executemany(query, values)
                connection.commit()
                
                # Получаем ID созданных записей
                first_id = cursor.lastrowid
                created_ids = list(range(first_id, first_id + len(promotions_data)))
                
                logger.info(f"✅ Создано {len(created_ids)} промо-акций одним запросом: {created_ids}")
                return created_ids
        except Exception as e:
            logger.error(f"Ошибка batch создания промо-акций: {e}")
            raise
    
    def update_promotion(self, promotion_id: int, promotion_data: Dict[str, Any]) -> bool:
        """Обновить промо-акцию"""
        try:
            with self.db.get_cursor() as (cursor, connection):
                query = """
                    UPDATE promotions 
                    SET project = %s, promo_type = %s, promo_kind = %s, 
                        start_date = %s, end_date = %s, title = %s, 
                        comment = %s, segment = %s, link = %s, responsible_id = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """
                
                # Парсим даты
                start_date = self._parse_date(promotion_data.get('start_date'))
                end_date = self._parse_date(promotion_data.get('end_date'))
                
                cursor.execute(query, (
                    promotion_data.get('project'),
                    promotion_data.get('promo_type'),
                    promotion_data.get('promo_kind'),
                    start_date,
                    end_date,
                    promotion_data.get('name'),
                    promotion_data.get('comment'),
                    promotion_data.get('segments'),
                    promotion_data.get('link'),
                    promotion_data.get('responsible_id'),
                    promotion_id
                ))
                
                affected_rows = cursor.rowcount
                connection.commit()
                
                logger.info(f"✅ Обновлена промо-акция {promotion_id}")
                return affected_rows > 0
        except Exception as e:
            logger.error(f"Ошибка обновления промо-акции {promotion_id}: {e}")
            raise
    
    def delete_promotion(self, promotion_id: int) -> bool:
        """Удалить промо-акцию"""
        try:
            with self.db.get_cursor() as (cursor, connection):
                # Сначала удаляем связанные информирования
                cursor.execute("DELETE FROM informing WHERE promo_id = %s", (promotion_id,))
                
                # Затем удаляем промо-акцию
                cursor.execute("DELETE FROM promotions WHERE id = %s", (promotion_id,))
                
                affected_rows = cursor.rowcount
                connection.commit()
                
                logger.info(f"✅ Удалена промо-акция {promotion_id}")
                return affected_rows > 0
        except Exception as e:
            logger.error(f"Ошибка удаления промо-акции {promotion_id}: {e}")
            raise
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Парсинг даты из строки"""
        if not date_str:
            return None
        
        try:
            date_str = date_str.strip()
            
            if 'T' in date_str:
                # ISO формат
                return datetime.fromisoformat(date_str.replace('Z', '+00:00')).replace(tzinfo=None)
            elif ' ' in date_str:
                # Формат с пробелом
                return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            else:
                # Простой формат даты
                return datetime.strptime(date_str, "%Y-%m-%d")
        except Exception as e:
            logger.warning(f"Не удалось распарсить дату '{date_str}': {e}")
            return None

class InformingRepository:
    """Репозиторий для работы с информированием"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_all_informing(self) -> List[Dict[str, Any]]:
        """Получить все информирования"""
        try:
            with self.db.get_cursor() as (cursor, connection):
                query = """
                    SELECT i.*, p.title as promo_title
                    FROM informing i
                    LEFT JOIN promotions p ON i.promo_id = p.id
                    ORDER BY i.start_date DESC
                """
                cursor.execute(query)
                informings = cursor.fetchall()
                
                # Конвертируем даты
                for info in informings:
                    if info['start_date']:
                        info['start_date'] = info['start_date'].isoformat() + "Z"
                
                return informings
        except Exception as e:
            logger.error(f"Ошибка получения информирований: {e}")
            raise
    
    def get_informing_by_promo_id(self, promo_id: int) -> List[Dict[str, Any]]:
        """Получить информирования по ID промо-акции"""
        try:
            with self.db.get_cursor() as (cursor, connection):
                query = """
                    SELECT * FROM informing 
                    WHERE promo_id = %s 
                    ORDER BY start_date
                """
                cursor.execute(query, (promo_id,))
                informings = cursor.fetchall()
                
                # Конвертируем даты и форматируем для совместимости
                for info in informings:
                    if info['start_date']:
                        info['start_date'] = info['start_date'].isoformat() + "Z"
                    
                    # Переименовываем поля для совместимости с фронтендом
                    info['type'] = info['informing_type']
                    info['name'] = info['title']
                    info['segments'] = info['segment']
                
                return informings
        except Exception as e:
            logger.error(f"Ошибка получения информирований для промо {promo_id}: {e}")
            raise
    
    def create_informing(self, informing_data: Dict[str, Any]) -> int:
        """Создать новое информирование"""
        try:
            with self.db.get_cursor() as (cursor, connection):
                query = """
                    INSERT INTO informing 
                    (informing_type, project, start_date, title, comment, segment, promo_id, link)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                start_date = self._parse_date(informing_data.get('start_date'))
                
                cursor.execute(query, (
                    informing_data.get('type'),  # В БД это informing_type
                    informing_data.get('project'),
                    start_date,
                    informing_data.get('name'),  # В БД это title
                    informing_data.get('comment'),
                    informing_data.get('segments'),  # В БД это segment
                    informing_data.get('promo_id'),
                    informing_data.get('link')
                ))
                
                informing_id = cursor.lastrowid
                connection.commit()
                logger.info(f"✅ Создано информирование с ID: {informing_id}")
                return informing_id
        except Exception as e:
            logger.error(f"Ошибка создания информирования: {e}")
            raise
    
    def create_informings_batch(self, informings_data: List[Dict[str, Any]]) -> List[int]:
        """Создать несколько информирований одним запросом (batch insert)"""
        try:
            with self.db.get_cursor() as (cursor, connection):
                query = """
                    INSERT INTO informing 
                    (informing_type, project, start_date, title, comment, segment, promo_id, link)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                # Подготавливаем данные для batch insert
                values = []
                for info_data in informings_data:
                    start_date = self._parse_date(info_data.get('start_date'))
                    
                    values.append((
                        info_data.get('type'),  # В БД это informing_type
                        info_data.get('project'),
                        start_date,
                        info_data.get('name'),  # В БД это title
                        info_data.get('comment'),
                        info_data.get('segments'),  # В БД это segment
                        info_data.get('promo_id'),
                        info_data.get('link')
                    ))
                
                # Выполняем batch insert
                cursor.executemany(query, values)
                connection.commit()
                
                # Получаем ID созданных записей
                first_id = cursor.lastrowid
                created_ids = list(range(first_id, first_id + len(informings_data)))
                
                logger.info(f"✅ Создано {len(created_ids)} информирований одним запросом: {created_ids}")
                return created_ids
        except Exception as e:
            logger.error(f"Ошибка batch создания информирований: {e}")
            raise
    
    def update_informing(self, informing_id: int, informing_data: Dict[str, Any]) -> bool:
        """Обновить информирование"""
        try:
            with self.db.get_cursor() as (cursor, connection):
                query = """
                    UPDATE informing 
                    SET informing_type = %s, project = %s, start_date = %s, 
                        title = %s, comment = %s, segment = %s, promo_id = %s, 
                        link = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """
                
                start_date = self._parse_date(informing_data.get('start_date'))
                
                cursor.execute(query, (
                    informing_data.get('type'),
                    informing_data.get('project'),
                    start_date,
                    informing_data.get('name'),
                    informing_data.get('comment'),
                    informing_data.get('segments'),
                    informing_data.get('promo_id'),
                    informing_data.get('link'),
                    informing_id
                ))
                
                affected_rows = cursor.rowcount
                connection.commit()
                
                logger.info(f"✅ Обновлено информирование {informing_id}")
                return affected_rows > 0
        except Exception as e:
            logger.error(f"Ошибка обновления информирования {informing_id}: {e}")
            raise
    
    def delete_informing(self, informing_id: int) -> bool:
        """Удалить информирование"""
        try:
            with self.db.get_cursor() as (cursor, connection):
                cursor.execute("DELETE FROM informing WHERE id = %s", (informing_id,))
                
                affected_rows = cursor.rowcount
                connection.commit()
                
                logger.info(f"✅ Удалено информирование {informing_id}")
                return affected_rows > 0
        except Exception as e:
            logger.error(f"Ошибка удаления информирования {informing_id}: {e}")
            raise
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Парсинг даты из строки"""
        if not date_str:
            return None
        
        try:
            date_str = date_str.strip()
            
            if 'T' in date_str:
                # ISO формат
                return datetime.fromisoformat(date_str.replace('Z', '+00:00')).replace(tzinfo=None)
            elif ' ' in date_str:
                # Формат с пробелом
                return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            else:
                # Простой формат даты
                return datetime.strptime(date_str, "%Y-%m-%d")
        except Exception as e:
            logger.warning(f"Не удалось распарсить дату '{date_str}': {e}")
            return None

class OccurrenceRepository:
    """Репозиторий для работы с рекуррентными событиями (promotion_occurrences)"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_occurrences_by_month(self, month: str) -> List[Dict[str, Any]]:
        """Получить рекуррентные события за конкретный месяц с данными из promotions"""
        try:
            # Парсим месяц в формате "YYYY-MM"
            year, month_num = month.split('-')
            year, month_num = int(year), int(month_num)
            
            # Вычисляем первый и последний день месяца
            first_day = date(year, month_num, 1)
            last_day = date(year, month_num, calendar.monthrange(year, month_num)[1])
            
            with self.db.get_cursor() as (cursor, connection):
                # Запрос для получения рекуррентных событий, которые пересекаются с указанным месяцем
                query = """
                    SELECT 
                        po.id as occurrence_id,
                        po.promo_id,
                        po.occurrence_start,
                        po.occurrence_end,
                        po.occurrence_key,
                        p.project,
                        p.promo_type,
                        p.promo_kind,
                        p.title as promo_title,
                        p.comment as promo_comment,
                        p.segment as promo_segment,
                        p.link as promo_link,
                        p.responsible_id,
                        u.login as responsible_name,
                        i.id as info_id,
                        i.informing_type,
                        i.project as info_project,
                        i.start_date as info_start_date,
                        i.title as info_title,
                        i.comment as info_comment,
                        i.segment as info_segment,
                        i.link as info_link
                    FROM promotion_occurrences po
                    INNER JOIN promotions p ON po.promo_id = p.id
                    LEFT JOIN users u ON p.responsible_id = u.id
                    LEFT JOIN informing i ON p.id = i.promo_id
                    WHERE (
                        -- Вхождение начинается в указанном месяце
                        (po.occurrence_start >= %s AND po.occurrence_start <= %s)
                        OR 
                        -- Вхождение заканчивается в указанном месяце
                        (po.occurrence_end >= %s AND po.occurrence_end <= %s)
                        OR
                        -- Вхождение пересекает указанный месяц (начинается до и заканчивается после)
                        (po.occurrence_start <= %s AND po.occurrence_end >= %s)
                    )
                    ORDER BY po.occurrence_start ASC, i.start_date ASC
                """
                
                cursor.execute(query, (
                    first_day, last_day,  # occurrence_start в месяце
                    first_day, last_day,  # occurrence_end в месяце
                    first_day, last_day   # пересечение месяца
                ))
                rows = cursor.fetchall()
                
                # Группируем результаты по вхождениям
                occurrences_map = {}
                
                for row in rows:
                    occurrence_key = row['occurrence_key']
                    
                    # Создаем вхождение если его ещё нет
                    if occurrence_key not in occurrences_map:
                        occurrence_start = row['occurrence_start']
                        occurrence_end = row['occurrence_end']
                        
                        occurrences_map[occurrence_key] = {
                            'id': f"occ_{row['occurrence_id']}",  # Префикс для отличия от обычных промо
                            'promo_id': row['promo_id'],
                            'occurrence_id': row['occurrence_id'],
                            'occurrence_key': row['occurrence_key'],
                            'project': row['project'] or '',
                            'promo_type': row['promo_type'] or '',
                            'promo_kind': row['promo_kind'] or '',
                            'start_date': occurrence_start.isoformat() + "Z" if occurrence_start else '',
                            'end_date': occurrence_end.isoformat() + "Z" if occurrence_end else '',
                            'name': row['promo_title'] or '',
                            'comment': row['promo_comment'] or '',
                            'segment': row['promo_segment'] or '',
                            'link': row['promo_link'] or '',
                            'responsible_id': row['responsible_id'],
                            'responsible_name': row['responsible_name'],
                            'info_channels': [],
                            'is_recurring': True  # Флаг для отличия от обычных событий
                        }
                    
                    # Добавляем информирование если оно есть
                    if row['info_id']:
                        info_start_date = row['info_start_date']
                        
                        info_channel = {
                            'id': row['info_id'],
                            'type': row['informing_type'] or '',
                            'project': row['info_project'] or row['project'] or '',
                            'start_date': info_start_date.isoformat() + "Z" if info_start_date else '',
                            'name': row['info_title'] or '',
                            'comment': row['info_comment'] or '',
                            'segments': row['info_segment'] or '',
                            'promo_id': row['promo_id'],
                            'link': row['info_link'] or ''
                        }
                        
                        occurrences_map[occurrence_key]['info_channels'].append(info_channel)
                
                # Возвращаем список вхождений
                occurrences_list = list(occurrences_map.values())
                
                logger.info(f"✅ Загружено {len(occurrences_list)} рекуррентных событий за {month}")
                return occurrences_list
                
        except Exception as e:
            logger.error(f"Ошибка получения рекуррентных событий за месяц {month}: {e}")
            raise
    
    def get_occurrences_by_promo_id(self, promo_id: int) -> List[Dict[str, Any]]:
        """Получить все вхождения для конкретной промо-акции"""
        try:
            with self.db.get_cursor() as (cursor, connection):
                query = """
                    SELECT * FROM promotion_occurrences 
                    WHERE promo_id = %s 
                    ORDER BY occurrence_start ASC
                """
                cursor.execute(query, (promo_id,))
                occurrences = cursor.fetchall()
                
                # Конвертируем даты
                for occ in occurrences:
                    if occ['occurrence_start']:
                        occ['occurrence_start'] = occ['occurrence_start'].isoformat() + "Z"
                    if occ['occurrence_end']:
                        occ['occurrence_end'] = occ['occurrence_end'].isoformat() + "Z"
                
                return occurrences
        except Exception as e:
            logger.error(f"Ошибка получения вхождений для промо {promo_id}: {e}")
            raise
    
    def get_occurrence_by_id(self, occurrence_id: int) -> Optional[Dict[str, Any]]:
        """Получить вхождение по ID"""
        try:
            with self.db.get_cursor() as (cursor, connection):
                query = """
                    SELECT * FROM promotion_occurrences 
                    WHERE id = %s
                """
                logger.info(f"🔍 Поиск вхождения с ID {occurrence_id}")
                cursor.execute(query, (occurrence_id,))
                occurrence = cursor.fetchone()
                
                if occurrence:
                    logger.info(f"✅ Найдено вхождение: {occurrence}")
                    # Конвертируем даты
                    if occurrence['occurrence_start']:
                        occurrence['occurrence_start'] = occurrence['occurrence_start'].isoformat() + "Z"
                    if occurrence['occurrence_end']:
                        occurrence['occurrence_end'] = occurrence['occurrence_end'].isoformat() + "Z"
                else:
                    logger.warning(f"❌ Вхождение с ID {occurrence_id} не найдено")
                
                return occurrence
        except Exception as e:
            logger.error(f"Ошибка получения вхождения {occurrence_id}: {e}")
            raise
    
    def create_occurrence(self, occurrence_data: Dict[str, Any]) -> int:
        """Создать новое вхождение"""
        try:
            with self.db.get_cursor() as (cursor, connection):
                query = """
                    INSERT INTO promotion_occurrences 
                    (promo_id, occurrence_start, occurrence_end, occurrence_key)
                    VALUES (%s, %s, %s, %s)
                """
                
                occurrence_start = self._parse_date(occurrence_data.get('occurrence_start'))
                occurrence_end = self._parse_date(occurrence_data.get('occurrence_end'))
                
                cursor.execute(query, (
                    occurrence_data.get('promo_id'),
                    occurrence_start,
                    occurrence_end,
                    occurrence_data.get('occurrence_key')
                ))
                
                occurrence_id = cursor.lastrowid
                connection.commit()
                logger.info(f"✅ Создано вхождение с ID: {occurrence_id}")
                return occurrence_id
        except Exception as e:
            logger.error(f"Ошибка создания вхождения: {e}")
            raise
    
    def create_occurrences_batch(self, occurrences_data: List[Dict[str, Any]]) -> List[int]:
        """Создать несколько вхождений одним запросом (batch insert)"""
        try:
            with self.db.get_cursor() as (cursor, connection):
                query = """
                    INSERT INTO promotion_occurrences 
                    (promo_id, occurrence_start, occurrence_end, occurrence_key)
                    VALUES (%s, %s, %s, %s)
                """
                
                # Подготавливаем данные для batch insert
                values = []
                for occ_data in occurrences_data:
                    occurrence_start = self._parse_date(occ_data.get('occurrence_start'))
                    occurrence_end = self._parse_date(occ_data.get('occurrence_end'))
                    
                    values.append((
                        occ_data.get('promo_id'),
                        occurrence_start,
                        occurrence_end,
                        occ_data.get('occurrence_key')
                    ))
                
                # Выполняем batch insert
                cursor.executemany(query, values)
                connection.commit()
                
                # Получаем ID созданных записей
                first_id = cursor.lastrowid
                created_ids = list(range(first_id, first_id + len(occurrences_data)))
                
                logger.info(f"✅ Создано {len(created_ids)} вхождений одним запросом: {created_ids}")
                return created_ids
        except Exception as e:
            logger.error(f"Ошибка batch создания вхождений: {e}")
            raise
    
    def update_occurrence(self, occurrence_id: int, occurrence_data: Dict[str, Any]) -> bool:
        """Обновить вхождение"""
        try:
            with self.db.get_cursor() as (cursor, connection):
                query = """
                    UPDATE promotion_occurrences 
                    SET promo_id = %s, occurrence_start = %s, occurrence_end = %s, 
                        occurrence_key = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """
                
                occurrence_start = self._parse_date(occurrence_data.get('occurrence_start'))
                occurrence_end = self._parse_date(occurrence_data.get('occurrence_end'))
                
                cursor.execute(query, (
                    occurrence_data.get('promo_id'),
                    occurrence_start,
                    occurrence_end,
                    occurrence_data.get('occurrence_key'),
                    occurrence_id
                ))
                
                affected_rows = cursor.rowcount
                connection.commit()
                
                logger.info(f"✅ Обновлено вхождение {occurrence_id}")
                return affected_rows > 0
        except Exception as e:
            logger.error(f"Ошибка обновления вхождения {occurrence_id}: {e}")
            raise
    
    def delete_occurrence(self, occurrence_id: int) -> bool:
        """Удалить вхождение"""
        try:
            with self.db.get_cursor() as (cursor, connection):
                cursor.execute("DELETE FROM promotion_occurrences WHERE id = %s", (occurrence_id,))
                
                affected_rows = cursor.rowcount
                connection.commit()
                
                logger.info(f"✅ Удалено вхождение {occurrence_id}")
                return affected_rows > 0
        except Exception as e:
            logger.error(f"Ошибка удаления вхождения {occurrence_id}: {e}")
            raise
    
    def delete_occurrences_by_promo_id(self, promo_id: int) -> bool:
        """Удалить все вхождения для конкретной промо-акции"""
        try:
            with self.db.get_cursor() as (cursor, connection):
                cursor.execute("DELETE FROM promotion_occurrences WHERE promo_id = %s", (promo_id,))
                
                affected_rows = cursor.rowcount
                connection.commit()
                
                logger.info(f"✅ Удалено {affected_rows} вхождений для промо-акции {promo_id}")
                return affected_rows > 0
        except Exception as e:
            logger.error(f"Ошибка удаления вхождений для промо-акции {promo_id}: {e}")
            raise
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Парсинг даты из строки"""
        if not date_str:
            return None
        
        try:
            date_str = date_str.strip()
            
            if 'T' in date_str:
                # ISO формат
                return datetime.fromisoformat(date_str.replace('Z', '+00:00')).replace(tzinfo=None)
            elif ' ' in date_str:
                # Формат с пробелом
                return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            else:
                # Простой формат даты
                return datetime.strptime(date_str, "%Y-%m-%d")
        except Exception as e:
            logger.warning(f"Не удалось распарсить дату '{date_str}': {e}")
            return None

class UserRepository:
    """Репозиторий для работы с пользователями"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_user_by_credentials(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Получить пользователя по логину и паролю"""
        try:
            with self.db.get_cursor() as (cursor, connection):
                query = "SELECT * FROM users WHERE login = %s AND password = %s"
                cursor.execute(query, (username.strip().lower(), password.strip()))
                user = cursor.fetchone()
                return user
        except Exception as e:
            logger.error(f"Ошибка получения пользователя: {e}")
            raise
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Получить пользователя по email"""
        try:
            with self.db.get_cursor() as (cursor, connection):
                query = "SELECT * FROM users WHERE mail = %s"
                cursor.execute(query, (email,))
                user = cursor.fetchone()
                return user
        except Exception as e:
            logger.error(f"Ошибка получения пользователя по email: {e}")
            raise
    
    def get_user_by_login(self, login: str) -> Optional[Dict[str, Any]]:
        """Получить пользователя по логину"""
        try:
            with self.db.get_cursor() as (cursor, connection):
                # Используем LOWER() для регистронезависимого поиска
                query = "SELECT * FROM users WHERE LOWER(login) = LOWER(%s)"
                cursor.execute(query, (login.strip(),))
                user = cursor.fetchone()
                logger.info(f"🔍 Поиск пользователя по логину '{login}': {'найден' if user else 'не найден'}")
                return user
        except Exception as e:
            logger.error(f"Ошибка получения пользователя по логину: {e}")
            raise
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить пользователя по ID"""
        try:
            with self.db.get_cursor() as (cursor, connection):
                query = "SELECT * FROM users WHERE id = %s"
                cursor.execute(query, (user_id,))
                user = cursor.fetchone()
                return user
        except Exception as e:
            logger.error(f"Ошибка получения пользователя по ID: {e}")
            raise
    
    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """Обновить данные пользователя"""
        try:
            # Фильтруем только разрешенные поля
            allowed_fields = ['login', 'password', 'token', 'mail', 'server', 'accountId', 'api_key', 'token_trello']
            filtered_data = {k: v for k, v in user_data.items() if k in allowed_fields and v is not None}
            
            if not filtered_data:
                logger.warning(f"Нет данных для обновления пользователя {user_id}")
                return False
            
            # Строим запрос UPDATE
            set_clause = ", ".join([f"{field} = %s" for field in filtered_data.keys()])
            query = f"UPDATE users SET {set_clause} WHERE id = %s"
            values = list(filtered_data.values()) + [user_id]
            
            with self.db.get_cursor() as (cursor, connection):
                cursor.execute(query, values)
                affected_rows = cursor.rowcount
                connection.commit()
                
                logger.info(f"✅ Обновлен пользователь {user_id}")
                return affected_rows > 0
                
        except Exception as e:
            logger.error(f"Ошибка обновления пользователя {user_id}: {e}")
            raise
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Получить всех пользователей"""
        try:
            with self.db.get_cursor() as (cursor, connection):
                query = "SELECT * FROM users ORDER BY login"
                cursor.execute(query)
                users = cursor.fetchall()
                logger.info(f"📋 Найдено пользователей: {len(users)}")
                return users
        except Exception as e:
            logger.error(f"Ошибка получения всех пользователей: {e}")
            raise

# Глобальные экземпляры - отложенная инициализация
db_manager = None
promo_repo = None
informing_repo = None
occurrence_repo = None
user_repo = None

def optimize_database():
    """Создать индексы для оптимизации производительности"""
    global db_manager
    if db_manager is None:
        return
    
    try:
        with db_manager.get_cursor(dictionary=False) as (cursor, connection):
            logger.info("🔧 Создание индексов для оптимизации производительности...")
            
            # Индексы для оптимизации JOIN запросов (MySQL совместимый синтаксис)
            indexes = [
                ("idx_informing_promo_id", "informing", "promo_id"),
                ("idx_promotions_start_date", "promotions", "start_date"),
                ("idx_promotions_project", "promotions", "project"),
                ("idx_promotions_responsible_id", "promotions", "responsible_id"),
                ("idx_informing_promo_start", "informing", "promo_id, start_date"),
                ("idx_users_login", "users", "login"),
                ("idx_occurrences_promo_id", "promotion_occurrences", "promo_id"),
                ("idx_occurrences_dates", "promotion_occurrences", "occurrence_start, occurrence_end"),
                ("idx_occurrences_key", "promotion_occurrences", "occurrence_key")
            ]
            
            created_count = 0
            for index_name, table_name, columns in indexes:
                try:
                    # Проверяем, существует ли индекс
                    check_query = f"""
                        SELECT COUNT(*) 
                        FROM information_schema.statistics 
                        WHERE table_schema = DATABASE() 
                        AND table_name = '{table_name}' 
                        AND index_name = '{index_name}'
                    """
                    cursor.execute(check_query)
                    exists = cursor.fetchone()[0] > 0
                    
                    if not exists:
                        # Создаем индекс только если он не существует
                        create_query = f"CREATE INDEX {index_name} ON {table_name}({columns})"
                        cursor.execute(create_query)
                        created_count += 1
                        logger.info(f"✅ Создан индекс {index_name}")
                    else:
                        logger.info(f"ℹ️ Индекс {index_name} уже существует")
                        
                except Exception as e:
                    logger.warning(f"Ошибка при создании индекса {index_name}: {e}")
            
            connection.commit()
            logger.info(f"✅ Оптимизация завершена. Создано {created_count} новых индексов")
            
    except Exception as e:
        logger.error(f"❌ Ошибка оптимизации базы данных: {e}")

def get_db_manager():
    """Получить менеджер базы данных с отложенной инициализацией"""
    global db_manager, promo_repo, informing_repo, occurrence_repo, user_repo
    
    if db_manager is None:
        try:
            db_manager = DatabaseManager()
            promo_repo = PromoRepository(db_manager)
            informing_repo = InformingRepository(db_manager)
            occurrence_repo = OccurrenceRepository(db_manager)
            user_repo = UserRepository(db_manager)
            logger.info("✅ База данных успешно инициализирована")
            
            # Автоматически создаем индексы для оптимизации
            optimize_database()
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации базы данных: {e}")
            raise
    
    return db_manager

def get_repositories():
    """Получить репозитории с проверкой инициализации"""
    get_db_manager()  # Убеждаемся что БД инициализирована
    return promo_repo, informing_repo, occurrence_repo, user_repo 