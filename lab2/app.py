from flask import Flask, request, jsonify
from db_utils.neo4j.neo4j_tool import Neo4jTool
from utils import has_all_required_fields, get_date_range

import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route('/api/lab2/report', methods=['POST'])
def get_classroom_requirements():
    """
    Обработчик POST-запроса для генерации отчета о требованиях к аудиториям (Лабораторная работа №2).
    Ожидает JSON с полями 'semester' и 'year', возвращает отчет в формате JSON.
    """
    if not request.is_json:
        return jsonify({'error': 'Запрос должен быть в виде JSON'}), 400

    data = request.get_json()
    required_fields = ['semester', 'year']
    if not has_all_required_fields(data, required_fields):
        return jsonify({
            'error': f"Нет необходимых полей: {required_fields}",
            'received': list(data.keys())
        }), 400

    response_body = {
        'semester': data['semester'],
        'year': data['year'],
        'courses': []
    }

    try:
        # Преобразуем семестр и год к промежутку времени
        start_date, end_date = get_date_range(data['year'], data['semester'])
        logger.info(
            f"Processing report for semester {data['semester']}, year {data['year']}, {start_date}, {end_date}")

        neo4j_tool = Neo4jTool(host='bolt://localhost:7687')
        lectures = neo4j_tool.find_students_and_lectures(
            start_date=start_date,
            end_date=end_date
        )

        unique_courses = {}

        for item in lectures:
            course_name = item['course.name']

            # Создаем структуру для лекции
            lecture_data = {
                'name': item['c.name'],
                'tags': item['c.tags'],
                'type': item['c.type'],
                'tech_requirements': item['c.tech_requirements'],
                'student_count': item['total_students']
            }

            if course_name not in unique_courses:
                # Создаем новый курс с массивом лекций
                unique_courses[course_name] = {
                    'name': course_name,
                    'department_id': item['course.department_id'],
                    'specialty_id': item['course.specialty_id'],
                    'description': item['course.description'],
                    'lectures': [lecture_data]
                }
            else:
                unique_courses[course_name]['lectures'].append(lecture_data)

        response_body['courses'] = list(unique_courses.values())

        return jsonify(report=response_body), 200

    except Exception as e:
        logger.error(f"Request processing error: {str(e)}")
        return jsonify({'error': f'Ошибка обработки запроса: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
