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

    # Elastic ищем все материалы с заданным термином
    elastic_tool = ElasticTool(host='localhost')
    materials = elastic_tool.search_materials_by_content(data['material'])

    # Если материалов нет
    if not materials:
        print('Нет материалов')
        return jsonify(report=response_body), 200

    class_ids = []
    for material in materials:
        class_ids.append(material['class_id'])
        print(f"Material ID: {material['material_id']}")
        print(f"Class ID: {material['class_id']}")
        print(f"Content snippet: {material['content'][:100]}...")
        print("-" * 50)

    # Neo4j ищем все расписания по промежутку и массиву class_ids из материалов
    neo4j_tool = Neo4jTool(host='bolt://localhost:7687')
    schedules = neo4j_tool.find_lecture_schedules(
        class_ids=class_ids,
        start_date=data['start_date'],
        end_date=data['end_date']
    )

    # Если расписаний нет
    if not schedules:
        print('Нет расписаний')
        return jsonify(report=response_body), 200

    schedules_info = []
    for schedule in schedules:
        print(schedules)
        schedules_info.append({
            "schedule_id": schedule['id'],
            "student_id": schedule['group_id']
        })
        print(f"Лекция {schedule['class_id']} в аудитории {schedule['room']}")
        print(f"Группа {schedule['group_id']} в аудитории {schedule['room']}")
        print(f"Дата: {schedule['scheduled_date']}")
        print(f"Время: {schedule['start_time']} - {schedule['end_time']}")
        print("-" * 50)

    # Redis ищем всех студентов по группе
    redis_tool = RedisTool(host='localhost')

    students_ids = set()
    full_student_info = {}

    for schedule_info in schedules_info:
        group_students = redis_tool.get_student_info_by_group_id(
            group_id=schedule_info['student_id'])

        for student_info in group_students:
            student_id = student_info['id']

            if student_id not in students_ids:
                full_student_info[student_id] = {
                    'name': student_info['name'],
                    'group_id': student_info['group_id'],
                    'book_number': student_info['book_number']
                }
                students_ids.add(student_id)

    if not students_ids:
        print('Нет студентов')
        return jsonify(report=response_body), 200

    # Postgres ищем топ 10 студентов
    postgres_tool = PostgresTool(host='localhost', port='5430')
    schedule_ids = [item["schedule_id"] for item in schedules_info]
    students = postgres_tool.get_students_with_lowest_attendance(
        schedule_ids=schedule_ids, students_ids=list(students_ids))

    # Если нет худших студентов
    if not students:
        print('Нет худших студентов')
        return jsonify(report=response_body), 200

    # Формируем информацию для вывода
    for student in students:
        student_id = student['student_id']

        if student_id in students_ids:
            student_info = {
                'student_id': student_id,
                'name': full_student_info[student_id]['name'],
                'group_id': full_student_info[student_id]['group_id'],
                'book_number': full_student_info[student_id]['book_number'],
                'missed_lectures': student['missed_count'],
                'total_lectures': student['total_lectures'],
                'attendance_percent': student['attendance_percent']
            }
            response_body['worst_attendees'].append(student_info)
        print(student)

    return jsonify(report=response_body), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
