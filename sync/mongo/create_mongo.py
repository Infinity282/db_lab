import psycopg2
from pymongo import MongoClient
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from env import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

def sync_university_hierarchy(mongo_uri='mongodb://localhost:27017/', db_name='university_db'):
    """
    Synchronize Universities, Institutes, and Departments from PostgreSQL to MongoDB in a hierarchical structure

    Args:
        mongo_uri (str): MongoDB connection URI
        db_name (str): Name of the MongoDB database
    """
    pg_conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    pg_cur = pg_conn.cursor()
    mongo_client = MongoClient(mongo_uri, username='admin', password='secret')
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
                'founded_date': {'bsonType': ['string', 'null']},  # Оставляем string для совместимости
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
        pg_cur.execute("SELECT university_id, name, address, founded_date FROM Universities")
        universities = pg_cur.fetchall()

        for uni_id, uni_name, uni_address, uni_founded in universities:
            pg_cur.execute("SELECT institute_id, name FROM Institutes WHERE university_id = %s", (uni_id,))
            institutes = pg_cur.fetchall()

            institutes_list = []
            for inst_id, inst_name in institutes:
                pg_cur.execute("SELECT department_id, name FROM Departments WHERE institute_id = %s", (inst_id,))
                departments = pg_cur.fetchall()

                departments_list = [{'department_id': dept_id, 'name': dept_name} for dept_id, dept_name in departments]

                institutes_list.append({
                    'institute_id': inst_id,
                    'name': inst_name,
                    'departments': departments_list
                })

            # Преобразуем datetime.date в строку или оставляем null
            founded_date = uni_founded.strftime('%Y-%m-%d') if uni_founded else None

            university_doc = {
                '_id': uni_id,
                'name': uni_name,
                'address': uni_address,
                'founded_date': founded_date,
                'institutes': institutes_list
            }
            universities_col.insert_one(university_doc)

        print(f"Successfully synchronized {len(universities)} universities to MongoDB")

    except Exception as e:
        print(f"Error during synchronization: {e}")
    finally:
        pg_cur.close()
        pg_conn.close()
        mongo_client.close()

def main():
    sync_university_hierarchy()

if __name__ == "__main__":
    main()