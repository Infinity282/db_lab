# Импорт Flask для создания веб-приложения
from flask import Flask, request, jsonify
# Импорт инструмента для работы с Neo4j
from db_utils.neo4j.neo4j_tool import Neo4jTool
# Импорт инструмента для работы с PostgreSQL
from db_utils.postgres.postgres_tool import PostgresTool
# Импорт инструмента для работы с Redis
from db_utils.redis.redis_tool import RedisTool
# Импорт утилиты для проверки наличия обязательных полей
from utils import has_all_required_fields
# Импорт типов для работы с датами и временем
from datetime import datetime, date, time
# Импорт модуля логирования
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,  # Уровень логирования: INFO
    format='%(asctime)s - %(levelname)s - %(message)s'  # Формат сообщений
)
logger = logging.getLogger(__name__)  # Создание логгера

# Инициализация Flask-приложения
app = Flask(__name__)

def get_date_range(year, semester):
    """
    Преобразует год и семестр в диапазон дат.
    :param year: Год (целое число или строка, преобразуемая в число).
    :param semester: Номер семестра (1 или 2).
    :return: Кортеж (start_date, end_date) — строки в формате 'YYYY-MM-DD'.
    """
    try:
        year = int(year)  # Преобразование года в целое число
        if semester == 1:
            # Осенний семестр: с 1 сентября по 31 декабря
            start_date = f"{year}-09-01"
            end_date = f"{year}-12-31"
        elif semester == 2:
            # Весенний семестр: с 1 января по 30 июня следующего года
            start_date = f"{year+1}-01-01"
            end_date = f"{year+1}-06-30"
        else:
            # Ошибка, если семестр не 1 или 2
            raise ValueError("Invalid semester: must be 1 or 2")
        # Проверка корректности дат путем их преобразования
        datetime.strptime(start_date, '%Y-%m-%d')
        datetime.strptime(end_date, '%Y-%m-%d')
        return start_date, end_date  # Возврат диапазона дат
    except ValueError as e:
        # Логирование ошибки и повторное возбуждение исключения
        raise ValueError(f"Invalid date parameters: {str(e)}")

