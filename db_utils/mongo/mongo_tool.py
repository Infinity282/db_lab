from pymongo import MongoClient
import logging
from env import (MONGO_URI, MONGO_DB_NAME, MONGO_USERNAME, MONGO_PASSWORD)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MongoTool:
    def __init__(self, host=MONGO_URI, username=MONGO_USERNAME, password=MONGO_PASSWORD):
        self.mongo_client = None
        self.db = None
        self.host = host
        self.username = username
        self.password = password

        self.connect()

    def connect(self):
        """Установка соединения с MongoDB"""
        try:
            self.mongo_client = MongoClient(
                host=self.host,
                username=self.username,
                password=self.password
            )

            self.mongo_client.server_info()
            self.db = self.mongo_client[MONGO_DB_NAME]

            logger.info("Успешное подключение к MongoDB")
            return True
        except Exception as e:
            logger.error(f"Ошибка подключения к MongoDB: {e}")
            return False

    def get_department_name_by_id(self, department_id: int) -> str | None:
        """
        Возвращает название кафедры по её ID

        :param department_id: ID кафедры
        :return: название кафедры или None если не найдена
        """
        try:
            if self.db is None:
                logger.error("Нет соединения с MongoDB")
                return None

            collection = self.db['universities']
            print(department_id)
            # Ищем кафедру по ID во всех университетах
            pipeline = [
                {'$unwind': '$institutes'},
                {'$unwind': '$institutes.departments'},
                {'$match': {'institutes.departments.department_id': department_id}},
                {'$project': {
                    'department_name': '$institutes.departments.name',
                    'institute_name': '$institutes.name',
                    'university_name': '$name'
                }}
            ]

            result = list(collection.aggregate(pipeline))

            if result:
                department_info = result[0]
                department_name = department_info['department_name']

                logger.info(
                    f"Найдена кафедра: {department_name} "
                    f"(ID: {department_id}), "
                    f"Институт: {department_info['institute_name']}, "
                    f"Университет: {department_info['university_name']}"
                )
                return department_name
            else:
                logger.warning(f"Кафедра с ID {department_id} не найдена")
                return None

        except Exception as e:
            logger.error(f"Ошибка при поиске кафедры по ID: {str(e)}")
            return None

    def close(self):
        """Закрытие соединения с MongoDB"""
        if self.mongo_client:
            self.mongo_client.close()
            logger.info("Соединение с MongoDB закрыто")

    def __del__(self):
        self.close()
