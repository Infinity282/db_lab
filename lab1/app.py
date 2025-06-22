from flask import Flask, request, jsonify
from db_utils.elastic.elastic_tool import ElasticTool
from db_utils.neo4j.neo4j_tool import Neo4jTool
from db_utils.postgres.postgres_tool import PostgresTool
from db_utils.redis.redis_tool import RedisTool
from utils import has_all_required_fields

app = Flask(__name__)


@app.route('/api/lab1/report', methods=['POST'])
def get_report_by_date_and_term():
    if not request.is_json:
        return jsonify({'error': 'Запрос должен быть в виде JSON'}), 400

    data = request.get_json()
    required_fields = ['material', 'start_date', 'end_date']
    if not has_all_required_fields(data, required_fields):
        jsonify({
            'error': f"Нет необходимых полей: {required_fields}",
            'received': list(data.keys())
        }), 400

    response_body = {
        'search_term': data['material'],
        'period': f"{data['start_date']} - {data['end_date']}",
        'worst_attendees': []
    }

    # Elastic
    elastic_tool = ElasticTool(host='elasticsearch')
    materials = elastic_tool.search_materials_by_content(
        data['material'], host='localhost')

    # Если материалов нет
    if not materials:
        return jsonify(report=response_body), 200

    class_ids = []
    # Для дебага
    for material in materials:
        class_ids.append(material['class_id'])
        print(f"Material ID: {material['material_id']}")
        print(f"Class ID: {material['class_id']}")
        print(f"Content snippet: {material['content'][:100]}...")
        print("-" * 50)

    # Neo4j
    neo4j_tool = Neo4jTool(host='bolt://neo4j:7687')
    schedules = neo4j_tool.find_lecture_schedules(
        class_ids=class_ids,
        start_date=data['start_date'],
        end_date=data['end_date']
    )

    # Если schedules нет
    if not schedules:
        return jsonify(report=response_body), 200

    schedules_id = []
    for schedule in schedules:
        schedules_id.append(schedule['id'])
        print(f"Лекция {schedule['class_id']} в аудитории {schedule['room']}")
        print(f"Дата: {schedule['scheduled_date']}")
        print(f"Время: {schedule['start_time']} - {schedule['end_time']}")
        print("-" * 50)

    # Postgres
    postgres_tool = PostgresTool(host='postgres')
    students = postgres_tool.get_students_with_lowest_attendance(
        schedule_ids=schedules_id)

    # Если schedules нет
    if not students:
        return jsonify(report=response_body), 200

    # Redis
    redis_tool = RedisTool(host='redis')
    for student in students:
        full_student_info = redis_tool.get_student_info(
            student_id=student['student_id'])
        student_info = {
            'student_id': student['student_id'],
            'name': full_student_info['name'],
            'group_id': full_student_info['group_id'],
            'book_number': full_student_info['book_number'],
            'missed_lectures': student['missed_count'],
            'total_lectures': student['total_lectures'],
            'attendance_percent': student['attendance_percent']
        }
        response_body['worst_attendees'].append(student_info)
        print(student)

    return jsonify(report=response_body), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
