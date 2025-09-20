from flask import Flask, Response, request, jsonify
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
    try:
        base_url = 'http://lab1:5001'
        resp = requests.post(
            f"{base_url}/api/lab1/report",
            json=request.get_json(force=True),
            headers={'Content-Type': 'application/json'}
        )
        return Response(
            resp.content,
            status=resp.status_code,
            headers=dict(resp.headers)
        )
    except requests.exceptions.Timeout:
        return jsonify({'error': f'Таймаут при обращении'}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({'error': f'Не удалось подключиться'}), 503
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Ошибка проксирования: {str(e)}'}), 502


@app.route('/api/lab2/report', methods=['POST'])
@jwt_required()
def proxy_lab2():
    try:
        base_url = 'http://lab2:5002'
        resp = requests.post(
            f"{base_url}/api/lab2/report",
            json=request.get_json(force=True),
            headers={'Content-Type': 'application/json'}
        )
        return Response(
            resp.content,
            status=resp.status_code,
            headers=dict(resp.headers)
        )
    except requests.exceptions.Timeout:
        return jsonify({'error': f'Таймаут при обращении'}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({'error': f'Не удалось подключиться'}), 503
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Ошибка проксирования: {str(e)}'}), 502


@app.route('/api/lab3/report', methods=['POST'])
@jwt_required()
def proxy_lab3():
    try:
        base_url = 'http://lab3:5003'
        resp = requests.post(
            f"{base_url}/api/lab3/report",
            json=request.get_json(force=True),
            headers={'Content-Type': 'application/json'}
        )
        return Response(
            resp.content,
            status=resp.status_code,
            headers=dict(resp.headers)
        )
    except requests.exceptions.Timeout:
        return jsonify({'error': f'Таймаут при обращении'}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({'error': f'Не удалось подключиться'}), 503
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Ошибка проксирования: {str(e)}'}), 502


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001)
