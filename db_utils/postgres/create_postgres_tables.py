import psycopg2
from env import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER
from db_utils.postgres.tables import TABLES


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
        cur.execute("""
            CREATE OR REPLACE FUNCTION create_attendance_partition() RETURNS TRIGGER AS $$
            DECLARE
                partition_name TEXT;
                from_date DATE;
                to_date DATE;
            BEGIN
                -- Определяем диапазон дат для партиции (обычно на месяц)
                from_date := DATE_TRUNC('month', NEW.scheduled_date);
                to_date := from_date + INTERVAL '1 month';
                    
                partition_name := 'attendance_p_' || TO_CHAR(from_date, 'YYYY_MM');
                
                -- Создаем партицию, если она еще не существует
                IF NOT EXISTS (
                    SELECT 1 FROM pg_tables 
                    WHERE tablename = partition_name
                ) THEN
                    EXECUTE format(
                        'CREATE TABLE %I PARTITION OF Attendance ' ||
                        'FOR VALUES FROM (%L) TO (%L)',
                        partition_name, from_date, to_date
                    );
                    RAISE NOTICE 'Создана партиция: %', partition_name;
                END IF;
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;

            DROP TRIGGER IF EXISTS trig_create_attendance_partition ON Schedule;
            CREATE TRIGGER trig_create_attendance_partition
            AFTER INSERT ON Schedule
            FOR EACH ROW EXECUTE FUNCTION create_attendance_partition();
        """)
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
