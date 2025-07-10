# Руководство по работе с Docker-контейнерами

### Команды для запуска проекта

```bash
sh start-project.sh
```

### Содержимое start-project.sh

```bash
# Сборка образа первой лабораторной
docker build . -t lab1 -f .\lab1\Dockerfile

# Сборка образа шлюза
docker build . -t gateway -f .\gateway\Dockerfile

# Поднятие контейнеров
docker compose up -d

# Старт проекта
python setup-project
```

---

### Команда для запуска py файлов

```bash
export PYTHONPATH=.
python ./lab1/app.py
```

---

### Базовые команды Docker

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
