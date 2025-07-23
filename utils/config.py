# config.py
import os
from typing import Dict

def get_mysql_config() -> Dict[str, str]:
    """Получение конфигурации MySQL из переменных окружения или настроек"""
    return {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'promo_calendar'),
        'charset': 'utf8mb4',
        'autocommit': False,
        'port': int(os.getenv('MYSQL_PORT', 3306))
    }

# Путь к файлу аутентификации Google Sheets
SHEETS_CREDENTIALS_PATH = os.getenv('SHEETS_CREDENTIALS_PATH', '../data/data.json')

# ID таблицы Google Sheets
SHEETS_ID = '1LrJyEzeyM5ULgR1QjWXcHW_jM2RsYPxOo2RqjQB8URw'