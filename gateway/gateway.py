from flask import Flask, request, jsonify
import os
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
import requests
from const import USER_DATA

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret-key')
jwt = JWTManager(app)


@app.route('/api/token', methods=['POST'])
def get_token():
    data = request.get_json(force=True)
    if data.get('username') != USER_DATA['username'] or data.get('password') != USER_DATA['password']:
        return jsonify({'msg': 'Неверные учетные данные'}), 401
    token = create_access_token(identity=data['username'])
    return jsonify(access_token=token), 200


@app.route('/api/lab1/report', methods=['POST'])
@jwt_required()
def proxy_lab1():
    base_url = os.getenv(f'LAB1_URL')
    resp = requests.post(
        f"{base_url}/api/lab1/report",
        json=request.get_json(force=True),
        headers={'Content-Type': 'application/json'}
    )
    return jsonify(resp.json()), resp.status_code


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001)
