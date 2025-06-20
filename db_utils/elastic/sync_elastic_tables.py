from elasticsearch import Elasticsearch
import psycopg2
import logging
from contextlib import closing
from datetime import datetime
from env import (DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT,
                 DB_USER, ES_HOST, ES_PORT, ES_USER, ES_PASSWORD)
from db_utils.elastic.const import SETTINGS, INDEX_NAME, MAPPINGS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ElasticLectureSessionSynchronizer:
    def __init__(self):
        self.pg_conn = None
        self.es_client = None
        self.stats = {
            'total_sessions': 0,
            'successful': 0,
            'failed': 0,
            'start_time': None
        }
        self.connect_postgres()
        self.connect_elasticsearch()

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

    def connect_elasticsearch(self) -> bool:
        """Установка соединения с Elasticsearch"""
        try:
            self.es_client = Elasticsearch(
                hosts=[f"http://{ES_HOST}:{ES_PORT}"],
                basic_auth=(ES_USER, ES_PASSWORD),
                verify_certs=False
            )
            if self.es_client.ping():
                logger.info("Успешное подключение к Elasticsearch")
                return True
            logger.error("Не удалось подключиться к Elasticsearch")
            return False
        except Exception as e:
            logger.error(f"Ошибка подключения к Elasticsearch: {e}")
            return False

    def close_connections(self) -> None:
        """Закрытие всех соединений"""
        if self.pg_conn:
            self.pg_conn.close()
            logger.info("Соединение с PostgreSQL закрыто")
        if self.es_client:
            self.es_client.close()
            logger.info("Соединение с Elasticsearch закрыто")

    def ensure_index_exists(self) -> bool:
        """Создание индекса, если он не существует"""
        try:
            if not self.es_client.indices.exists(index=INDEX_NAME):
                self.es_client.indices.create(
                    index=INDEX_NAME,
                    settings=SETTINGS,
                    mappings=MAPPINGS
                )
                logger.info(f"Создан новый индекс: {INDEX_NAME}")
            else:
                logger.info(
                    f"Используется существующий индекс: {INDEX_NAME}")
            return True
        except Exception as e:
            logger.error(f"Ошибка создания индекса: {e}")
            return False

    def fetch_materials_data(self) -> list:
        """Получение данных материалов из PostgreSQL"""
        logger.info("Извлечение данных материалов занятий из PostgreSQL")

        try:
            with closing(self.pg_conn.cursor()) as cursor:
                cursor.execute("""
                    SELECT cm.id, cm.class_id, cm.content
                    FROM Class_Materials cm
                """)
                materials = cursor.fetchall()
                self.stats['total_materials'] = len(materials)
                logger.info(f"Получено {len(materials)} материалов занятий")
                print(materials)
                return materials
        except psycopg2.Error as e:
            logger.error(f"Ошибка получения данных материалов: {e}")
            raise

    def prepare_material_document(self, material: tuple) -> dict:
        """Подготовка документа материала для индексации"""
        return {
            "material_id": material[0],
            "class_id": material[1],
            "content": material[2],
        }

    def sync_to_elasticsearch(self, materials: list) -> bool:
        """Синхронизация данных в Elasticsearch"""
        logger.info("Начало синхронизации данных в Elasticsearch")

        for material in materials:
            try:
                doc = self.prepare_material_document(material)
                response = self.es_client.index(
                    index=INDEX_NAME,
                    id=doc['material_id'],
                    document=doc
                )

                if response['result'] in ['created', 'updated']:
                    self.stats['successful'] += 1
                else:
                    self.stats['failed'] += 1
                    logger.warning(
                        f"Неизвестный статус для сессии {doc['material_id']}: {response['result']}")

            except Exception as e:
                self.stats['failed'] += 1
                logger.error(f"Ошибка индексации сессии {material[0]}: {e}")

        return True

    def run_sync(self) -> bool:
        """Основной метод выполнения синхронизации"""
        self.stats['start_time'] = datetime.now()
        logger.info("Начало синхронизации лекционных сессий")

        try:
            if not self.pg_conn:
                return False
            if not self.es_client:
                return False
            if not self.ensure_index_exists():
                return False

            materials = self.fetch_materials_data()
            if not materials:
                logger.warning("Нет данных для синхронизации")
                return False

            self.sync_to_elasticsearch(materials)

            self.es_client.indices.refresh(index=INDEX_NAME)

            es_count = self.es_client.count(index=INDEX_NAME)['count']
            duration = (datetime.now() -
                        self.stats['start_time']).total_seconds()

            logger.info(
                f"Синхронизация завершена: {self.stats['successful']}/{self.stats['total_sessions']} "
                f"сессий успешно синхронизировано, {self.stats['failed']} ошибок"
            )
            logger.info(f"Количество документов в Elasticsearch: {es_count}")
            logger.info(f"Время выполнения: {duration:.2f} секунд")

            return self.stats['failed'] == 0

        except Exception as e:
            logger.exception(f"Критическая ошибка синхронизации: {e}")
            return False
        finally:
            self.close_connections()


def main():
    synchronizer = ElasticLectureSessionSynchronizer()
    is_success = synchronizer.run_sync()

    if not is_success:
        logger.error("Синхронизация завершена с ошибками")
        return


if __name__ == "__main__":
    main()
