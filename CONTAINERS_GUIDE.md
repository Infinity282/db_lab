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
8. [Контейнер приложения (lab1/lab2)](#контейнер-приложения)  
9. [Работа с API через шлюз](#работа-с-api-через-шлюз)  
10. [Советы по работе с контейнерами](#советы-по-работе-с-контейнерами)  
11. [Особенности реализации](#особенности-реализации)  

---

## Запуск проекта

### Команды для запуска проекта
Для запуска проекта выполните следующую команду, которая вызывает скрипт `start-project.sh`:

```bash
sh start-project.sh
```

### Содержимое `start-project.sh`
Скрипт выполняет сборку образов и запуск контейнеров:

```bash
# Сборка образа первой лабораторной
docker build . -t lab1 -f ./lab1/Dockerfile

# Сборка образа шлюза
docker build . -t gateway -f ./gateway/Dockerfile

# Поднятие контейнеров
docker compose up -d

# Старт проекта
python setup-project
```

### Запуск Python-файлов
Для запуска Python-приложения (например, `app.py` из `lab1`):

```bash
export PYTHONPATH=.
python ./lab1/app.py
```

---

## Базовые команды Docker

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
  Замените `<container_name>` на имя контейнера, например, `postgres_container`, `lab1_container`, `lab2_container` или `gateway`.

- **Просмотр запущенных контейнеров**:  
  ```bash
  docker ps
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

---

## Контейнер MongoDB

### Подключение к базе данных
```bash
docker exec -it mongodb_container mongosh "mongodb://admin:secret@localhost:27017/university_db?authSource=admin"
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
db.students.find().limit(5);
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

## Советы по работе с контейнерами

1. **Проверка имен контейнеров**: Используйте `docker ps` для уточнения имен контейнеров, так как они могут отличаться от указанных.  
2. **Копирование токена**: Используйте `CTRL+SHIFT+C` (Windows/Linux) или `CMD+C` (Mac) для копирования токена в терминале.  
3. **Проверка статуса контейнеров**: При проблемах выполните `docker-compose ps`.  
4. **Логи**: Проверяйте логи контейнеров с помощью `docker logs <container_name> -f` для диагностики ошибок.  
5. **Выход из оболочки**: Используйте `exit` или `CTRL+D` для выхода из интерактивного режима контейнера или базы данных.  
6. **Перезапуск контейнеров**: Если контейнер не отвечает, попробуйте перезапустить:  
   ```bash
   docker-compose restart <container_name>
   ```

---

## Особенности реализации

- **Универсальные имена**: Имена контейнеров (`postgres_container`, `mongodb_container` и т.д.) являются общими. Замените их на фактические из вашего `docker-compose.yml`.  
- **Практические примеры**: Включены команды для запуска проекта, работы с базами данных и API, а также диагностики.  
- **Форматирование**: Используется подсветка синтаксиса для различных оболочек (Bash, SQL, JS, Cypher, Redis).  
- **Безопасность**: Токен авторизации передается через переменную окружения для предотвращения утечек.  
- **Диагностика**: Добавлены команды для проверки сети и подключений между контейнерами.  

### Рекомендации
- Проверьте имена контейнеров и порты в вашем `docker-compose.yml`.  
- Убедитесь, что порты (например, 1337 для API) открыты и не конфликтуют.  
- Обновите учетные данные (имя пользователя, пароль) для баз данных, если они отличаются.  
- При необходимости добавьте дополнительные команды для диагностики в зависимости от вашей конфигурации.
