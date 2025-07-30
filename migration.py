import mysql.connector
import gspread
import os
from datetime import datetime
import json
from typing import Optional, Dict, Any

class SheetsToMySQLMigrator:
    """Класс для миграции данных из Google Sheets в MySQL"""
    
    def __init__(self, mysql_config: Dict[str, str], sheets_credentials_path: str):
        """
        Инициализация мигратора
        
        Args:
            mysql_config: Конфигурация MySQL подключения
            sheets_credentials_path: Путь к файлу аутентификации Google Sheets
        """
        self.mysql_config = mysql_config
        self.sheets_credentials_path = sheets_credentials_path
        self.mysql_conn = None
        self.spreadsheet = None
        
    def connect_mysql(self):
        """Подключение к MySQL"""
        try:
            self.mysql_conn = mysql.connector.connect(**self.mysql_config)
            print("✅ Подключение к MySQL установлено")
        except Exception as e:
            print(f"❌ Ошибка подключения к MySQL: {e}")
            raise
    
    def connect_sheets(self):
        """Подключение к Google Sheets"""
        try:
            gc = gspread.service_account(filename=self.sheets_credentials_path)
            self.spreadsheet = gc.open_by_key('1LrJyEzeyM5ULgR1QjWXcHW_jM2RsYPxOo2RqjQB8URw')
            print("✅ Подключение к Google Sheets установлено")
        except Exception as e:
            print(f"❌ Ошибка подключения к Google Sheets: {e}")
            raise
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Парсинг даты из различных форматов"""
        if not date_str or date_str.strip() == '':
            return None
        
        try:
            date_str = date_str.strip()
            
            # Пробуем разные форматы
            if 'T' in date_str:
                # ISO формат
                return datetime.fromisoformat(date_str.replace('Z', '+00:00')).replace(tzinfo=None)
            elif ' ' in date_str:
                # Формат с пробелом
                if '.' in date_str.split()[0]:
                    # DD.MM.YYYY HH:MM:SS
                    return datetime.strptime(date_str.split()[0], "%d.%m.%Y")
                else:
                    # YYYY-MM-DD HH:MM:SS
                    return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            elif '.' in date_str:
                # DD.MM.YYYY
                return datetime.strptime(date_str, "%d.%m.%Y")
            else:
                # YYYY-MM-DD
                return datetime.strptime(date_str, "%Y-%m-%d")
        except Exception as e:
            print(f"⚠️ Не удалось распарсить дату '{date_str}': {e}")
            return None
    
    def find_user_by_email(self, email: str) -> Optional[int]:
        """Поиск пользователя по email для responsible_id"""
        if not email:
            return None
            
        cursor = self.mysql_conn.cursor()
        try:
            cursor.execute("SELECT id FROM users WHERE mail = %s", (email,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"⚠️ Ошибка поиска пользователя {email}: {e}")
            return None
        finally:
            cursor.close()
    
    def migrate_promotions(self):
        """Миграция данных из листа ПРОМО в таблицу promotions"""
        print("\n🔄 Начинаем миграцию промо-акций...")
        
        try:
            promo_sheet = self.spreadsheet.worksheet('ПРОМО')
            promo_data = promo_sheet.get_all_records()
            
            cursor = self.mysql_conn.cursor()
            
            # Очищаем таблицу (опционально)
            # cursor.execute("TRUNCATE TABLE promotions")
            
            success_count = 0
            error_count = 0
            
            for row in promo_data:
                try:
                    if not row.get('id'):  # Пропускаем строки без id
                        continue
                    
                    # Подготавливаем данные
                    project = row.get('Проект', '').strip() or None
                    promo_type = row.get('Тип промо', '').strip() or None
                    promo_kind = row.get('Вид промо', '').strip() or None
                    title = row.get('Название', '').strip()
                    comment = row.get('Комментарий', '').strip() or None
                    segment = row.get('Сегмент', '').strip() or None
                    link = row.get('Ссылка', '').strip() or None
                    
                    # Парсим даты
                    start_date = self.parse_date(row.get('Дата старта', ''))
                    end_date = self.parse_date(row.get('Дата конца', ''))
                    
                    # Ищем ответственного (если есть поле с email)
                    responsible_id = None
                    if 'Email ответственного' in row:
                        responsible_id = self.find_user_by_email(row.get('Email ответственного', ''))
                    
                    # Вставляем данные
                    insert_query = """
                        INSERT INTO promotions 
                        (project, promo_type, promo_kind, start_date, end_date, 
                         title, comment, segment, link, responsible_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    cursor.execute(insert_query, (
                        project, promo_type, promo_kind, start_date, end_date,
                        title, comment, segment, link, responsible_id
                    ))
                    
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    print(f"⚠️ Ошибка при обработке строки: {e}")
                    print(f"   Данные строки: {row}")
            
            self.mysql_conn.commit()
            cursor.close()
            
            print(f"✅ Миграция промо-акций завершена:")
            print(f"   - Успешно: {success_count}")
            print(f"   - Ошибок: {error_count}")
            
        except Exception as e:
            print(f"❌ Ошибка миграции промо-акций: {e}")
            raise
    
    def migrate_informing(self):
        """Миграция данных из листа ИНФОРМИРОВАНИЕ в таблицу informing"""
        print("\n🔄 Начинаем миграцию информирования...")
        
        try:
            info_sheet = self.spreadsheet.worksheet('ИНФОРМИРОВАНИЕ')
            info_data = info_sheet.get_all_records()
            
            cursor = self.mysql_conn.cursor()
            
            # Создаем мапинг ID промо из Google Sheets в MySQL ID
            promo_id_mapping = self.create_promo_id_mapping()
            
            success_count = 0
            error_count = 0
            
            for row in info_data:
                try:
                    if not row.get('id'):  # Пропускаем строки без id
                        continue
                    
                    # Подготавливаем данные
                    informing_type = row.get('Информирование', '').strip()
                    project = row.get('Проект', '').strip() or None
                    title = row.get('Название', '').strip()
                    comment = row.get('Комментарий', '').strip() or None
                    segment = row.get('Сегмент', '').strip() or None
                    link = row.get('Ссылка', '').strip() or None
                    
                    # Парсим дату
                    start_date = self.parse_date(row.get('Дата старта', ''))
                    
                    # Находим promo_id в MySQL
                    sheets_promo_id = row.get('Идентификатор промо', '').strip()
                    mysql_promo_id = promo_id_mapping.get(sheets_promo_id) if sheets_promo_id else None
                    
                    # Вставляем данные
                    insert_query = """
                        INSERT INTO informing 
                        (informing_type, project, start_date, title, comment, segment, promo_id, link)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    cursor.execute(insert_query, (
                        informing_type, project, start_date, title, comment, segment, mysql_promo_id, link
                    ))
                    
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    print(f"⚠️ Ошибка при обработке строки информирования: {e}")
                    print(f"   Данные строки: {row}")
            
            self.mysql_conn.commit()
            cursor.close()
            
            print(f"✅ Миграция информирования завершена:")
            print(f"   - Успешно: {success_count}")
            print(f"   - Ошибок: {error_count}")
            
        except Exception as e:
            print(f"❌ Ошибка миграции информирования: {e}")
            raise
    
    def create_promo_id_mapping(self) -> Dict[str, int]:
        """Создает маппинг между ID промо из Google Sheets и MySQL"""
        print("🔄 Создаем маппинг ID промо-акций...")
        
        try:
            # Получаем данные из Google Sheets
            promo_sheet = self.spreadsheet.worksheet('ПРОМО')
            promo_data = promo_sheet.get_all_records()
            
            # Получаем данные из MySQL
            cursor = self.mysql_conn.cursor()
            cursor.execute("SELECT id, title, project, start_date FROM promotions")
            mysql_promos = cursor.fetchall()
            cursor.close()
            
            mapping = {}
            
            for sheets_row in promo_data:
                sheets_id = sheets_row.get('id', '').strip()
                if not sheets_id:
                    continue
                
                sheets_title = sheets_row.get('Название', '').strip()
                sheets_project = sheets_row.get('Проект', '').strip()
                sheets_start_date = self.parse_date(sheets_row.get('Дата старта', ''))
                
                # Ищем соответствие в MySQL по названию и проекту
                for mysql_id, mysql_title, mysql_project, mysql_start_date in mysql_promos:
                    if (mysql_title == sheets_title and 
                        mysql_project == sheets_project and
                        mysql_start_date == sheets_start_date):
                        mapping[sheets_id] = mysql_id
                        break
            
            print(f"✅ Создан маппинг для {len(mapping)} промо-акций")
            return mapping
            
        except Exception as e:
            print(f"❌ Ошибка создания маппинга: {e}")
            return {}
    
    def run_migration(self):
        """Запуск полной миграции"""
        print("🚀 Начинаем миграцию данных из Google Sheets в MySQL")
        
        try:
            # Подключения
            self.connect_mysql()
            self.connect_sheets()
            
            # Миграция
            self.migrate_promotions()
            self.migrate_informing()
            
            print("\n🎉 Миграция успешно завершена!")
            
        except Exception as e:
            print(f"\n💥 Критическая ошибка миграции: {e}")
            raise
        finally:
            # Закрываем соединения
            if self.mysql_conn:
                self.mysql_conn.close()
                print("🔌 MySQL соединение закрыто")

def main():
    """Основная функция для запуска миграции"""
    
    # Конфигурация MySQL
    mysql_config = {
        'host': '91.209.226.31',  # или ваш хост
        'user': 'promo_user',
        'password': '789159987Cs',
        'database': 'promo_db',
        'charset': 'utf8mb4',
        'autocommit': False
    }

    # Путь к файлу аутентификации Google Sheets
    sheets_credentials_path = '../data/data.json'
    
    # Создаем и запускаем мигратор
    migrator = SheetsToMySQLMigrator(mysql_config, sheets_credentials_path)
    migrator.run_migration()

if __name__ == "__main__":
    main()