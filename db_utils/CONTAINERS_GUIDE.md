# Руководство по работе с Docker-контейнерами

## Базовые команды Docker
```bash
# Запуск всех сервисов (из директории с docker-compose.yml)
docker-compose up -d

# Просмотр запущенных контейнеров
docker ps

# Остановка всех контейнеров
docker-compose down

# Просмотр логов конкретного контейнера
docker logs <container_name> -f
```

---

## 1. Контейнер PostgreSQL
**Подключение к БД:**
```bash
docker exec -it postgres_container psql -U postgres_user -d postgres_db
```

**Основные команды внутри PostgreSQL:**
```sql
\dt                  -- Список таблиц
SELECT * FROM table; -- Просмотр данных
\q                   -- Выход
```

---

## 2. Контейнер MongoDB
**Подключение к БД:**
```bash
docker exec -it mongodb_container mongosh "mongodb://admin:secret@localhost:27017/university_db?authSource=admin"
```

**Основные команды внутри MongoDB:**
```javascript
show dbs;             -- Список баз данных
use university_db;    -- Переключение на БД
show collections;     -- Список коллекций
db.collection.find(); -- Просмотр документов
```

---

## 3. Контейнер приложения (lab2)
**Подключение к контейнеру:**
```bash
docker exec -it lab2_container /bin/bash
```

**Проверка работы API:**
```bash
# 1. Получение токена авторизации
curl -X POST "http://gateway:1337/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"user"}'

# 2. Экспорт токена (подставить полученное значение)
export TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# 3. Пример вызова API
curl -X POST "http://gateway:1337/api/lab2/audience_report" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"year":2022,"semester":1}'
```

**Тестирование сетевых подключений:**
```bash
ping gateway      # Проверка связи с gateway
curl gateway:1337 # Проверка доступности API
```

---

## Советы
1. Имена контейнеров (`postgres_container`, `mongodb_container`, `lab2_container`) могут отличаться в вашей системе. Уточните через `docker ps`
2. Для копирования токена используйте `CTRL+SHIFT+C`/`CMD+C` в терминале
3. При проблемах с подключением проверьте статус контейнеров: `docker-compose ps`
4. Для выхода из интерактивного режима в терминале используйте `exit` или `CTRL+D`


## Особенности реализации:
1. **Универсальные имена контейнеров**  
   Используются общие имена (`postgres_container` и т.д.), которые нужно заменить на фактические из вашего `docker-compose.yml`

2. **Практические примеры**  
   Включены реальные команды из задачи + дополнительные полезные команды для диагностики

3. **Форматирование**  
   Четкое разделение на секции с подсветкой синтаксиса для разных оболочек (Bash, SQL, JS)

4. **Диагностика проблем**  
   Добавлены команды для проверки сети и подключений между контейнерами

5. **Безопасность**  
   Токен авторизации передается через переменную окружения (а не в plain-text)

Рекомендуется:
- Обновить имена контейнеров согласно вашему `docker-compose.yml`
- Проверить порты подключения (1337 в примере)
- При необходимости добавить учетные данные для других пользователей БД