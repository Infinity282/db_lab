#!/usr/bin/env python3
from elasticsearch import Elasticsearch
import logging
from env import ES_HOST, ES_PORT, ES_USER, ES_PASSWORD
from db_utils.elastic.const import INDEX_NAME

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('es_data_checker')


class ElasticDataChecker:
    def __init__(self, index_name=INDEX_NAME):
        self.es = Elasticsearch(
            hosts=[f"http://{ES_HOST}:{ES_PORT}"],
            basic_auth=(ES_USER, ES_PASSWORD),
            verify_certs=False
        )
        self.index_name = index_name
        if not self.es.ping():
            raise ConnectionError("Не удалось подключиться к Elasticsearch")
        logger.info(
            f"Подключение к Elasticsearch установлено. Индекс: {index_name}")

    def get_random_documents(self, size=5):
        """Получение случайных документов из индекса"""
        try:
            response = self.es.search(
                index=self.index_name,
                size=size,
                query={
                    "function_score": {
                        "query": {"match_all": {}},
                        "random_score": {}
                    }
                }
            )
            return [hit["_source"] for hit in response["hits"]["hits"]]
        except Exception as e:
            logger.error(f"Ошибка при получении документов: {e}")
            return []

    def print_document(self, doc, doc_num):
        """Печать документа в читаемом формате"""
        print(f"\n{'=' * 60}")
        print(f"МАТЕРИАЛ #{doc_num}")
        print(f"{'=' * 60}")

        print(f"ID материала: {doc.get('material_id', 'N/A')}")
        print(f"ID занятия: {doc.get('class_id', 'N/A')}")

        content = doc.get('content', '')
        print(f"\nСодержание материала:")
        print("-" * 60)

        # Форматированный вывод с переносами
        if len(content) > 200:
            print(content[:200] + "...")
            print(f"\n... (полный текст: {len(content)} символов)")
        else:
            print(content)

        print(f"{'-' * 60}")


def main():
    try:
        checker = ElasticDataChecker()

        # Получение информации об индексе
        # try:
        #     index_info = checker.es.indices.get(index=checker.index_name)
        #     print(index_info)
        #     total_docs = index_info[checker.index_name]['primaries']['docs']['count']
        #     logger.info(f"Всего документов в индексе: {total_docs}")
        # except:
        #     logger.warning("Не удалось получить информацию об индексе")
        #     total_docs = 0

        # if total_docs == 0:
        #     logger.warning("Индекс пуст. Нет данных для отображения.")
        #     return

        # Получение случайных документов
        documents = checker.get_random_documents()

        if not documents:
            logger.warning("Не удалось получить документы")
            return

        logger.info(f"\nВывод {len(documents)} случайных документов:")

        # Печать документов
        for i, doc in enumerate(documents, 1):
            checker.print_document(doc, i)

        print("\n" + "=" * 60)
        logger.info("Проверка данных завершена")

    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")


if __name__ == "__main__":
    main()
