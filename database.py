import mysql.connector
from mysql.connector import pooling
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
import logging
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Конфигурация базы данных"""
    
    def __init__(self):
        self.config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'database': os.getenv('MYSQL_DATABASE', 'promo_calendar'),
            'charset': 'utf8mb4',
            'autocommit': False,
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'pool_name': 'promo_pool',
            'pool_size': 10,
            'pool_reset_session': True
        }
    
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

# Глобальные экземпляры - отложенная инициализация
db_manager = None
promo_repo = None
informing_repo = None
user_repo = None

def optimize_database():
    """Создать индексы для оптимизации производительности"""
    global db_manager
    if db_manager is None:
        return
    
    try:
        with db_manager.get_cursor(dictionary=False) as (cursor, connection):
            logger.info("🔧 Создание индексов для оптимизации производительности...")
            
            # Индексы для оптимизации JOIN запросов
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_informing_promo_id ON informing(promo_id)",
                "CREATE INDEX IF NOT EXISTS idx_promotions_start_date ON promotions(start_date)", 
                "CREATE INDEX IF NOT EXISTS idx_promotions_project ON promotions(project)",
                "CREATE INDEX IF NOT EXISTS idx_promotions_responsible_id ON promotions(responsible_id)",
                "CREATE INDEX IF NOT EXISTS idx_informing_promo_start ON informing(promo_id, start_date)",
                "CREATE INDEX IF NOT EXISTS idx_users_login ON users(login)"
            ]
            
            created_count = 0
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                    created_count += 1
                except Exception as e:
                    logger.warning(f"Индекс уже существует или ошибка: {e}")
            
            connection.commit()
            logger.info(f"✅ Оптимизация завершена. Обработано {created_count} индексов")
            
    except Exception as e:
        logger.error(f"❌ Ошибка оптимизации базы данных: {e}")

def get_db_manager():
    """Получить менеджер базы данных с отложенной инициализацией"""
    global db_manager, promo_repo, informing_repo, user_repo
    
    if db_manager is None:
        try:
            db_manager = DatabaseManager()
            promo_repo = PromoRepository(db_manager)
            informing_repo = InformingRepository(db_manager)
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
    return promo_repo, informing_repo, user_repo 