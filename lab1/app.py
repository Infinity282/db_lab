from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required
from const import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, ES_HOST, ES_PORT, ES_USER, ES_PASS, REDIS_HOST, REDIS_PORT
from session_type_search import SessionTypeSearch
from lab import AttendanceFinder
from lecture_session import LectureMaterialSearcher
import redis
import os

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret-key')
jwt = JWTManager(app)

def has_all_required_fields(data, required_fields):
    if not all(field in data for field in required_fields):
        return False
    return True

@app.route('/api/lab1/report', methods=['POST'])
@jwt_required()
def generate_attendance_report():
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400

    data = request.get_json()

    required_fields = ['term', 'start_date', 'end_date']
    if not has_all_required_fields(data, required_fields):
        return jsonify({
            'error': f"Missing required fields: {required_fields}",
            'received': list(data.keys())
        }), 400

    # Фильтр только лекций
    session_searcher = SessionTypeSearch(redis_host=REDIS_HOST, redis_port=REDIS_PORT)
    sessions = session_searcher.get_by_name('lecture')
    if not sessions:
        return jsonify({'error': 'No lecture session type found'}), 404

    es_searcher = LectureMaterialSearcher(es_host=ES_HOST, es_port=ES_PORT, es_user=ES_USER, es_password=ES_PASS)
    class_ids = es_searcher.search_by_course_and_session_type(data['term'], sessions[0]['id'])
    if not class_ids:
        return jsonify({'error': 'No classes found for the term'}), 404

    finder = AttendanceFinder(uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD)
    redis_conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    try:
        worst = finder.find_worst_attendees(
            class_ids,
            top_n=10,
            start_date=data['start_date'],
            end_date=data['end_date']
        )

        def format_student(record):
            redis_info = redis_conn.hgetall(f"student:{record['studentId']}")
            return {
                **record,
                'redis_info': {
                    'name': redis_info.get('name'),
                    'age': redis_info.get('age'),
                    'mail': redis_info.get('mail'),
                    'group': redis_info.get('group')
                }
            }

        report = {
            'search_term': data['term'],
            'period': f"{data['start_date']} - {data['end_date']}",
            'found_classes': len(class_ids),
            'worst_attendees': [format_student(r) for r in worst]
        }
        return jsonify(report=report, meta={'status': 'success', 'results': len(worst)}), 200

    except Exception as e:
        app.logger.error(f"Error: {e}")
        return jsonify({'error': 'Data processing failed'}), 500

    finally:
        finder.close()
        redis_conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)