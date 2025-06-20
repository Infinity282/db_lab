from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from db_sync import SyncService
from datetime import datetime
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

app = Flask(__name__)

# Настройка JWT
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', '2e4f746042bfe1d5d6a3d8f877696f45c5ad0ebc8dc76d75e80f35ed167420b1')  # Замените на безопасный ключ
jwt = JWTManager(app)

# Настройка параметров подключения
PG_CONFIG = {
    'dbname': os.getenv('POSTGRES_DB', 'postgres_db'),
    'user': os.getenv('POSTGRES_USER', 'postgres_user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres_password'),
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', 5432),
}

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'strongpassword')
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

# Инициализация сервиса синхронизации
service = SyncService(PG_CONFIG, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, REDIS_HOST, REDIS_PORT)

@app.route('/api/lab3/group_report', methods=['POST'])
@jwt_required()
def get_group_report():
    # Проверка роли пользователя
    current_user = get_jwt_identity()
    if current_user.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json(force=True)
    group_id = data.get('group_id')
    if group_id is None:
        return jsonify({'error': 'Required field: group_id'}), 400

    try:
        report = service.generate_group_report(group_id=group_id)
        return jsonify({
            'report': report,
            'meta': {'status': 'success', 'group_id': group_id, 'count': len(report), 'timestamp': datetime.utcnow().isoformat()}
        }), 200
    except Exception as e:
        app.logger.error(f"Group report error: {e}")
        return jsonify({'error': 'Failed to generate group report', 'details': str(e)}), 500
    finally:
        service.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json(force=True)
    username = data.get('username')
    password = data.get('password')
    if username == 'admin' and password == 'admin123':  # Замените на реальную проверку
        from jwt import encode
        token = encode({'role': 'admin', 'sub': username}, app.config['JWT_SECRET_KEY'], algorithm='HS256')
        return jsonify({'token': token}), 200
    return jsonify({'error': 'Invalid credentials'}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=False)