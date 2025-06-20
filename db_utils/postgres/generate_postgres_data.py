import psycopg2
from db_utils.postgres.tables import TABLES
from db_utils.postgres.tables_data import UNIVERSITIES, INSTITUTES, DEPARTMENTS, SPECIALTIES, STUDENT_GROUPS, STUDENTS, COURSE_OF_CLASSES, CLASSES, CLASS_MATERIALS, SCHEDULE, ATTENDANCE
from db_utils.postgres.create_postgres_tables import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


def generate_insert_query(table_name, columns):
    """Генерация INSERT запроса на основе структуры таблицы"""
    # Убираем id из колонок, так как он SERIAL
    filtered_columns = [col for col in columns if col != 'id']
    placeholders = ', '.join(['%s'] * len(filtered_columns))
    columns_str = ', '.join(filtered_columns)

    return f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"


def parse_table_structure(table_def):
    """Парсинг структуры таблицы из SQL определения"""
    # Удаляем скобки и разбиваем на строки
    lines = table_def.strip()[1:-1].split(',')
    columns = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Берем первое слово как имя колонки
        column_name = line.split()[0]
        columns.append(column_name)

    return columns


def insert_data_from_dict(cur, table_name, data):
    """Вставка данных для конкретной таблицы"""
    print(f"Добавление данных в {table_name}")
    if table_name not in TABLES:
        print(f"Таблица {table_name} не найдена в определении TABLES")
        return

    # Получаем структуру таблицы
    table_def = TABLES[table_name]
    columns = parse_table_structure(table_def)

    # Генерируем и выполняем запросы
    query = generate_insert_query(table_name, columns)

    for row in data:
        cur.execute(query, row)


def insert_data():
    """Основная функция для заполнения БД"""
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()

    try:
        # Порядок вставки с учетом зависимостей
        tables_order = [
            ('Universities', UNIVERSITIES),
            ('Institutes', INSTITUTES),
            ('Departments', DEPARTMENTS),
            ('Specialties', SPECIALTIES),
            ('Student_Groups', STUDENT_GROUPS),
            ('Students', STUDENTS),
            ('Course_of_classes', COURSE_OF_CLASSES),
            ('Class', CLASSES),
            ('Class_Materials', CLASS_MATERIALS),
            ('Schedule', SCHEDULE),
            ('Attendance', ATTENDANCE)
        ]

        for table_name, data in tables_order:
            insert_data_from_dict(cur, table_name, data)

        conn.commit()
        print("Данные успешно добавлены в БД Postgres")

    except Exception as e:
        conn.rollback()
        print(f"Ошибка при добавлении данных: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    insert_data()
