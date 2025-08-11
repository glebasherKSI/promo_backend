-- Убедимся, что используем UTF8MB4
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- Создаём базу данных (если ещё не создана)
CREATE DATABASE IF NOT EXISTS promo_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Используем базу данных
USE promo_db;

-- Таблица users
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    login VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL, -- Хранить в хеше (например, bcrypt)
    role VARCHAR(50) NOT NULL,
    token TEXT,
    mail VARCHAR(255),
    server VARCHAR(100),
    accountId VARCHAR(100),
    api_key VARCHAR(255),
    token_trello VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Таблица promotions
CREATE TABLE IF NOT EXISTS promotions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project VARCHAR(100),
    promo_type VARCHAR(100),         -- Тип промо
    promo_kind VARCHAR(100),         -- Вид промо
    start_date DATETIME,             -- Дата старта
    end_date DATETIME,               -- Дата конца
    title VARCHAR(255) NOT NULL,     -- Название
    comment TEXT,                    -- Комментарий
    segment VARCHAR(255),            -- Сегмент
    link VARCHAR(500),               -- Ссылка
    responsible_id INT,              -- Внешний ключ на users(id)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (responsible_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Таблица informing (информирование)
CREATE TABLE IF NOT EXISTS informing (
    id INT AUTO_INCREMENT PRIMARY KEY,
    informing_type VARCHAR(100) NOT NULL,  -- Тип информирования
    project VARCHAR(100),
    start_date DATETIME,                   -- Дата старта
    title VARCHAR(255) NOT NULL,
    comment TEXT,
    segment VARCHAR(255),
    promo_id INT,                          -- Внешний ключ на promotions(id)
    link VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (promo_id) REFERENCES promotions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Таблица promotion_occurrences (рекуррентные события)
CREATE TABLE IF NOT EXISTS promotion_occurrences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    promo_id INT NOT NULL,                 -- Внешний ключ на promotions(id)
    occurrence_start DATETIME NOT NULL,    -- Дата начала конкретного вхождения
    occurrence_end DATETIME NOT NULL,      -- Дата окончания конкретного вхождения
    occurrence_key VARCHAR(255) UNIQUE,    -- Уникальный ключ вхождения (например, promo_id#YYYYMMDDHHMMSS)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (promo_id) REFERENCES promotions(id) ON DELETE CASCADE,
    INDEX idx_promo_id (promo_id),
    INDEX idx_occurrence_dates (occurrence_start, occurrence_end),
    INDEX idx_occurrence_key (occurrence_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;