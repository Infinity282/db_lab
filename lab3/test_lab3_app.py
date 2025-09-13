import json
from app import BASE_URL, app
import pytest


@pytest.fixture
def client():
    """A test client for the app."""
    with app.test_client() as client:
        yield client


def test_generate_attendance(client):
    """Test the attendance report generation endpoint."""
    # Тестовые данные
    request_data = {
        "group_name": "МЕХ-101"
    }

    expected_response = {
        "report": {
            "group_info": {
                "course_year": 1,
                "department_id": 1,
                "id": 1,
                "name": "МЕХ-101"
            },
            "students": [
                {
                    "book_number": "01001",
                    "courses": [
                        {
                            "course_info": {
                                "description": "Основы классической механики",
                                "id": 1,
                                "name": "Теоретическая механика",
                                "specialty_id": 1
                            },
                            "listened_hours": 0,
                            "planned_hours": 6
                        }
                    ],
                    "date_of_birth": "2002-05-12",
                    "email": "ivan.ivanov@university.edu",
                    "enrollment_year": "2023",
                    "group_id": 1,
                    "id": 1,
                    "name": "Иванов Иван"
                },
                {
                    "book_number": "01002",
                    "courses": [
                        {
                            "course_info": {
                                "description": "Основы классической механики",
                                "id": 1,
                                "name": "Теоретическая механика",
                                "specialty_id": 1
                            },
                            "listened_hours": 0,
                            "planned_hours": 6
                        }
                    ],
                    "date_of_birth": "2001-08-23",
                    "email": "alexey.petrov@university.edu",
                    "enrollment_year": "2023",
                    "group_id": 1,
                    "id": 2,
                    "name": "Петров Алексей"
                },
                {
                    "book_number": "01003",
                    "courses": [
                        {
                            "course_info": {
                                "description": "Основы классической механики",
                                "id": 1,
                                "name": "Теоретическая механика",
                                "specialty_id": 1
                            },
                            "listened_hours": 0,
                            "planned_hours": 6
                        }
                    ],
                    "date_of_birth": "2002-11-30",
                    "email": "maria.sidorova@university.edu",
                    "enrollment_year": "2023",
                    "group_id": 1,
                    "id": 3,
                    "name": "Сидорова Мария"
                },
                {
                    "book_number": "01004",
                    "courses": [
                        {
                            "course_info": {
                                "description": "Основы классической механики",
                                "id": 1,
                                "name": "Теоретическая механика",
                                "specialty_id": 1
                            },
                            "listened_hours": 4,
                            "planned_hours": 6
                        }
                    ],
                    "date_of_birth": "2001-03-15",
                    "email": "dmitry.kuznetsov@university.edu",
                    "enrollment_year": "2023",
                    "group_id": 1,
                    "id": 4,
                    "name": "Кузнецов Дмитрий"
                },
                {
                    "book_number": "01005",
                    "courses": [
                        {
                            "course_info": {
                                "description": "Основы классической механики",
                                "id": 1,
                                "name": "Теоретическая механика",
                                "specialty_id": 1
                            },
                            "listened_hours": 6,
                            "planned_hours": 6
                        }
                    ],
                    "date_of_birth": "2002-07-08",
                    "email": "anna.smirnova@university.edu",
                    "enrollment_year": "2023",
                    "group_id": 1,
                    "id": 5,
                    "name": "Смирнова Анна"
                },
                {
                    "book_number": "01006",
                    "courses": [
                        {
                            "course_info": {
                                "description": "Основы классической механики",
                                "id": 1,
                                "name": "Теоретическая механика",
                                "specialty_id": 1
                            },
                            "listened_hours": 6,
                            "planned_hours": 6
                        }
                    ],
                    "date_of_birth": "2001-09-21",
                    "email": "mikhail.popov@university.edu",
                    "enrollment_year": "2023",
                    "group_id": 1,
                    "id": 6,
                    "name": "Попов Михаил"
                },
                {
                    "book_number": "02001",
                    "courses": [
                        {
                            "course_info": {
                                "description": "Основы классической механики",
                                "id": 1,
                                "name": "Теоретическая механика",
                                "specialty_id": 1
                            },
                            "listened_hours": 0,
                            "planned_hours": 6
                        }
                    ],
                    "date_of_birth": "2000-04-17",
                    "email": "sergey.fedorov@university.edu",
                    "enrollment_year": "2023",
                    "group_id": 1,
                    "id": 7,
                    "name": "Федоров Сергей"
                },
                {
                    "book_number": "02002",
                    "courses": [
                        {
                            "course_info": {
                                "description": "Основы классической механики",
                                "id": 1,
                                "name": "Теоретическая механика",
                                "specialty_id": 1
                            },
                            "listened_hours": 2,
                            "planned_hours": 6
                        }
                    ],
                    "date_of_birth": "2001-01-25",
                    "email": "ekaterina.morozova@university.edu",
                    "enrollment_year": "2023",
                    "group_id": 1,
                    "id": 8,
                    "name": "Морозова Екатерина"
                },
                {
                    "book_number": "02003",
                    "courses": [
                        {
                            "course_info": {
                                "description": "Основы классической механики",
                                "id": 1,
                                "name": "Теоретическая механика",
                                "specialty_id": 1
                            },
                            "listened_hours": 2,
                            "planned_hours": 6
                        }
                    ],
                    "date_of_birth": "2000-12-05",
                    "email": "andrey.vasilyev@university.edu",
                    "enrollment_year": "2023",
                    "group_id": 1,
                    "id": 9,
                    "name": "Васильев Андрей"
                },
                {
                    "book_number": "02004",
                    "courses": [
                        {
                            "course_info": {
                                "description": "Основы классической механики",
                                "id": 1,
                                "name": "Теоретическая механика",
                                "specialty_id": 1
                            },
                            "listened_hours": 4,
                            "planned_hours": 6
                        }
                    ],
                    "date_of_birth": "2001-06-14",
                    "email": "olga.novikova@university.edu",
                    "enrollment_year": "2023",
                    "group_id": 1,
                    "id": 10,
                    "name": "Новикова Ольга"
                },
                {
                    "book_number": "02005",
                    "courses": [
                        {
                            "course_info": {
                                "description": "Основы классической механики",
                                "id": 1,
                                "name": "Теоретическая механика",
                                "specialty_id": 1
                            },
                            "listened_hours": 4,
                            "planned_hours": 6
                        }
                    ],
                    "date_of_birth": "2000-02-28",
                    "email": "artem.lebedev@university.edu",
                    "enrollment_year": "2023",
                    "group_id": 1,
                    "id": 11,
                    "name": "Лебедев Артем"
                },
                {
                    "book_number": "02006",
                    "courses": [
                        {
                            "course_info": {
                                "description": "Основы классической механики",
                                "id": 1,
                                "name": "Теоретическая механика",
                                "specialty_id": 1
                            },
                            "listened_hours": 4,
                            "planned_hours": 6
                        }
                    ],
                    "date_of_birth": "2001-10-11",
                    "email": "natalia.kozlova@university.edu",
                    "enrollment_year": "2023",
                    "group_id": 1,
                    "id": 12,
                    "name": "Козлова Наталья"
                }
            ]
        }
    }

    response = client.post(
        BASE_URL,
        data=json.dumps(request_data),
        content_type='application/json'
    )

    assert response.status_code == 200
    assert response.get_json() == expected_response


def test_generate_attendance_report_invalid_data(client):
    """Test the endpoint with invalid data."""
    # Тест с отсутствующими полями
    request_data = {

    }

    response = client.post(
        BASE_URL,
        data=json.dumps(request_data),
        content_type='application/json'
    )

    # Ожидаем ошибку валидации
    assert response.status_code in [400]

    error_response = response.get_json()
    assert "error" in error_response
    assert "received" in error_response
    assert "Нет необходимых полей" in error_response["error"]
