-- Скрипт оптимизации базы данных для ускорения запросов
-- Выполните эти команды в вашей MySQL базе данных

-- 1. Индекс для связи informing -> promotions (самый важный для JOIN)
CREATE INDEX IF NOT EXISTS idx_informing_promo_id ON informing(promo_id);

-- 2. Индекс для сортировки промо-акций по дате
CREATE INDEX IF NOT EXISTS idx_promotions_start_date ON promotions(start_date);

-- 3. Индекс для фильтрации по проекту (если будет нужен)
CREATE INDEX IF NOT EXISTS idx_promotions_project ON promotions(project);

-- 4. Индекс для связи promotions -> users
CREATE INDEX IF NOT EXISTS idx_promotions_responsible_id ON promotions(responsible_id);

-- 5. Составной индекс для информирований (promo_id + start_date для сортировки)
CREATE INDEX IF NOT EXISTS idx_informing_promo_start ON informing(promo_id, start_date);

-- 6. Индекс для поиска пользователей по логину/паролю
CREATE INDEX IF NOT EXISTS idx_users_login ON users(login);

-- Проверка созданных индексов
SHOW INDEX FROM promotions;
SHOW INDEX FROM informing;
SHOW INDEX FROM users;

-- Анализ производительности (опционально)
-- EXPLAIN SELECT ... - можно использовать для анализа планов выполнения запросов 