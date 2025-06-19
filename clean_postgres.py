import psycopg2
from env import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER, TABLES


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
        for table in TABLES:
            cur.execute(f"DROP TABLE IF EXISTS ${table} CASCADE")

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
