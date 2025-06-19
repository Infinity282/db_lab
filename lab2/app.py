from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, get_jwt
from db_sync import SyncService
from datetime import datetime
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

app = Flask(__name__)

# Настройка JWT
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', '2e4f746042bfe1d5d6a3d8f877696f45c5ad0ebc8dc76d75e80f35ed167420b1')
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

# Инициализация сервиса синхронизации
service = SyncService(PG_CONFIG, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

@app.route('/api/lab2/audience_report', methods=['POST'])
@jwt_required()
def get_audience_report():
    # Исправление: получение роли из claims через get_jwt()
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json(force=True)
    year = data.get('year')
    semester = data.get('semester')
    if year is None or semester is None:
        return jsonify({'error': 'Required fields: year, semester'}), 400

    try:
        report = service.generate_audience_report(year=year, semester=semester)
        return jsonify({
            'report': report,
            'meta': {'status': 'success', 'count': len(report), 'timestamp': datetime.utcnow().isoformat()}
        }), 200
    except Exception as e:
        app.logger.error(f"Audience report error: {e}")
        return jsonify({'error': 'Failed to generate audience report', 'details': str(e)}), 500
    finally:
        service.close()

# Пример эндпоинта для генерации JWT-токена (для тестирования)
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json(force=True)
    username = data.get('username')
    password = data.get('password')
    if username == 'admin' and password == 'admin123':
        token = create_access_token(identity=username, additional_claims={'role': 'admin'})
        return jsonify({'token': token}), 200
    return jsonify({'error': 'Invalid credentials'}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=False)