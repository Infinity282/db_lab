import psycopg2
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from env import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER
from tables import TABLES


def check_tables():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()

    try:
        print("\n" + "="*50)
        print("ПРОВЕРКА ДАННЫХ В БАЗЕ ДАННЫХ")
        print("="*50 + "\n")

        for table in TABLES.keys():
            # Проверка существования таблицы
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_tables 
                    WHERE schemaname = 'public' AND tablename = %s
                )
            """, (table.lower(),))
            exists = cur.fetchone()[0]
            if not exists:
                print(f"\nТаблица: {table} - не существует")
                print("-"*50 + "\n")
                continue

            # Получаем количество записей
            cur.execute("SELECT COUNT(*) FROM %s", (psycopg2.extensions.AsIs(table),))
            count = cur.fetchone()[0]

            # Получаем информацию о колонках
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = %s
            """, (table.lower(),))
            columns = cur.fetchall()

            # Получаем имена колонок для читаемого вывода
            cur.execute("SELECT * FROM %s LIMIT 0", (psycopg2.extensions.AsIs(table),))
            col_names = [desc[0] for desc in cur.description]

            print(f"\nТаблица: {table} (записей: {count})")
            print("-"*50)
            print("Структура таблицы:")
            for col in columns:
                print(f"  {col[0]} ({col[1]})")

            if count > 0:
                # Получаем первые 3 записи
                cur.execute("SELECT * FROM %s LIMIT 3", (psycopg2.extensions.AsIs(table),))
                rows = cur.fetchall()

                print("\nПример данных:")
                for row in rows:
                    row_data = dict(zip(col_names, row))
                    print("  ", row_data)
            else:
                print("\nТаблица пуста")

            print("\n" + "="*50 + "\n")

    except Exception as e:
        print(f"Ошибка при проверке данных: {e}")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    check_tables()