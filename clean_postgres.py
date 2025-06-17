import psycopg2
from env import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

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
        cur.execute("DROP TABLE IF EXISTS Attendance CASCADE")
        cur.execute("DROP TABLE IF EXISTS Material_of_lecture CASCADE")
        cur.execute("DROP TABLE IF EXISTS Schedule CASCADE")
        cur.execute("DROP TABLE IF EXISTS Students CASCADE")
        cur.execute("DROP TABLE IF EXISTS Lecture CASCADE")
        cur.execute("DROP TABLE IF EXISTS Group_Courses CASCADE")
        cur.execute("DROP TABLE IF EXISTS Student_Groups CASCADE")
        cur.execute("DROP TABLE IF EXISTS Course_of_lecture CASCADE")
        cur.execute("DROP TABLE IF EXISTS Specialties CASCADE")
        cur.execute("DROP TABLE IF EXISTS Departments CASCADE")
        cur.execute("DROP TABLE IF EXISTS Institutes CASCADE")
        cur.execute("DROP TABLE IF EXISTS Universities CASCADE")

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