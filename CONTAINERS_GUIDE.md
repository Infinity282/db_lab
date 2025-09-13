# Руководство по работе с Docker-контейнерами

Это руководство предназначено для пользователей, работающих с системой, состоящей из нескольких Docker-контейнеров, включая базы данных (PostgreSQL, MongoDB, Neo4j, Elasticsearch, Redis), контейнер приложения (`lab1` и `lab2`) и шлюз (`gateway`). Здесь вы найдете команды для запуска проекта, управления контейнерами, подключения к базам данных, работы с API и советы по диагностике проблем.

---

## Содержание

1. [Запуск проекта](#запуск-проекта)
2. [Базовые команды Docker](#базовые-команды-docker)
3. [Контейнер PostgreSQL](#контейнер-postgresql)
4. [Контейнер MongoDB](#контейнер-mongodb)
5. [Контейнер Neo4j](#контейнер-neo4j)
6. [Контейнер Elasticsearch](#контейнер-elasticsearch)
7. [Контейнер Redis](#контейнер-redis)
8. [Контейнер приложения (lab1/lab2/lab3)](#контейнер-приложения)
9. [Работа с API через шлюз](#работа-с-api-через-шлюз)

---

## Запуск проекта

### Команды для запуска проекта

Для запуска проекта выполните следующую команду, которая вызывает скрипт `start-project.sh`:

```bash
sh start-project.sh
```

### Содержимое `start-project.sh`

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

### Запуск Python-файлов

Для запуска Python-приложения (например, `app.py` из `lab1`):

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

## Контейнер PostgreSQL

### Подключение к базе данных

```bash
docker exec -it postgres_container psql -U postgres_user -d postgres_db
```

- `postgres_container` — имя контейнера PostgreSQL.
- `postgres_user` — имя пользователя.
- `postgres_db` — имя базы данных.

### Основные команды PostgreSQL

- **Список таблиц**:
  ```sql
  \dt
  ```
- **Просмотр данных в таблице**:
  ```sql
  SELECT * FROM <table_name>;
  ```
- **Выход из psql**:
  ```sql
  \q
  ```

**Пример**:

```sql
SELECT * FROM course_of_classes LIMIT 5;
```

## Контейнер MongoDB

### Подключение к базе данных

```bash
docker exec -it db_lab-mongodb_1 mongosh "mongodb://admin:secret@localhost:27017/university_db?authSource=admin"
```

- `mongodb_container` — имя контейнера MongoDB.
- `admin:secret` — учетные данные.
- `university_db` — имя базы данных.

### Основные команды MongoDB

- **Список баз данных**:
  ```javascript
  show dbs;
  ```
- **Переключение на базу данных**:
  ```javascript
  use university_db;
  ```
- **Список коллекций**:
  ```javascript
  show collections;
  ```
- **Просмотр документов в коллекции**:
  ```javascript
  db.<collection_name>.find();
  ```

**Пример**:

```javascript
db.students.find().limit(5)
```

---

## Контейнер Neo4j

### Подключение к базе данных

```bash
docker exec -it neo4j_container cypher-shell -u neo4j -p neo4j_password
```

- `neo4j_container` — имя контейнера Neo4j.
- `neo4j:neo4j_password` — учетные данные.

### Основные команды Neo4j

- **Справка по командам**:
  ```cypher
  :help
  ```
- **Пример запроса**:
  ```cypher
  MATCH (n) RETURN n LIMIT 5;
  ```
- **Выход из cypher-shell**:
  ```cypher
  :exit
  ```

**Пример**:

```cypher
MATCH (c:Class)-[:FOR_CLASS]->(s:Schedule) RETURN c, s LIMIT 5;
```

---

## Контейнер Elasticsearch

### Подключение к базе данных

Проверка состояния кластера:

```bash
curl -X GET "http://localhost:9200/_cat/health?v"
```

### Основные команды Elasticsearch

- **Список индексов**:
  ```bash
  curl -X GET "http://localhost:9200/_cat/indices?v"
  ```
- **Поиск в индексе**:
  ```bash
  curl -X GET "http://localhost:9200/universities/_search"
  ```

**Пример**:

```bash
curl -X GET "http://localhost:9200/universities/_search" -H "Content-Type: application/json" -d '{"query": {"match_all": {}}}'
```

---

## Контейнер Redis

### Подключение к базе данных

```bash
docker exec -it redis_container redis-cli -a redis_password
```

- `redis_container` — имя контейнера Redis.
- `redis_password` — пароль.

### Основные команды Redis

- **Список ключей**:
  ```redis
  KEYS *
  ```
- **Получение значения по ключу**:
  ```redis
  GET key_name
  ```
- **Получение всех полей хэша**:
  ```redis
  HGETALL hash_key
  ```
- **Постраничное сканирование ключей**:
  ```redis
  SCAN 0
  ```

**Пример**:

```redis
GET course:1:students
```

---

## Контейнер приложения (lab1/lab2)

### Подключение к контейнеру

Для `lab1`:

```bash
docker exec -it lab1_container /bin/bash
```

Для `lab2`:

```bash
docker exec -it lab2_container /bin/bash
```

- `lab1_container`/`lab2_container` — имя контейнера приложения.

### Запуск приложения

Для `lab1`:

```bash
export PYTHONPATH=.
python ./lab1/app.py
```

---

## Работа с API через шлюз

### Получение токена авторизации

```bash
curl -X POST "http://gateway:1337/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "user"}'
```

### Экспорт токена

```bash
export TOKEN=<полученный_токен>
```

### Запрос к API

```bash
curl -X POST "http://gateway:1337/api/lab2/audience_report" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"year": 2022, "semester": 1}'
```

### Тестирование сетевых подключений

- **Проверка связи с gateway**:
  ```bash
  ping gateway
  ```
- **Проверка доступности API**:
  ```bash
  curl gateway:1337
  ```

---
