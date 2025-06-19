import psycopg2
from pymongo import MongoClient
# from env import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

DB_NAME = "postgres_db"
DB_USER = "postgres_user"
DB_PASSWORD = "postgres_password"
DB_HOST = "localhost"
DB_PORT = "5430"
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB_NAME = "university_db"
MONGO_USERNAME = "admin"
MONGO_PASSWORD = "secret"


def sync_university_hierarchy(mongo_uri=MONGO_URI, db_name=MONGO_DB_NAME):
    pg_conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

    pg_cur = pg_conn.cursor()

    mongo_client = MongoClient(
        mongo_uri,  username=MONGO_USERNAME, password=MONGO_PASSWORD)
    mongo_db = mongo_client[db_name]

    mongo_db.drop_collection('universities')
    mongo_db.create_collection('universities', validator={
        '$jsonSchema': {
            'bsonType': 'object',
            'required': ['_id', 'name', 'institutes'],
            'properties': {
                '_id': {'bsonType': 'int'},
                'name': {'bsonType': 'string'},
                'address': {'bsonType': ['string', 'null']},
                'founded_date': {'bsonType': ['string', 'null']},
                'institutes': {
                    'bsonType': 'array',
                    'items': {
                        'bsonType': 'object',
                        'required': ['institute_id', 'name', 'departments'],
                        'properties': {
                            'institute_id': {'bsonType': 'int'},
                            'name': {'bsonType': 'string'},
                            'departments': {
                                'bsonType': 'array',
                                'items': {
                                    'bsonType': 'object',
                                    'required': ['department_id', 'name'],
                                    'properties': {
                                        'department_id': {'bsonType': 'int'},
                                        'name': {'bsonType': 'string'}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    })

    universities_col = mongo_db['universities']

    try:
        pg_cur.execute(
            "SELECT id, name, address, founded_date FROM Universities")
        universities = pg_cur.fetchall()

        if not universities:
            print("Не найдено университетов")
            return

        for uni_id, uni_name, uni_address, uni_founded in universities:
            pg_cur.execute(
                "SELECT id, name FROM Institutes WHERE university_id = %s", (uni_id,))
            institutes = pg_cur.fetchall()

            institutes_list = []
            for inst_id, inst_name in institutes:
                pg_cur.execute(
                    "SELECT id, name FROM Departments WHERE institute_id = %s", (inst_id,))
                departments = pg_cur.fetchall()

                departments_list = [{'department_id': dept_id, 'name': dept_name}
                                    for dept_id, dept_name in departments]

                institutes_list.append({
                    'institute_id': inst_id,
                    'name': inst_name,
                    'departments': departments_list
                })

            founded_date = uni_founded.strftime(
                '%Y-%m-%d') if uni_founded else None

            university_doc = {
                '_id': uni_id,
                'name': uni_name,
                'address': uni_address if uni_address else None,
                'founded_date': founded_date,
                'institutes': institutes_list
            }
            universities_col.insert_one(university_doc)

        print(
            f"Успешно синхронизировано {len(universities)} universities в MongoDB")

    except Exception as e:
        print(f"Ошибка при синхронизации: {e}")
    finally:
        pg_cur.close()
        pg_conn.close()
        mongo_client.close()


def main():
    sync_university_hierarchy()


if __name__ == "__main__":
    main()
