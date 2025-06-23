# Руководство по работе с Docker-контейнерами

Это руководство предназначено для пользователей, работающих с системой, состоящей из нескольких Docker-контейнеров, включая базы данных (PostgreSQL, MongoDB, Neo4j, Elasticsearch, Redis) и контейнер приложения (`lab2`). Здесь вы найдете команды для управления контейнерами, подключения к базам данных, работы с API и советы по диагностике проблем.

---

## Содержание

1. [Базовые команды Docker](#базовые-команды-docker)  
2. [Контейнер PostgreSQL](#1-контейнер-postgresql)  
3. [Контейнер MongoDB](#2-контейнер-mongodb)  
4. [Контейнер Neo4j](#3-контейнер-neo4j)  
5. [Контейнер Elasticsearch](#4-контейнер-elasticsearch)  
6. [Контейнер Redis](#5-контейнер-redis)  
7. [Контейнер приложения (lab2)](#6-контейнер-приложения-lab2)  
8. [Советы по работе с контейнерами](#советы-по-работе-с-контейнерами)  
9. [Особенности реализации](#особенности-реализации)  

---

## Базовые команды Docker

Ниже приведены основные команды для управления контейнерами с помощью `docker-compose`:

- **Запуск всех сервисов** (в фоновом режиме):  
  ```bash
  docker-compose up -d
  ```
- **Остановка всех сервисов**:  
  ```bash
  docker-compose down
  ```
- **Просмотр логов контейнера** (в режиме реального времени):  
  ```bash
  docker logs <container_name> -f
  ```

**Примечание**: Замените `<container_name>` на имя контейнера, например, `postgres_container` или `lab2_container`.

---

## 1. Контейнер PostgreSQL

### Подключение к базе данных
Для подключения к PostgreSQL выполните:  
```bash
docker exec -it postgres_container psql -U postgres_user -d postgres_db
```
- `postgres_container` — имя контейнера PostgreSQL.  
- `postgres_user` — имя пользователя.  
- `postgres_db` — имя базы данных.

### Основные команды PostgreSQL
После подключения используйте:  
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

---

## 2. Контейнер MongoDB

### Подключение к базе данных
Для подключения к MongoDB выполните:  
```bash
docker exec -it mongodb_container mongosh "mongodb://admin:secret@localhost:27017/university_db?authSource=admin"
```
- `mongodb_container` — имя контейнера MongoDB.  
- `admin:secret` — учетные данные для аутентификации.  
- `university_db` — имя базы данных.

### Основные команды MongoDB
После подключения используйте:  
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
db.students.find().limit(5);
```

---

## 3. Контейнер Neo4j

### Подключение к базе данных
Для подключения к Neo4j выполните:  
```bash
docker exec -it neo4j_container cypher-shell -u neo4j -p neo4j_password
```
- `neo4j_container` — имя контейнера Neo4j.  
- `neo4j:neo4j_password` — учетные данные для аутентификации.

### Основные команды Neo4j
После подключения используйте:  
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

## 4. Контейнер Elasticsearch

### Подключение к базе данных
Для проверки состояния кластера Elasticsearch выполните:  
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

## 5. Контейнер Redis

### Подключение к базе данных
Для подключения к Redis выполните:  
```bash
docker exec -it redis_container redis-cli -a redis_password
```
- `redis_container` — имя контейнера Redis.  
- `redis_password` — пароль для аутентификации.

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

## 6. Контейнер приложения (lab2)

### Подключение к контейнеру
Для доступа к контейнеру приложения выполните:  
```bash
docker exec -it lab2_container /bin/bash
```
- `lab2_container` — имя контейнера приложения.

### Проверка работы API
1. **Получение токена авторизации**:  
   ```bash
   curl -X POST "http://gateway:1337/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "user", "password": "user"}'
   ```
2. **Экспорт токена**:  
   ```bash
   export TOKEN=<полученный_токен>
   ```
3. **Запрос к API**:  
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

## Советы по работе с контейнерами

1. **Имена контейнеров**: Уточните имена контейнеров в вашей системе с помощью `docker ps`, так как они могут отличаться от указанных в руководстве.  
2. **Копирование токена**: Для копирования токена в терминале используйте `CTRL+SHIFT+C` (Windows/Linux) или `CMD+C` (Mac).  
3. **Проверка статуса контейнеров**: При проблемах с подключением выполните `docker-compose ps`.  
4. **Выход из интерактивного режима**: Для выхода из оболочки контейнера или базы данных используйте `exit` или `CTRL+D`.

---

## Особенности реализации

- **Универсальные имена контейнеров**: Используются общие имена (`postgres_container`, `mongodb_container` и т.д.). Замените их на фактические из вашего `docker-compose.yml`.  
- **Практические примеры**: Включены команды из задачи и дополнительные команды для диагностики.  
- **Форматирование**: Используется подсветка синтаксиса для различных оболочек (Bash, SQL, JS, Cypher, Redis).  
- **Диагностика проблем**: Добавлены команды для проверки сети и подключений между контейнерами.  
- **Безопасность**: Токен авторизации передается через переменную окружения для предотвращения утечек.

### Рекомендации
- Обновите имена контейнеров в командах, если они отличаются от указанных.  
- Проверьте порты подключения (например, порт 1337 для API).  
- При необходимости добавьте учетные данные для других пользователей баз данных.

---

Это руководство поможет вам эффективно работать с Docker-контейнерами в рамках вашего проекта. Если возникнут вопросы или проблемы, обратитесь к разделу [Советы по работе с контейнерами](#советы-по-работе-с-контейнерами) или проверьте логи контейнеров.