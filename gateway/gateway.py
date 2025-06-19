# gateway.py
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
import os
import requests

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', '2e4f746042bfe1d5d6a3d8f877696f45c5ad0ebc8dc76d75e80f35ed167420b1')
jwt = JWTManager(app)

# Определение учетных данных непосредственно в коде
HARDCODED_USER = {'username': 'user', 'password': 'user'}

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json(force=True)
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'msg': 'Отсутствуют учетные данные'}), 400
    if data.get('username') != HARDCODED_USER['username'] or data.get('password') != HARDCODED_USER['password']:
        return jsonify({'msg': 'Неверные учетные данные'}), 401
    # Исправление: identity как строка, role в additional_claims
    token = create_access_token(identity=data['username'], additional_claims={'role': 'admin'})
    return jsonify(access_token=token), 200

def forward_request(lab_number):
    base_url = os.getenv(f'LAB{lab_number}_URL')
    if not base_url:
        return jsonify({'msg': f'URL для LAB{lab_number} не настроен'}), 500
    endpoint = 'report' if lab_number == 1 else 'audience_report' if lab_number == 2 else 'group_report'
    resp = requests.post(
        f"{base_url}/api/lab{lab_number}/{endpoint}",
        json=request.get_json(force=True),
        headers=dict(request.headers)
    )
    return jsonify(resp.json()), resp.status_code

@app.route('/api/lab1/report', methods=['POST'])
@jwt_required()
def proxy_lab1():
    return forward_request(1)

@app.route('/api/lab2/audience_report', methods=['POST'])
@jwt_required()
def proxy_lab2():
    return forward_request(2)

@app.route('/api/lab3/group_report', methods=['POST'])
@jwt_required()
def proxy_lab3():
    return forward_request(3)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1337)