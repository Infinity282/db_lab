import psycopg2
from pymongo import MongoClient
from contextlib import closing
from datetime import datetime
import logging
from env import (DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT,
                 DB_USER, MONGO_URI, MONGO_DB_NAME, MONGO_USERNAME, MONGO_PASSWORD)
from db_utils.mongo.table_schema import UNIVERSITY_SCHEMA

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MongoSynchronizer:
    def __init__(self) -> None:
        self.pg_conn = None
        self.mongo_client = None
        self.university_data = None
        self.stats = {
            'universities': 0,
            'institutes': 0,
            'departments': 0,
            'start_time': None
        }

        self.connect_postgres()
        self.connect_mongodb()

    def connect_postgres(self) -> bool:
        """Установка соединения с PostgreSQL"""
        try:
            self.pg_conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT
            )
            logger.info("Успешное подключение к PostgreSQL")
            return True
        except psycopg2.Error as e:
            logger.error(f"Ошибка подключения к PostgreSQL: {e}")
            return False

    def connect_mongodb(self) -> bool:
        """Установка соединения с MongoDB"""
        try:
            self.mongo_client = MongoClient(
                host=MONGO_URI,
                username=MONGO_USERNAME,
                password=MONGO_PASSWORD
            )

            self.mongo_client.server_info()
            logger.info("Успешное подключение к MongoDB")
            return True
        except Exception as e:
            logger.error(f"Ошибка подключения к MongoDB: {e}")
            return False

    def close_connections(self) -> None:
        if self.pg_conn:
            self.pg_conn.close()
            logger.info("Соединение с PostgreSQL закрыто")
        if self.mongo_client:
            self.mongo_client.close()
            logger.info("Соединение с Redis закрыто")

    def fetch_hierarchy_data(self) -> bool:
        """Получение иерархических данных из PostgreSQL с валидацией"""
        logger.info("Извлечение иерархических данных университетов")
        self.university_data = []

        with closing(self.pg_conn.cursor()) as pg_cur:
            pg_cur.execute(
                "SELECT id, name, address, founded_date FROM Universities")
            universities = pg_cur.fetchall()
            self.stats['universities'] = len(universities)

            if not universities:
                logger.warning("Не найдено университетов")
                return False

            university_map = {}
            for row in universities:
                university_id = row[0]
                university_name = row[1]
                university_address = row[2]
                university_founded_date = row[3]

                university_map[university_id] = {
                    'id': university_id,
                    'name': university_name,
                    'address': university_address,
                    'founded_date': university_founded_date,
                    'institutes': {}
                }

            pg_cur.execute("SELECT id, university_id, name FROM Institutes")
            institutes = pg_cur.fetchall()
            self.stats['institutes'] = len(institutes)

            institute_map = {}
            for inst_id, uni_id, name in institutes:
                if uni_id not in university_map:
                    logger.warning(
                        f"Институт {inst_id} ссылается на несуществующий университет {uni_id}")
                    continue

                institute_map[inst_id] = {
                    'name': name,
                    'university_id': uni_id,
                    'departments': []
                }
                university_map[uni_id]['institutes'][inst_id] = institute_map[inst_id]

            pg_cur.execute("SELECT id, institute_id, name FROM Departments")
            departments = pg_cur.fetchall()
            self.stats['departments'] = len(departments)

            for dept_id, inst_id, name in departments:
                if inst_id not in institute_map:
                    logger.warning(
                        f"Кафедра {dept_id} ссылается на несуществующий институт {inst_id}")
                    continue

                institute_map[inst_id]['departments'].append({
                    'department_id': dept_id,
                    'name': name
                })

            for uni_id, data in university_map.items():
                institutes_list = []
                for inst_id, inst_data in data['institutes'].items():
                    institutes_list.append({
                        'institute_id': inst_id,
                        'name': inst_data['name'],
                        'departments': inst_data['departments']
                    })

                self.university_data.append({
                    '_id': uni_id,
                    'name': data['name'],
                    'address': data['address'],
                    'founded_date': data['founded_date'].strftime('%Y-%m-%d') if data['founded_date'] else None,
                    'institutes': institutes_list
                })

            logger.info("Данные успешно подготовлены для MongoDB")
            return True

    def sync_to_mongodb(self) -> bool:
        """Синхронизация данных в MongoDB"""
        if not self.university_data:
            logger.error("Нет данных для синхронизации")
            return False

        try:
            db = self.mongo_client[MONGO_DB_NAME]

            if 'universities' in db.list_collection_names():
                db['universities'].drop()

            db.create_collection(
                'universities', validator=UNIVERSITY_SCHEMA)
            collection = db['universities']

            result = collection.insert_many(self.university_data)
            inserted_count = len(result.inserted_ids)

            mongo_count = collection.count_documents({})
            if mongo_count != inserted_count:
                logger.error(f"Несоответствие данных: вставлено {inserted_count}, "
                             f"но найдено {mongo_count} документов")
                return False

            logger.info(f"Успешно синхронизировано {inserted_count} университетов "
                        f"с {self.stats['institutes']} институтами "
                        f"и {self.stats['departments']} кафедрами")
            return True
        except Exception as e:
            logger.exception(f"Ошибка при синхронизации с MongoDB: {e}")
            return False

    def run_sync(self) -> bool:
        """Основной метод выполнения синхронизации"""
        self.stats['start_time'] = datetime.now()
        logger.info("Начало синхронизации университетской иерархии")

        try:
            if not self.pg_conn:
                return False
            if not self.mongo_client:
                return False
            if not self.fetch_hierarchy_data():
                return False
            if not self.sync_to_mongodb():
                return False

            duration = (datetime.now() -
                        self.stats['start_time']).total_seconds()
            logger.info(
                f"Синхронизация успешно завершена за {duration:.2f} секунд")
            return True
        except Exception as e:
            logger.exception(f"Критическая ошибка при синхронизации: {e}")
            return False
        finally:
            self.close_connections()


if __name__ == "__main__":
    mongo_synchronizer = MongoSynchronizer()
    success = mongo_synchronizer.run_sync()
