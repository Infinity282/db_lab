import json
from app import app
import pytest


@pytest.fixture
def client():
    """A test client for the app."""
    with app.test_client() as client:
        yield client


def test_generate_attendance_report(client):
    """Test the attendance report generation endpoint."""
    # Тестовые данные
    request_data = {
        "material": "кинемати",
        "start_date": "2023-09-01",
        "end_date": "2023-12-16"
    }

    expected_response = {
        "report": {
            "period": "2023-09-01 - 2023-12-16",
            "search_term": "кинемати",
            "worst_attendees": [
                  {
                      "attendance_percent": 0.0,
                      "book_number": "01001",
                      "group_id": 1,
                      "missed_lectures": 1,
                      "name": "Иванов Иван",
                      "student_id": 1,
                      "total_lectures": 1
                  },
                {
                      "attendance_percent": 0.0,
                      "book_number": "01002",
                      "group_id": 1,
                      "missed_lectures": 1,
                      "name": "Петров Алексей",
                      "student_id": 2,
                      "total_lectures": 1
                  },
                {
                      "attendance_percent": 0.0,
                      "book_number": "01003",
                      "group_id": 1,
                      "missed_lectures": 1,
                      "name": "Сидорова Мария",
                      "student_id": 3,
                      "total_lectures": 1
                  },
                {
                      "attendance_percent": 0.0,
                      "book_number": "02001",
                      "group_id": 1,
                      "missed_lectures": 1,
                      "name": "Федоров Сергей",
                      "student_id": 7,
                      "total_lectures": 1
                  },
                {
                      "attendance_percent": 0.0,
                      "book_number": "02003",
                      "group_id": 1,
                      "missed_lectures": 1,
                      "name": "Васильев Андрей",
                      "student_id": 9,
                      "total_lectures": 1
                  },
                {
                      "attendance_percent": 0.0,
                      "book_number": "02006",
                      "group_id": 1,
                      "missed_lectures": 1,
                      "name": "Козлова Наталья",
                      "student_id": 12,
                      "total_lectures": 1
                  },
                {
                      "attendance_percent": 100.0,
                      "book_number": "01004",
                      "group_id": 1,
                      "missed_lectures": 0,
                      "name": "Кузнецов Дмитрий",
                      "student_id": 4,
                      "total_lectures": 1
                  },
                {
                      "attendance_percent": 100.0,
                      "book_number": "01005",
                      "group_id": 1,
                      "missed_lectures": 0,
                      "name": "Смирнова Анна",
                      "student_id": 5,
                      "total_lectures": 1
                  },
                {
                      "attendance_percent": 100.0,
                      "book_number": "01006",
                      "group_id": 1,
                      "missed_lectures": 0,
                      "name": "Попов Михаил",
                      "student_id": 6,
                      "total_lectures": 1
                  },
                {
                      "attendance_percent": 100.0,
                      "book_number": "02002",
                      "group_id": 1,
                      "missed_lectures": 0,
                      "name": "Морозова Екатерина",
                      "student_id": 8,
                      "total_lectures": 1
                  }
            ]
        }
    }

    response = client.post(
        '/api/lab1/report',
        data=json.dumps(request_data),
        content_type='application/json'
    )

    assert response.status_code == 200
    assert response.get_json() == expected_response


def test_generate_attendance_report_invalid_data(client):
    """Test the endpoint with invalid data."""
    # Тест с отсутствующими полями
    request_data = {
        "material": "кинемати"
        # missing start_date and end_date
    }

    response = client.post(
        '/api/lab1/report',
        data=json.dumps(request_data),
        content_type='application/json'
    )

    # Ожидаем ошибку валидации
    assert response.status_code in [400]

    error_response = response.get_json()
    assert "error" in error_response
    assert "received" in error_response
    assert "Нет необходимых полей" in error_response["error"]
    assert "material" in error_response["received"]


def test_generate_attendance_report_empty_material(client):
    """Test the endpoint with empty material."""
    empty_data = {
        "material": "",
        "start_date": "2023-09-01",
        "end_date": "2023-12-16"
    }

    response = client.post(
        '/api/lab1/report',
        data=json.dumps(empty_data),
        content_type='application/json'
    )

    # В зависимости от логики приложения, может возвращать ошибку или пустой отчет
    assert response.status_code in [200]
