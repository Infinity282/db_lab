import json
from app import BASE_URL, app
import pytest


@pytest.fixture
def client():
    """A test client for the app."""
    with app.test_client() as client:
        yield client


def test_generate_lectures_report(client):
    """Test the attendance report generation endpoint."""
    # Тестовые данные
    request_data = {
        "year": "2023",
        "semester": 1
    }

    expected_response = {
        "report": {
            "courses": [
                        {
                            "department_id": 1,
                            "description": "Основы классической механики",
                            "lectures": [
                                {
                                    "name": "Кинематика точки и твёрдого тела",
                                    "student_count": 12,
                                    "tags": "Кафедра теоретической механики",
                                    "tech_requirements": "Доска, маркеры, проектор, калькулятор",
                                    "type": "лекция"
                                },
                                {
                                    "name": "Динамика материальной точки",
                                    "student_count": 12,
                                    "tags": "Кафедра теоретической механики",
                                    "tech_requirements": "Доска, маркеры, проектор, калькулятор",
                                    "type": "лекция"
                                },
                                {
                                    "name": "Теоремы об изменении энергии и импульса",
                                    "student_count": 12,
                                    "tags": "Кафедра теоретической механики",
                                    "tech_requirements": "Доска, маркеры, проектор, калькулятор",
                                    "type": "лекция"
                                }
                            ],
                            "name": "Теоретическая механика",
                            "specialty_id": 1
                        },
                {
                            "department_id": 2,
                            "description": "Основы физики космоса",
                            "lectures": [
                                {
                                    "name": "Основы астрономических наблюдений",
                                    "student_count": 12,
                                    "tags": "Специальный тэг",
                                    "tech_requirements": "Доска, маркеры",
                                    "type": "лекция"
                                },
                                {
                                    "name": "Строение и эволюция звёзд",
                                    "student_count": 12,
                                    "tags": "Обычный тэг",
                                    "tech_requirements": "Доска, маркеры",
                                    "type": "лекция"
                                },
                                {
                                    "name": "Космология: теория Большого взрыва",
                                    "student_count": 12,
                                    "tags": "Специальный тэг",
                                    "tech_requirements": "Доска, маркеры",
                                    "type": "лекция"
                                }
                            ],
                            "name": "Введение в астрофизику",
                            "specialty_id": 2
                        }
            ],
            "semester": 1,
            "year": "2023"
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
        "year": "2023"
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
    assert "year" in error_response["received"]
