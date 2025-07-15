from flask import Flask, request, jsonify
from db_utils.neo4j.neo4j_tool import Neo4jTool
from db_utils.postgres.postgres_tool import PostgresTool
from db_utils.redis.redis_tool import RedisTool
from utils import has_all_required_fields
from datetime import datetime, date, time
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def get_date_range(year, semester):
    """
    Преобразует год и семестр в диапазон дат.
    :param year: Год (целое число или строка, преобразуемая в число).
    :param semester: Номер семестра (1 или 2).
    :return: Кортеж (start_date, end_date) — строки в формате 'YYYY-MM-DD'.
    """
    try:
        year = int(year)
        if semester == 1:
            start_date = f"{year}-09-01"
            end_date = f"{year}-12-31"
        elif semester == 2:
            start_date = f"{year+1}-01-01"
            end_date = f"{year+1}-06-30"
        else:
            raise ValueError("Invalid semester: must be 1 or 2")
        datetime.strptime(start_date, '%Y-%m-%d')
        datetime.strptime(end_date, '%Y-%m-%d')
        return start_date, end_date
    except ValueError as e:
        raise ValueError(f"Invalid date parameters: {str(e)}")

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
        start_date, end_date = get_date_range(data['year'], data['semester'])
        logger.info(f"Processing report for semester {data['semester']}, year {data['year']}")

        postgres_tool = PostgresTool(host='postgres')
        neo4j_tool = Neo4jTool(host='bolt://neo4j:7687')
        redis_tool = RedisTool(host='redis')

        course_lectures = postgres_tool.get_courses_lectures_lab2(
            start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
            end_date=datetime.strptime(end_date, '%Y-%m-%d').date()
        )

        if not course_lectures:
            logger.warning(f"No courses or lectures found for {start_date} to {end_date}")
            return jsonify({'error': 'Курсы или лекции не найдены для указанного семестра и года'}), 404

        courses = {}
        for lecture in course_lectures:
            if 'course_id' not in lecture or not lecture['course_id']:
                logger.error(f"Invalid lecture data, missing course_id: {lecture}")
                continue
            course_id = lecture['course_id']
            if course_id not in courses:
                courses[course_id] = {
                    'course_id': course_id,
                    'course_name': lecture.get('course_name', 'Unknown'),
                    'lectures': [],
                    'student_count': 0,
                    'classroom_requirements': []
                }
            lecture_date = lecture['date'].strftime('%Y-%m-%d') if isinstance(lecture['date'], date) else str(lecture['date'])
            start_time = lecture['start_time'].strftime('%H:%M:%S') if isinstance(lecture['start_time'], time) else str(lecture['start_time'])
            end_time = lecture['end_time'].strftime('%H:%M:%S') if isinstance(lecture['end_time'], time) else str(lecture['end_time'])
            courses[course_id]['lectures'].append({
                'lecture_id': lecture.get('lecture_id', 'Unknown'),
                'topic': lecture.get('topic', 'Unknown'),
                'date': lecture_date,
                'start_time': start_time,
                'end_time': end_time,
                'tech_requirements': lecture.get('tech_requirements', 'None')
            })

        for course_id in courses:
            student_count = redis_tool.get_student_count(course_id)
            if student_count is None:
                student_count = postgres_tool.get_student_count_lab2(course_id)
                if student_count is not None:
                    redis_tool.set_student_count(course_id, student_count)
            courses[course_id]['student_count'] = student_count or 0

            class_ids = [lec['lecture_id'] for lec in courses[course_id]['lectures']]
            schedules = neo4j_tool.find_lecture_schedules(
                class_ids=class_ids,
                start_date=start_date,
                end_date=end_date
            )

            for schedule in schedules:
                scheduled_date = schedule['scheduled_date'].strftime('%Y-%m-%d') if isinstance(schedule['scheduled_date'], date) else str(schedule['scheduled_date'])
                start_time = schedule['start_time'].strftime('%H:%M:%S') if isinstance(schedule['start_time'], time) else str(schedule['start_time'])
                end_time = schedule['end_time'].strftime('%H:%M:%S') if isinstance(schedule['end_time'], time) else str(schedule['end_time'])
                classroom_info = {
                    'lecture_id': schedule['class_id'],
                    'room': schedule['room'],
                    'scheduled_date': scheduled_date,
                    'start_time': start_time,
                    'end_time': end_time,
                    'required_capacity': courses[course_id]['student_count'],
                    'tech_requirements': next(
                        (lec['tech_requirements'] for lec in courses[course_id]['lectures'] if lec['lecture_id'] == schedule['class_id']),
                        'Unknown'
                    )
                }
                courses[course_id]['classroom_requirements'].append(classroom_info)

        response_body['courses'] = list(courses.values())
        logger.info(f"Generated report with {len(courses)} courses")
        return jsonify(report=response_body), 200

    except Exception as e:
        logger.error(f"Request processing error: {str(e)}")
        return jsonify({'error': f'Ошибка обработки запроса: {str(e)}'}), 500
    finally:
        postgres_tool.close()
        redis_tool.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)