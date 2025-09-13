from flask import Flask, request, jsonify
from db_utils.mongo.mongo_tool import MongoTool
from db_utils.neo4j.neo4j_tool import Neo4jTool
from db_utils.postgres.postgres_tool import PostgresTool
from db_utils.redis.redis_tool import RedisTool
from utils import has_all_required_fields, get_date_range

import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

BASE_URL = '/api/lab3/report'

# МЕХ-101


@app.route(BASE_URL, methods=['POST'])
def get_classroom_requirements():
    """
    Обработчик POST-запроса для генерации отчета о прослушанных лекциях (Лабораторная работа №3).
    Ожидает JSON с полями 'group_name', возвращает отчет в формате JSON.
    """
    if not request.is_json:
        return jsonify({'error': 'Запрос должен быть в виде JSON'}), 400

    data = request.get_json()
    required_fields = ['group_name']
    if not has_all_required_fields(data, required_fields):
        return jsonify({
            'error': f"Нет необходимых полей: {required_fields}",
            'received': list(data.keys())
        }), 400

    response_body = {
        'group_info': {},
        'students': []
    }

    try:
        # Получаем id группы по названию
        group_name = data['group_name']
        postgres_tool = PostgresTool(host='localhost')
        group_info = postgres_tool.get_student_group_by_name(
            group_name=group_name)

        if group_info['id'] is None:
            raise Exception(f'Группа с названием {group_name} не найдена')
        response_body['group_info'] = group_info

        # Получаем название кафедры по group_department_id
        print(group_info, group_info['department_id'])
        mongo_tool = MongoTool(host='localhost')
        department_name = mongo_tool.get_department_name_by_id(
            department_id=int(group_info['department_id'])
        )
        if department_name is None:
            raise Exception(f'Не найдена кафедра для группы')

        # Получаем всех студентов, а также информацию про них
        redis_tool = RedisTool(host='localhost')
        students = redis_tool.get_students_info_by_group_id(
            group_id=group_info['id']
        )
        if not students:
            return jsonify(report=response_body), 200

        # Ищем все расписания по лекциям со специальным тегом на текущую дату для нашей группы и возвращаем курс лекций, все расписания
        neo4j_tool = Neo4jTool(host='bolt://localhost:7687')
        schedules = neo4j_tool.find_special_lectures_and_course_of_lectures(
            group_id=group_info['id'], special_tag=department_name)

        print('schedules', schedules)

        # Находим все посещения студентом лекций на текущий момент
        for student in students:
            student_info = {
                'id': student['id'],
                'group_id': student['group_id'],
                'name': student['name'],
                'enrollment_year': student['enrollment_year'],
                'date_of_birth': student['date_of_birth'],
                'email': student['email'],
                'book_number': student['book_number'],
                'courses': []
            }
            for schedule in schedules:
                # add course info
                attendance_info = postgres_tool.get_student_attendance(
                    student['id'], schedule['schedule_ids']),

                if not attendance_info:
                    print(f'нет attendance_info для студента {student['id']}')
                    return

                planned_hours = len(schedule['schedule_ids']) * 2
                listened_hours = attendance_info[0] * 2
                student_info['courses'].append({
                    'course_info': {
                        'id': schedule['course_id'],
                        'specialty_id': schedule['course.specialty_id'],
                        'name': schedule['course.name'],
                        'description': schedule['course.description']
                    },
                    'planned_hours': planned_hours,
                    'listened_hours': listened_hours
                })
                print(attendance_info)

            response_body['students'].append(student_info)
        return jsonify(report=response_body), 200

    except Exception as e:
        logger.error(f"Request processing error: {str(e)}")
        return jsonify({'error': f'Ошибка обработки запроса: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
