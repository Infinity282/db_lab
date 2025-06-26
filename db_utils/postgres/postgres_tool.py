# Импорт библиотеки для работы с PostgreSQL
import psycopg2
# Импорт модуля логирования для отслеживания событий и ошибок
import logging
# Импорт типа date для работы с датами
from datetime import date
# Импорт переменных окружения из файла env.py для конфигурации подключения к базе данных
from env import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

# Настройка базовой конфигурации логирования
logging.basicConfig(
    level=logging.INFO,  # Уровень логирования: INFO (информация о ходе выполнения)
    format='%(asctime)s - %(levelname)s - %(message)s'  # Формат сообщений: время, уровень, текст
)
# Создание объекта логгера с именем текущего модуля
logger = logging.getLogger(__name__)

# Определение класса для взаимодействия с PostgreSQL
class PostgresTool:
    """
    Класс для работы с базой данных PostgreSQL.
    Содержит методы для подключения и выполнения запросов, необходимых для Лабораторных работ №1 и №2.
    """

    def __init__(self, host=DB_HOST):
        """
        Инициализация объекта PostgresTool.
        :param host: Адрес хоста базы данных (по умолчанию берется из env.py).
        """
        self.conn = None  # Переменная для хранения объекта подключения (изначально None)
        self.host = host  # Сохранение хоста базы данных
        self.connect()    # Вызов метода подключения при создании объекта

    def connect(self):
        """
        Устанавливает соединение с базой данных PostgreSQL с использованием параметров из env.py.
        """
        try:
            # Создание соединения с базой данных через psycopg2
            self.conn = psycopg2.connect(
                dbname=DB_NAME,      # Имя базы данных из env.py
                user=DB_USER,        # Имя пользователя из env.py
                password=DB_PASSWORD,  # Пароль из env.py
                host=self.host,      # Хост из параметра или env.py
                port=DB_PORT         # Порт из env.py
            )
            logger.info("Connected to PostgreSQL")  # Логирование успешного подключения
        except Exception as e:
            # Логирование ошибки подключения и повторное возбуждение исключения
            logger.error(f"PostgreSQL connection error: {str(e)}")
            raise

    def get_courses_lectures(self, start_date: date, end_date: date) -> list:
        """
        Метод для Лабораторной работы №2: Получение списка курсов и их лекций за указанный период.
        :param start_date: Начальная дата периода (тип date).
        :param end_date: Конечная дата периода (тип date).
        :return: Список словарей с информацией о курсах и лекциях.
        """
        try:
            # Создание курсора для выполнения SQL-запроса в контексте менеджера with
            with self.conn.cursor() as cur:
                # SQL-запрос для выборки данных о курсах и лекциях
                query = """
                SELECT
                    c.id AS course_id,              -- ID курса
                    c.name AS course_name,          -- Название курса
                    cl.id AS lecture_id,            -- ID лекции
                    cl.name AS topic,               -- Тема лекции
                    s.scheduled_date AS date,       -- Дата лекции
                    s.start_time,                   -- Время начала лекции
                    s.end_time,                     -- Время окончания лекции
                    cl.tech_requirements            -- Технические требования к лекции
                FROM course_of_classes c            -- Таблица курсов
                JOIN class cl ON c.id = cl.course_of_class_id  -- Связь с таблицей занятий
                JOIN schedule s ON cl.id = s.class_id          -- Связь с таблицей расписания
                WHERE
                    cl.type = 'лекция'              -- Фильтр: только лекции
                    AND s.scheduled_date >= %s      -- Дата >= начальной даты
                    AND s.scheduled_date <= %s      -- Дата <= конечной даты
                ORDER BY c.id, s.scheduled_date, s.start_time  -- Сортировка по ID курса, дате и времени
                """
                # Выполнение запроса с передачей параметров (start_date, end_date)
                cur.execute(query, (start_date, end_date))
                # Получение названий столбцов из описания курсора
                columns = [desc[0] for desc in cur.description]
                # Преобразование результатов в список словарей, где ключи — названия столбцов
                results = [dict(zip(columns, row)) for row in cur.fetchall()]
                # Логирование количества полученных записей
                logger.info(f"Fetched {len(results)} courses and lectures")
                return results  # Возврат списка результатов
        except Exception as e:
            # Логирование ошибки и возврат пустого списка в случае сбоя
            logger.error(f"Error fetching courses and lectures: {str(e)}")
            return []

    def get_student_count(self, course_id: int) -> int:
        """
        Метод для Лабораторной работы №2: Подсчет количества студентов на курсе.
        :param course_id: ID курса (целое число).
        :return: Количество студентов (целое число).
        """
        try:
            with self.conn.cursor() as cur:
                # SQL-запрос для подсчета уникальных студентов на курсе
                query = """
                SELECT COUNT(DISTINCT s.id)          -- Подсчет уникальных ID студентов
                FROM students s                      -- Таблица студентов
                JOIN student_groups g ON s.group_id = g.id  -- Связь с таблицей групп
                JOIN schedule sch ON g.id = sch.group_id    -- Связь с расписанием
                JOIN class cl ON sch.class_id = cl.id       -- Связь с занятиями
                WHERE cl.course_of_class_id = %s     -- Фильтр по ID курса
                """
                # Выполнение запроса с параметром course_id
                cur.execute(query, (course_id,))
                # Получение результата (первое значение первой строки)
                count = cur.fetchone()[0]
                # Логирование полученного количества студентов
                logger.info(f"Student count for course {course_id}: {count}")
                return count  # Возврат количества студентов
        except Exception as e:
            # Логирование ошибки и возврат 0 в случае сбоя
            logger.error(f"Error fetching student count: {str(e)}")
            return 0

    def get_course_lectures(self, course_id: int, semester: int, year: int, term: str = None) -> list:
        """
        Метод для Лабораторной работы №1: Получение лекций курса с возможной фильтрацией по термину.
        :param course_id: ID курса (целое число).
        :param semester: Номер семестра (целое число).
        :param year: Год (целое число).
        :param term: Строка для фильтрации тем лекций (опционально).
        :return: Список словарей с данными о лекциях.
        """
        try:
            with self.conn.cursor() as cur:
                # Базовый SQL-запрос для получения лекций курса
                query = """
                SELECT
                    c.id AS course_id,              -- ID курса
                    c.name AS course_name,          -- Название курса
                    cl.id AS lecture_id,            -- ID лекции
                    cl.name AS topic,               -- Тема лекции
                    s.scheduled_date AS date,       -- Дата лекции
                    s.start_time AS duration        -- Время начала (используется как продолжительность)
                FROM course_of_classes c            -- Таблица курсов
                JOIN class cl ON c.id = cl.course_of_class_id  -- Связь с таблицей занятий
                JOIN schedule s ON cl.id = s.class_id          -- Связь с таблицей расписания
                WHERE
                    c.id = %s                       -- Фильтр по ID курса
                    AND c.semester = %s             -- Фильтр по семестру
                    AND EXTRACT(YEAR FROM s.scheduled_date) = %s  -- Фильтр по году
                    AND cl.type = 'лекция'          -- Фильтр: только лекции
                """
                params = [course_id, semester, year]  # Параметры для базового запроса
                if term:
                    # Добавление фильтра по термину (чувствительность к регистру игнорируется через ILIKE)
                    query += " AND cl.name ILIKE %s"
                    params.append(f"%{term}%")  # Добавление термина с подстановкой % для поиска подстроки
                
                # Выполнение запроса с параметрами
                cur.execute(query, tuple(params))
                # Получение названий столбцов
                columns = [desc[0] for desc in cur.description]
                # Преобразование результатов в список словарей
                results = [dict(zip(columns, row)) for row in cur.fetchall()]
                # Логирование количества полученных лекций
                logger.info(f"Fetched {len(results)} lectures for course {course_id}")
                return results  # Возврат списка лекций
        except Exception as e:
            # Логирование ошибки и возврат пустого списка в случае сбоя
            logger.error(f"Error fetching course lectures: {str(e)}")
            return []

    def get_students_with_lowest_attendance(self, schedule_ids: list, start_date: date, end_date: date, term: str = None, limit: int = 10) -> list:
        """
        Метод для Лабораторной работы №1: Получение студентов с минимальной посещаемостью.
        :param schedule_ids: Список ID расписаний (список целых чисел).
        :param start_date: Начальная дата периода (тип date).
        :param end_date: Конечная дата периода (тип date).
        :param term: Строка для фильтрации по теме лекций (опционально).
        :param limit: Максимальное количество студентов в результате (по умолчанию 10).
        :return: Список словарей с данными о студентах и их посещаемости.
        """
        try:
            with self.conn.cursor() as cur:
                # SQL-запрос для анализа посещаемости студентов
                query = """
                SELECT
                    s.id AS student_id,             -- ID студента
                    s.name AS student_name,         -- Имя студента
                    s.email AS student_email,       -- Email студента
                    s.enrollment_year,              -- Год зачисления
                    s.date_of_birth,                -- Дата рождения
                    SUM(CASE WHEN a.attended = FALSE THEN 1 ELSE 0 END) AS missed_count,  -- Количество пропусков
                    COUNT(a.schedule_id) AS total_lectures  -- Общее количество лекций
                FROM students s                     -- Таблица студентов
                JOIN attendance a ON s.id = a.student_id  -- Связь с таблицей посещаемости
                JOIN schedule sch ON a.schedule_id = sch.id  -- Связь с расписанием
                JOIN class cl ON sch.class_id = cl.id        -- Связь с занятиями
                WHERE
                    a.schedule_id = ANY(%s)         -- Фильтр по списку ID расписаний
                    AND sch.scheduled_date >= %s    -- Дата >= начальной даты
                    AND sch.scheduled_date <= %s    -- Дата <= конечной даты
                """
                params = [schedule_ids, start_date, end_date]  # Базовые параметры запроса
                if term:
                    # Добавление фильтра по термину в теме лекции
                    query += " AND cl.name ILIKE %s"
                    params.append(f"%{term}%")  # Подстановка термина с % для поиска подстроки
                
                # Группировка, сортировка и ограничение результата
                query += """
                GROUP BY s.id, s.name, s.email, s.enrollment_year, s.date_of_birth
                ORDER BY missed_count DESC          -- Сортировка по убыванию пропусков
                LIMIT %s                            -- Ограничение количества записей
                """
                params.append(limit)  # Добавление лимита в параметры
                
                # Выполнение запроса
                cur.execute(query, tuple(params))
                results = []  # Список для хранения результатов
                # Обработка каждой строки результата
                for row in cur.fetchall():
                    student_id, student_name, student_email, enrollment_year, date_of_birth, missed_count, total_lectures = row
                    # Расчет процента посещаемости
                    attendance_percent = round(
                        ((total_lectures - missed_count) / total_lectures) * 100, 2
                    ) if total_lectures > 0 else 0.0
                    # Формирование словаря с данными о студенте
                    student_data = {
                        'student_id': student_id,
                        'student_name': student_name,
                        'student_email': student_email,
                        'enrollment_year': enrollment_year,
                        'date_of_birth': str(date_of_birth),  # Преобразование даты в строку
                        'missed_count': missed_count,
                        'total_lectures': total_lectures,
                        'attendance_percent': attendance_percent
                    }
                    results.append(student_data)  # Добавление данных в список
                    # Логирование информации о студенте
                    logger.info(
                        f"Student (ID: {student_id}): "
                        f"missed {missed_count} of {total_lectures} lectures "
                        f"({attendance_percent}% attendance)"
                    )
                # Логирование общего количества найденных студентов
                logger.info(f"Found {len(results)} students with low attendance")
                return results  # Возврат списка студентов
        except Exception as e:
            # Логирование ошибки и возврат пустого списка в случае сбоя
            logger.error(f"Error analyzing attendance: {str(e)}")
            return []

    def close(self):
        """
        Закрытие соединения с базой данных.
        """
        if self.conn:  # Проверка, существует ли соединение
            self.conn.close()  # Закрытие соединения
            logger.info("PostgreSQL connection closed")  # Логирование закрытия

    def __del__(self):
        """
        Деструктор: автоматически закрывает соединение при удалении объекта.
        """
        self.close()  # Вызов метода закрытия соединения

