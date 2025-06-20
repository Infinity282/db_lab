#!/usr/bin/env python3
import redis
import logging
from env import REDIS_HOST, REDIS_PORT
from random import sample

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('redis_checker')


class RedisDataChecker:
    def __init__(self, host, port):
        self.redis = redis.Redis(
            host=host,
            port=port,
            decode_responses=True
        )
        try:
            self.redis.ping()
            logger.info("Успешное подключение к Redis")
        except redis.ConnectionError:
            logger.error("Не удалось подключиться к Redis")
            raise

    def get_total_students(self) -> int:
        """Возвращает общее количество студентов в Redis"""
        return len(self.redis.keys("student:*"))

    def get_all_students(self) -> list:
        """Возвращает все записи студентов"""
        keys = self.redis.keys("student:*")
        return [self.redis.hgetall(key) for key in keys]

    def get_random_students(self, count: int) -> list:
        """Возвращает случайные записи студентов"""
        all_keys = self.redis.keys("student:*")
        if not all_keys:
            return []

        count = min(count, len(all_keys))
        sample_keys = sample(all_keys, count)
        return [self.redis.hgetall(key) for key in sample_keys]

    def get_by_name(self, name: str) -> list:
        """Поиск студентов по точному имени"""
        index_key = f"index:student:name:{name.lower()}"
        student_ids = self.redis.smembers(index_key)
        return [self.redis.hgetall(f"student:{id}") for id in student_ids]

    def get_by_email(self, email: str) -> list:
        """Поиск студентов по точному email"""
        index_key = f"index:student:email:{email.lower()}"
        student_ids = self.redis.smembers(index_key)
        return [self.redis.hgetall(f"student:{id}") for id in student_ids]

    def get_index_stats(self) -> dict:
        """Возвращает статистику по индексам"""
        name_indexes = self.redis.keys("index:student:name:*")
        email_indexes = self.redis.keys("index:student:email:*")

        return {
            'total_name_indexes': len(name_indexes),
            'total_email_indexes': len(email_indexes),
            'sample_name_index': name_indexes[0] if name_indexes else None,
            'sample_email_index': email_indexes[0] if email_indexes else None,
        }


def print_student(student: dict):
    """Форматированный вывод информации о студенте"""
    print("\n" + "=" * 50)
    print(f"Студент ID: {student.get('id', 'N/A')}")
    print("-" * 50)
    print(f"Имя: {student.get('name', 'N/A')}")
    print(f"Email: {student.get('email', 'N/A')}")
    print(f"Группа: {student.get('group_id', 'N/A')}")
    print(f"Год поступления: {student.get('enrollment_year', 'N/A')}")
    print(f"Дата рождения: {student.get('date_of_birth', 'N/A')}")
    print(f"Номер зачетки: {student.get('book_number', 'N/A')}")
    print("=" * 50 + "\n")


def main():
    try:
        checker = RedisDataChecker(REDIS_HOST, REDIS_PORT)

        # 1. Проверка общего количества
        total = checker.get_total_students()
        logger.info(f"Общее количество студентов в Redis: {total}")

        # 2. Вывод всех записей (если их немного)
        if total > 0 and total <= 20:
            logger.info("\nВывод всех записей студентов:")
            all_students = checker.get_all_students()
            for student in all_students:
                print_student(student)
        elif total > 20:
            logger.info(
                f"\nСлишком много записей ({total}), вывод только 5 случайных")

        # 3. Вывод случайных записей
        if total > 0:
            sample_size = min(5, total)
            logger.info(f"\nВывод {sample_size} случайных записей:")
            for student in checker.get_random_students(sample_size):
                print_student(student)

        # 4. Проверка индексов
        index_stats = checker.get_index_stats()
        logger.info("\nСтатистика индексов:")
        logger.info(
            f"  Индексов по именам: {index_stats['total_name_indexes']}")
        logger.info(
            f"  Индексов по email: {index_stats['total_email_indexes']}")

        # 5. Автоматическая проверка поиска
        if total > 0:
            # Выбор случайного студента для демонстрации поиска
            random_student = checker.get_random_students(1)[0]
            name = random_student.get('name')
            email = random_student.get('email')

            if name:
                logger.info(f"\nПроверка поиска по имени: '{name}'")
                results = checker.get_by_name(name)
                logger.info(f"Найдено записей: {len(results)}")
                for student in results:
                    print_student(student)

            if email:
                logger.info(f"\nПроверка поиска по email: '{email}'")
                results = checker.get_by_email(email)
                logger.info(f"Найдено записей: {len(results)}")
                for student in results:
                    print_student(student)

    except Exception as e:
        logger.error(f"Ошибка при проверке данных: {e}")
        exit(1)


if __name__ == "__main__":
    main()
