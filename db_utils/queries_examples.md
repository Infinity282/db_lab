### Развернутые примеры запросов для разных баз данных (простые, средние, сложные)

---

#### **PostgreSQL (SQL)**
**Простые:**
```sql
-- 1. Получить 5 университетов
SELECT id, name, founded_date FROM Universities LIMIT 5;

-- 2. Найти студентов 2023 года зачисления
SELECT name, book_number FROM Students WHERE enrollment_year = 2023 LIMIT 10;
```

**Средние:**
```sql
-- 1. Количество групп на кафедре
SELECT d.name, COUNT(g.id) AS group_count 
FROM Departments d
JOIN Student_Groups g ON d.id = g.department_id
GROUP BY d.name;

-- 2. Расписание группы на сегодня
SELECT c.name, s.room, s.start_time 
FROM Schedule s
JOIN Class c ON s.class_id = c.id
WHERE s.group_id = 101 AND s.scheduled_date = CURRENT_DATE;
```

**Сложные:**
```sql
-- 1. Статистика посещаемости по специальностям
SELECT sp.name, 
       AVG(CASE WHEN a.attended THEN 1 ELSE 0 END) AS attendance_rate
FROM Attendance a
JOIN Schedule sch ON a.schedule_id = sch.id
JOIN Class c ON sch.class_id = c.id
JOIN Course_of_classes cc ON c.course_of_class_id = cc.id
JOIN Specialties sp ON cc.specialty_id = sp.id
GROUP BY sp.name;

-- 2. Студенты с низкой посещаемостью (< 60%)
WITH AttendanceStats AS (
  SELECT s.id, 
         COUNT(*) AS total_classes,
         SUM(CASE WHEN a.attended THEN 1 ELSE 0 END) AS attended
  FROM Students s
  JOIN Attendance a ON s.id = a.student_id
  GROUP BY s.id
)
SELECT s.name, g.name AS group_name, 
       ROUND(attended::NUMERIC/total_classes*100, 1) AS rate
FROM AttendanceStats ast
JOIN Students s ON ast.id = s.id
JOIN Student_Groups g ON s.group_id = g.id
WHERE attended::NUMERIC/total_classes < 0.6;
```

---

#### **MongoDB**
**Простые:**
```javascript
// 1. Найти 3 института
db.Institutes.find({}, {name: 1}).limit(3)

// 2. Студенты с email в домене @edu.ru
db.Students.find(
  {email: /@edu\.ru$/}, 
  {name: 1, email: 1}
)
```

**Средние:**
```javascript
// 1. Группы с количеством студентов
db.Student_Groups.aggregate([
  {
    $lookup: {
      from: "Students",
      localField: "id",
      foreignField: "group_id",
      as: "students"
    }
  },
  {
    $project: {
      name: 1,
      student_count: {$size: "$students"}
    }
  }
])

// 2. Занятия лекционного типа
db.Class.aggregate([
  {$match: {type: "Lecture"}},
  {$lookup: {
      from: "Course_of_classes",
      localField: "course_of_class_id",
      foreignField: "id",
      as: "course"
  }},
  {$unwind: "$course"},
  {$project: {name: 1, "course.name": 1}}
])
```

**Сложные:**
```javascript
// 1. Средняя посещаемость по группам
db.Attendance.aggregate([
  {
    $lookup: {
      from: "Schedule",
      localField: "schedule_id",
      foreignField: "id",
      as: "schedule"
    }
  },
  {$unwind: "$schedule"},
  {
    $group: {
      _id: "$schedule.group_id",
      total: {$sum: 1},
      attended: {$sum: {$cond: [{$eq: ["$attended", true]}, 1, 0]}}
  },
  {
    $project: {
      attendance_rate: {$round: [{$multiply: [{$divide: ["$attended", "$total"]}, 100]}, 1]}
    }
  }
])

// 2. Поиск конфликтующих аудиторий
db.Schedule.aggregate([
  {
    $group: {
      _id: {
        room: "$room",
        date: "$scheduled_date"
      },
      slots: {$push: {start: "$start_time", end: "$end_time"}}
    }
  },
  {
    $project: {
      conflicts: {
        $filter: {
          input: "$slots",
          as: "slot",
          cond: {
            $gt: [
              {$size: {
                $filter: {
                  input: "$slots",
                  as: "other",
                  cond: {
                    $and: [
                      {$ne: ["$$slot", "$$other"]},
                      {$lt: ["$$slot.start", "$$other.end"]},
                      {$gt: ["$$slot.end", "$$other.start"]}
                    ]
                  }
                }
              }},
              0
            ]
          }
        }
      }
    }
  }
])
```

---

#### **Elasticsearch**
**Простые:**
```http
### 1. Поиск университетов по названию
GET /universities/_search
{
  "query": {
    "match": {
      "name": "технический"
    }
  }
}

### 2. Количество групп
GET /student_groups/_count
```

