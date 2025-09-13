import logging
from elasticsearch import Elasticsearch
from db_utils.elastic.const import INDEX_NAME
from env import ES_HOST, ES_PASSWORD, ES_PORT, ES_USER

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ElasticTool:
    def __init__(self, host: str = ES_HOST):
        """Инициализация класса, но соединение пока не устанавливаем"""
        self.es_client = None
        self.host = host

    def _get_connection(self) -> Elasticsearch:
        """Создает и возвращает новое соединение с Elasticsearch"""
        try:
            es_client = Elasticsearch(
                hosts=[f"http://{self.host}:{ES_PORT}"],
                basic_auth=(ES_USER, ES_PASSWORD),
                verify_certs=False
            )
            if es_client.ping():
                return es_client
            raise ConnectionError("Не удалось подключиться к Elasticsearch")
        except Exception as e:
            logger.error(f"Ошибка подключения к Elasticsearch: {e}")
            raise

    def search_materials_by_content(self, search_query: str) -> list:
        """
        Поиск материалов, содержащих заданную строку в поле content.
        Соединение создается и закрывается автоматически при каждом вызове.

        :param search_query: Строка для поиска
        :param size: Количество возвращаемых результатов
        :return: Список найденных материалов или пустой список при ошибке
        """
        try:
            self.es_client = self._get_connection()

            search_body = {
                "query": {
                    "match": {
                        "content": {
                            "query": search_query,
                            "fuzziness": "AUTO"
                        }
                    }
                },
                "_source": ["material_id", "class_id", "content"],
                "highlight": {
                    "fields": {
                        "content": {
                            "pre_tags": ["<b>"],
                            "post_tags": ["</b>"],
                            "fragment_size": 200
                        }
                    }
                }
            }

            response = self.es_client.search(
                index=INDEX_NAME,
                body=search_body,
            )

            hits = response['hits']['hits']
            results = [{
                "material_id": hit['_source']['material_id'],
                "class_id": hit['_source']['class_id'],
                "content": hit['_source']['content'],
            } for hit in hits]

            logger.info(
                f"Найдено {len(results)} материалов по запросу '{search_query}'")
            return results
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}")
            return []
        finally:
            if self.es_client:
                self.es_client.close()
                self.es_client = None


def main():
    searcher = ElasticTool()
    results = searcher.search_materials_by_content("кинемати")

    for result in results:
        print(f"Material ID: {result['material_id']}")
        print(f"Class ID: {result['class_id']}")
        print(f"Content snippet: {result['content'][:100]}...")
        print("-" * 50)


if __name__ == "__main__":
    main()
