import psycopg2
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from env import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER
from tables import TABLES


def drop_tables():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()

    try:
        for table_name in reversed(TABLES.keys()):
            cur.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
            print(f"Таблица {table_name} удалена")
        conn.commit()
        print("Все таблицы успешно удалены!")

    except Exception as e:
        conn.rollback()
        print(f"Ошибка при удалении таблиц: {e}")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    drop_tables()