# Тестовый код для проверки функциональности
if __name__ == "__main__":
    from datetime import datetime  # Импорт datetime для создания тестовых дат
    tool = PostgresTool()  # Создание объекта PostgresTool
    try:
        # Тест метода для Лабораторной работы №2
        start_date = datetime.strptime("2023-09-01", "%Y-%m-%d").date()  # Начальная дата
        end_date = datetime.strptime("2023-12-31", "%Y-%m-%d").date()    # Конечная дата
        courses_lectures = tool.get_courses_lectures(start_date, end_date)  # Получение лекций
        print(f"Лабораторная №2: Получено {len(courses_lectures)} лекций")  # Вывод результата

        # Тест методов для Лабораторной работы №1
        course_lectures = tool.get_course_lectures(course_id=1, semester=1, year=2023, term="кинематика")  # Получение лекций курса
        schedule_ids = [1, 2, 3]  # Пример списка ID расписаний
        students = tool.get_students_with_lowest_attendance(
            schedule_ids=schedule_ids,
            start_date=start_date,
            end_date=end_date,
            term="кинематика",
            limit=10
        )  # Получение студентов с низкой посещаемостью
        print(f"Лабораторная №1: Найдено {len(students)} студентов с низкой посещаемостью")  # Вывод результата
    finally:
        tool.close()  # Закрытие соединения в любом случае