**Средние:**
```http
### 1. Расписание по аудитории
POST /schedule/_search
{
  "query": {
    "bool": {
      "must": [
        {"term": {"room.keyword": "А-101"}},
        {"range": {"scheduled_date": {"gte": "2023-09-01"}}}
      ]
    }
  },
  "size": 5
}

### 2. Анализ типов занятий
POST /class/_search
{
  "size": 0,
  "aggs": {
    "types_count": {
      "terms": {"field": "type.keyword"}
    }
  }
}
```

**Сложные:**
```http
### 1. Студенты с днями рождения на этой неделе
POST /students/_search
{
  "query": {
    "script": {
      "script": {
        "source": """
          def now = new Date();
          def bday = Date.fromString(doc['date_of_birth'].value);
          def thisYearBday = Date.of(now.getYear(), bday.getMonth(), bday.getDay());
          return thisYearBday >= now && thisYearBday < now.plusDays(7);
        """
      }
    }
  }
}

### 2. Полнотекстовый поиск материалов занятий
POST /class_materials/_search
{
  "query": {
    "multi_match": {
      "query": "базы данных SQL",
      "fields": ["content^2", "class.name"],
      "type": "most_fields"
    }
  },
  "highlight": {
    "fields": {"content": {}}
  }
}
```

---

#### **Neo4j (Cypher)**
**Простые:**
```cypher
// 1. Найти 5 кафедр
MATCH (d:Department) RETURN d.name LIMIT 5

// 2. Студенты группы "КТ-101"
MATCH (g:Group {name: "КТ-101"})<-[:BELONGS_TO]-(s:Student)
RETURN s.name, s.book_number
```

**Средние:**
```cypher
// 1. Иерархия: Университет → Институты
MATCH (u:University)-[:HAS]->(i:Institute)
RETURN u.name, COLLECT(i.name) AS institutes

// 2. Преподаватели кафедры (если есть связь)
MATCH (d:Department {name: "Информатика"})<-[:WORKS_IN]-(t:Teacher)
RETURN t.name, t.position
```

**Сложные:**
```cypher
// 1. Анализ учебной нагрузки
MATCH (g:Group)-[:HAS_SCHEDULE]->(s:Schedule)<-[:TEACHES]-(t:Teacher)
WITH t, COUNT(s) AS total_classes
RETURN t.name, total_classes
ORDER BY total_classes DESC
LIMIT 10

// 2. Поиск "общих" студентов между преподавателями
MATCH (t1:Teacher)-[:TEACHES]->()<-[:HAS_SCHEDULE]-(g:Group)<-[:BELONGS_TO]-(s:Student)-[:BELONGS_TO]->(g2:Group)<-[:HAS_SCHEDULE]-()<-[:TEACHES]-(t2:Teacher)
WHERE t1 <> t2
RETURN t1.name, t2.name, COUNT(DISTINCT s) AS common_students
ORDER BY common_students DESC
```

---

#### **Redis**
**Простые:**
```bash
# 1. Получить данные студента
HGETALL student:1843

# 2. Группы кафедры
SMEMBERS department:25:groups
```

**Средние:**
```bash
# 1. Ближайшие занятия группы
ZRANGEBYSCORE schedule:group:101 -inf +inf WITHSCORES LIMIT 0 5

# 2. Статистика посещаемости
HGET student:1843 attendance:stats
```

**Сложные:**
```bash
# 1. Поиск свободных аудиторий (Lua script)
EVAL "local slots = redis.call('ZRANGEBYSCORE', KEYS[1], ARGV[1], ARGV[2]) 
      local busy = {}
      for i, room in ipairs(slots) do 
          busy[room] = true 
      end
      local all_rooms = redis.call('SMEMBERS', 'rooms')
      local free = {}
      for j, room in ipairs(all_rooms) do 
          if not busy[room] then 
              table.insert(free, room) 
          end 
      end
      return free" 1 schedule:2023-10-15 09:00 11:00

# 2. Обновление посещаемости (pipeline)
MULTI
HINCRBY student:1843 attendance:total 1
HINCRBY student:1843 attendance:attended 1
EXPIRE student:1843 604800
EXEC
```

---

### Рекомендации для демонстрации:
1. **PostgreSQL** - Покажите JOIN'ы между 3+ таблицами
2. **MongoDB** - Демонстрируйте $lookup для связей и $expr для сложных условий
3. **Elasticsearch** - Используйте highlight и multi-field поиск
4. **Neo4j** - Визуализируйте связи между 4+ узлами
5. **Redis** - Покажите Lua-скрипты для атомарных операций

Пример сложного сценария для всех БД:  
*"Получить статистику посещаемости студентов 3 курса технических специальностей за последний месяц с расчетом рейтинга"*