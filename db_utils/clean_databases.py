from env import (
    DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT,
    MONGO_URI, MONGO_DB_NAME, MONGO_USERNAME, MONGO_PASSWORD,
    REDIS_HOST, REDIS_PORT,
    NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD,
    ES_HOST, ES_PORT, ES_USER, ES_PASSWORD
)
import psycopg2
from pymongo import MongoClient
from neo4j import GraphDatabase
from elasticsearch import Elasticsearch
import redis
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseCleaner:
    def __init__(self):
        """Инициализация подключений ко всем базам данных"""
        self.connections = {
            'postgres': None,
            'mongo': None,
            'neo4j': None,
            'elastic': None,
            'redis': None
        }

    def connect_all(self):
        """Установка соединений со всеми БД"""
        try:
            # PostgreSQL
            logger.info("Подключаемся к PostgreSQL...")
            self.connections['postgres'] = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT
            )
            
            # MongoDB
            logger.info("Подключаемся к MongoDB...")
            mongo_auth = {}
            if MONGO_USERNAME:
                mongo_auth['username'] = MONGO_USERNAME
            if MONGO_PASSWORD:
                mongo_auth['password'] = MONGO_PASSWORD
            self.connections['mongo'] = MongoClient(
                MONGO_URI,
                **mongo_auth
            )[MONGO_DB_NAME]
            
            # Neo4j
            logger.info("Подключаемся к Neo4j...")
            self.connections['neo4j'] = GraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USER, NEO4J_PASSWORD)
            )
            
            # ElasticSearch
            logger.info("Подключаемся к ElasticSearch...")
            es_host = f"http://{ES_HOST}:{ES_PORT}" if not ES_HOST.startswith(('http://', 'https://')) else ES_HOST
            es_auth = (ES_USER, ES_PASSWORD) if ES_USER and ES_PASSWORD else None
            self.connections['elastic'] = Elasticsearch(
                hosts=[es_host],
                basic_auth=es_auth,
                verify_certs=False  # Для разработки, в production следует использовать True
            )
            if not self.connections['elastic'].ping():
                raise ConnectionError("Не удалось подключиться к Elasticsearch")
            
            # Redis
            logger.info("Подключаемся к Redis...")
            redis_kwargs = {
                'host': REDIS_HOST,
                'port': REDIS_PORT,
                'db': 0
            }
            if 'REDIS_PASSWORD' in globals():
                redis_kwargs['password'] = REDIS_PASSWORD
            self.connections['redis'] = redis.Redis(**redis_kwargs)
            self.connections['redis'].ping()  # Проверка подключения
            
            logger.info("Все подключения установлены успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка подключения: {str(e)}", exc_info=True)
            self.close_all_connections()
            return False

    def clean_postgres(self):
        """Очистка всех таблиц и сброс последовательностей ID в PostgreSQL"""
        try:
            with self.connections['postgres'].cursor() as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                if not tables:
                    logger.info("PostgreSQL: Нет таблиц для очистки")
                    return True
                
                cursor.execute("SET session_replication_role = 'replica';")
                
                for table in tables:
                    cursor.execute(f'TRUNCATE TABLE "{table}" CASCADE')
                
                cursor.execute("""
                    SELECT sequence_name 
                    FROM information_schema.sequences 
                    WHERE sequence_schema = 'public'
                """)
                sequences = [row[0] for row in cursor.fetchall()]
                
                for sequence in sequences:
                    try:
                        cursor.execute(f'ALTER SEQUENCE "{sequence}" RESTART WITH 1;')
                    except Exception as seq_error:
                        logger.warning(f"Не удалось сбросить последовательность {sequence}: {seq_error}")
                
                cursor.execute("SET session_replication_role = 'origin';")
                
                self.connections['postgres'].commit()
                logger.info(f"PostgreSQL: Очищено {len(tables)} таблиц и сброшено {len(sequences)} последовательностей")
                return True
                
        except Exception as e:
            self.connections['postgres'].rollback()
            logger.error(f"Ошибка очистки PostgreSQL: {str(e)}", exc_info=True)
            return False

    def clean_mongodb(self):
        """Очистка всех коллекций в MongoDB"""
        try:
            db = self.connections['mongo']
            collections = db.list_collection_names()
            
            if not collections:
                logger.info("MongoDB: Нет коллекций для очистки")
                return True
                
            for collection in collections:
                db[collection].delete_many({})
            
            logger.info(f"MongoDB: Очищено {len(collections)} коллекций")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка очистки MongoDB: {str(e)}", exc_info=True)
            return False

    def clean_neo4j(self):
        """Очистка всех данных в Neo4j"""
        try:
            with self.connections['neo4j'].session() as session:
                result = session.run("MATCH (n) RETURN count(n) AS count")
                count = result.single()['count']
                
                if count == 0:
                    logger.info("Neo4j: Нет данных для очистки")
                    return True
                    
                session.run("MATCH (n) DETACH DELETE n")
                logger.info(f"Neo4j: Удалено {count} узлов")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка очистки Neo4j: {str(e)}", exc_info=True)
            return False

    def clean_elasticsearch(self):
        """Очистка всех индексов в ElasticSearch"""
        try:
            indices = list(self.connections['elastic'].indices.get_alias().keys())
            user_indices = [idx for idx in indices if not idx.startswith('.')]
            
            if not user_indices:
                logger.info("ElasticSearch: Нет индексов для очистки")
                return True
                
            for index in user_indices:
                self.connections['elastic'].indices.delete(index=index)
            
            logger.info(f"ElasticSearch: Удалено {len(user_indices)} индексов")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка очистки ElasticSearch: {str(e)}", exc_info=True)
            return False

    def clean_redis(self):
        """Очистка всех данных в Redis"""
        try:
            db_size = self.connections['redis'].dbsize()
            if db_size == 0:
                logger.info("Redis: Нет данных для очистки")
                return True
                
            self.connections['redis'].flushdb()
            logger.info(f"Redis: Очищено {db_size} ключей")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка очистки Redis: {str(e)}", exc_info=True)
            return False

    def clean_all_databases(self):
        """Очистка всех баз данных"""
        if not self.connect_all():
            return False
        
        results = {
            'postgres': self.clean_postgres(),
            'mongo': self.clean_mongodb(),
            'neo4j': self.clean_neo4j(),
            'elastic': self.clean_elasticsearch(),
            'redis': self.clean_redis()
        }
        
        self.close_all_connections()
        
        if all(results.values()):
            logger.info("Все базы данных успешно очищены!")
            return True
        else:
            failed = [db for db, success in results.items() if not success]
            logger.error(f"Ошибки при очистке следующих БД: {', '.join(failed)}")
            return False

    def close_all_connections(self):
        """Закрытие всех соединений с базами данных"""
        for name, conn in self.connections.items():
            if conn is None:
                continue
                
            try:
                if name == 'postgres':
                    conn.close()
                elif name == 'mongo':
                    conn.client.close()
                elif name == 'neo4j':
                    conn.close()
                elif name == 'elastic':
                    conn.close()
                elif name == 'redis':
                    conn.close()
                    
                logger.info(f"Соединение с {name} закрыто")
            except Exception as e:
                logger.error(f"Ошибка при закрытии соединения с {name}: {str(e)}")

if __name__ == "__main__":
    cleaner = DatabaseCleaner()
    if cleaner.clean_all_databases():
        logger.info("Очистка всех баз данных завершена успешно!")
    else:
        logger.error("При очистке баз данных возникли ошибки")