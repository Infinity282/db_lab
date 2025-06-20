import psycopg2
import redis
from contextlib import closing
from datetime import datetime
import logging
from env import (DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT,
                 DB_USER, REDIS_HOST, REDIS_PORT)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RedisStudentSynchronizer:
    def __init__(self) -> None:
        self.pg_conn = None
        self.redis_client = None
        self.stats = {
            'students': 0,
            'start_time': None
        }

        self.connect_postgres()
        self.connect_redis()

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

    def connect_redis(self) -> bool:
        """Установка соединения с Redis"""
        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Успешное подключение к Redis")
            return True
        except redis.ConnectionError as e:
            logger.error(f"Ошибка подключения к Redis: {e}")
            return False

    def close_connections(self) -> None:
        if self.pg_conn:
            self.pg_conn.close()
            logger.info("Соединение с PostgreSQL закрыто")
        if self.redis_client:
            self.redis_client.close()
            logger.info("Соединение с Redis закрыто")

    def clear_redis_data(self) -> None:
        logger.info("Очистка старых данных в Redis")

        # Удаление ключей студентов
        student_keys = [
            key for key in self.redis_client.scan_iter("student:*")]
        # Удаление индексных ключей
        index_keys = [
            key for key in self.redis_client.scan_iter("index:student:*")]

        all_keys = student_keys + index_keys
        if all_keys:
            self.redis_client.delete(*all_keys)
            logger.info(f"Удалено {len(all_keys)} ключей Redis")

    def fetch_students_data(self) -> list:
        """Получение данных студентов из PostgreSQL"""
        logger.info("Извлечение данных студентов из PostgreSQL")

        with closing(self.pg_conn.cursor()) as cursor:
            try:
                cursor.execute("""
                    SELECT id, group_id, name, enrollment_year, 
                           date_of_birth, email, book_number 
                    FROM Students
                """)
                students = cursor.fetchall()
                logger.info(f"Получено {len(students)} записей о студентах")
                return students
            except psycopg2.Error as e:
                logger.error(f"Ошибка получения данных: {e}")
                raise

    def sync_to_redis(self, students: list) -> None:
        """Сохранение данных студентов в Redis"""
        logger.info("Сохранение данных в Redis")

        for student in students:
            (student_id, group_id, name, enrollment_year,
             date_of_birth, email, book_number) = student

            student_key = f"student:{student_id}"
            mapping = {
                'id': student_id,
                'group_id': group_id,
                'name': name,
                'enrollment_year': enrollment_year,
                'date_of_birth': str(date_of_birth),
                'email': email,
                'book_number': book_number
            }
            self.redis_client.hset(student_key, mapping=mapping)

            # Создание индексов
            self.redis_client.sadd(
                f"index:student:name:{name.lower()}", student_id)
            self.redis_client.sadd(
                f"index:student:email:{email.lower()}", student_id)
            self.redis_client.sadd(
                f"index:student:book_number:{book_number.lower()}", student_id)

    def run_sync(self) -> bool:
        """Основной метод выполнения синхронизации"""
        self.stats['start_time'] = datetime.now()
        logger.info("Начало синхронизации данных студентов")

        try:
            if not self.pg_conn:
                return False
            if not self.redis_client:
                return False

            self.clear_redis_data()

            students = self.fetch_students_data()
            self.stats['students'] = len(students)

            if not students:
                logger.warning("Нет данных студентов для синхронизации")
                return False

            self.sync_to_redis(students)

            redis_count = len(self.redis_client.keys("student:*"))
            if redis_count != self.stats['students']:
                logger.error(
                    f"Несоответствие данных: PostgreSQL={self.stats['students']}, Redis={redis_count}")
                return False

            duration = (datetime.now() -
                        self.stats['start_time']).total_seconds()
            logger.info(
                f"Синхронизация завершена: {self.stats['students']} студентов "
                f"за {duration:.2f} секунд"
            )
            return True

        except Exception as e:
            logger.exception(f"Критическая ошибка синхронизации: {e}")
            return False
        finally:
            self.close_connections()


if __name__ == "__main__":
    synchronizer = RedisStudentSynchronizer()
    is_success = synchronizer.run_sync()
