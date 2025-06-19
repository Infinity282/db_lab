import psycopg2
from env import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER, TABLES


def check_database_data_simple():
    """Упрощенная версия без внешних зависимостей"""
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

        for table in TABLES:
            # Получаем количество записей
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]

            # Получаем информацию о колонках
            cur.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table.lower()}'
            """)
            columns = cur.fetchall()

            print(f"\nТаблица: {table} (записей: {count})")
            print("-"*50)
            print("Структура таблицы:")
            for col in columns:
                print(f"  {col[0]} ({col[1]})")

            if count > 0:
                # Получаем первые 3 записи
                cur.execute(f"SELECT * FROM {table} LIMIT 3")
                rows = cur.fetchall()

                print("\nПример данных:")
                for row in rows:
                    print("  ", row)
            else:
                print("\nТаблица пуста")

            print("\n" + "="*50 + "\n")

    except Exception as e:
        print(f"Ошибка при проверке данных: {e}")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    check_database_data_simple()