# Определение маршрута для API (POST-запрос)
@app.route('/api/lab2/report', methods=['POST'])
def get_classroom_requirements():
    """
    Обработчик POST-запроса для генерации отчета о требованиях к аудиториям (Лабораторная работа №2).
    Ожидает JSON с полями 'semester' и 'year', возвращает отчет в формате JSON.
    """
    # Проверка, что запрос содержит JSON
    if not request.is_json:
        return jsonify({'error': 'Запрос должен быть в виде JSON'}), 400  # Ошибка 400, если не JSON

    data = request.get_json()  # Получение данных из запроса
    required_fields = ['semester', 'year']  # Список обязательных полей
    # Проверка наличия всех обязательных полей
    if not has_all_required_fields(data, required_fields):
        return jsonify({
            'error': f"Нет необходимых полей: {required_fields}",
            'received': list(data.keys())  # Список полученных полей
        }), 400  # Ошибка 400, если поля отсутствуют

    # Формирование базовой структуры ответа
    response_body = {
        'semester': data['semester'],
        'year': data['year'],
        'courses': []  # Список курсов (пока пустой)
    }

    try:
        # Получение диапазона дат на основе года и семестра
        start_date, end_date = get_date_range(data['year'], data['semester'])
        # Логирование начала обработки запроса
        logger.info(f"Processing report for semester {data['semester']}, year {data['year']}")

        # Инициализация инструментов для работы с базами данных
        postgres_tool = PostgresTool(host='postgres_container')  # Подключение к PostgreSQL
        neo4j_tool = Neo4jTool(host='bolt://neo4j:7687')        # Подключение к Neo4j
        redis_tool = RedisTool(host='redis')                    # Подключение к Redis

        # Получение данных о курсах и лекциях из PostgreSQL
        course_lectures = postgres_tool.get_courses_lectures(
            start_date=start_date,
            end_date=end_date
        )

        # Проверка, найдены ли лекции
        if not course_lectures:
            logger.warning(f"No courses or lectures found for {start_date} to {end_date}")
            return jsonify({'error': 'Курсы или лекции не найдены для указанного семестра и года'}), 404

        courses = {}  # Словарь для хранения данных о курсах
        # Обработка каждой лекции
        for lecture in course_lectures:
            # Проверка наличия 'course_id' в данных лекции
            if 'course_id' not in lecture or not lecture['course_id']:
                logger.error(f"Invalid lecture data, missing course_id: {lecture}")
                continue  # Пропуск некорректной записи
            course_id = lecture['course_id']  # ID курса
            # Если курс еще не добавлен в словарь, инициализируем его структуру
            if course_id not in courses:
                courses[course_id] = {
                    'course_id': course_id,
                    'course_name': lecture.get('course_name', 'Unknown'),  # Название курса (по умолчанию 'Unknown')
                    'lectures': [],          # Список лекций
                    'student_count': 0,      # Количество студентов (пока 0)
                    'classroom_requirements': []  # Требования к аудиториям
                }
            # Преобразование дат и времени в строки для JSON-сериализации
            lecture_date = lecture['date'].strftime('%Y-%m-%d') if isinstance(lecture['date'], date) else str(lecture['date'])
            start_time = lecture['start_time'].strftime('%H:%M:%S') if isinstance(lecture['start_time'], time) else str(lecture['start_time'])
            end_time = lecture['end_time'].strftime('%H:%M:%S') if isinstance(lecture['end_time'], time) else str(lecture['end_time'])
            # Добавление данных о лекции в список лекций курса
            courses[course_id]['lectures'].append({
                'lecture_id': lecture.get('lecture_id', 'Unknown'),  # ID лекции
                'topic': lecture.get('topic', 'Unknown'),            # Тема лекции
                'date': lecture_date,                                # Дата лекции
                'start_time': start_time,                            # Время начала
                'end_time': end_time,                                # Время окончания
                'tech_requirements': lecture.get('tech_requirements', 'None')  # Технические требования
            })

        # Обработка количества студентов и расписания для каждого курса
        for course_id in courses:
            # Попытка получить количество студентов из Redis
            student_count = redis_tool.get_student_count(course_id)
            if student_count is None:
                # Если в Redis нет данных, запрос к PostgreSQL
                student_count = postgres_tool.get_student_count(course_id)
                if student_count is not None:
                    # Сохранение результата в Redis для последующего использования
                    redis_tool.set_student_count(course_id, student_count)
            # Установка количества студентов (0, если данных нет)
            courses[course_id]['student_count'] = student_count or 0

            # Получение списка ID лекций для запроса к Neo4j
            class_ids = [lec['lecture_id'] for lec in courses[course_id]['lectures']]
            # Запрос расписания лекций из Neo4j
            schedules = neo4j_tool.find_lecture_schedules(
                class_ids=class_ids,
                start_date=start_date,
                end_date=end_date
            )

            # Обработка данных расписания
            for schedule in schedules:
                # Преобразование дат и времени в строки
                scheduled_date = schedule['scheduled_date'].strftime('%Y-%m-%d') if isinstance(schedule['scheduled_date'], date) else str(schedule['scheduled_date'])
                start_time = schedule['start_time'].strftime('%H:%M:%S') if isinstance(schedule['start_time'], time) else str(schedule['start_time'])
                end_time = schedule['end_time'].strftime('%H:%M:%S') if isinstance(schedule['end_time'], time) else str(schedule['end_time'])
                # Формирование структуры с требованиями к аудитории
                classroom_info = {
                    'lecture_id': schedule['class_id'],              # ID лекции
                    'room': schedule['room'],                        # Номер аудитории
                    'scheduled_date': scheduled_date,                # Запланированная дата
                    'start_time': start_time,                        # Время начала
                    'end_time': end_time,                            # Время окончания
                    'required_capacity': courses[course_id]['student_count'],  # Требуемая вместимость
                    'tech_requirements': next(                       # Технические требования
                        (lec['tech_requirements'] for lec in courses[course_id]['lectures'] if lec['lecture_id'] == schedule['class_id']),
                        'Unknown'  # Значение по умолчанию, если требования не найдены
                    )
                }
                # Добавление требований к списку
                courses[course_id]['classroom_requirements'].append(classroom_info)

        # Добавление списка курсов в тело ответа
        response_body['courses'] = list(courses.values())
        # Логирование успешной генерации отчета
        logger.info(f"Generated report with {len(courses)} courses")
        return jsonify(report=response_body), 200  # Возврат ответа с кодом 200 (OK)

    except Exception as e:
        # Логирование ошибки и возврат сообщения об ошибке с кодом 500
        logger.error(f"Request processing error: {str(e)}")
        return jsonify({'error': f'Ошибка обработки запроса: {str(e)}'}), 500
    finally:
        # Закрытие соединений с базами данных
        postgres_tool.close()  # Закрытие PostgreSQL
        redis_tool.close()     # Закрытие Redis

# Запуск приложения, если файл выполняется напрямую
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)  # Запуск сервера на порту 5002, доступного извне