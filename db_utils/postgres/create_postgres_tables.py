import psycopg2
from env import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER
from .tables import TABLES


def create_table(cur, table_name, definition):
    """Создает таблицу с обработкой ошибок"""
    try:
        cur.execute(f"CREATE TABLE IF NOT EXISTS {table_name} {definition}")
        print(f"Таблица {table_name} успешно создана")
    except Exception as e:
        print(f"Ошибка при создании таблицы {table_name}: {e}")
        raise


def create_tables():
    """Создает все таблицы в базе данных"""
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()

    try:
        for table_name, definition in TABLES.items():
            create_table(cur, table_name, definition)

        conn.commit()
        print("Все таблицы успешно созданы!")

    except Exception as e:
        conn.rollback()
        print(f"Ошибка при создании таблиц: {e}")

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    create_tables()
