import pytest
from fastapi.testclient import TestClient
from app.app import app
from app.core.security import create_access_token

client = TestClient(app)

def get_test_token():
    test_user = {"sub": "testuser@example.com"}
    return create_access_token(test_user)

def test_create_employee():
    response = client.post(
        "/api/employees",
        json={
            "name": "John Doe",
            "category_id": 1,
            "off_day_preferences": {"Monday": 1},
            "shift_preferences": [1, 2, 3],
            "work_center_preferences": [1],
            "delta": 0.5
        }
    )
    assert response.status_code == 200
    assert response.json()["name"] == "John Doe"

def test_get_employee():
    # First, create an employee
    create_response = client.post(
        "/api/employees",
        json={
            "name": "Jane Doe",
            "category_id": 1,
            "off_day_preferences": {"Tuesday": 1},
            "shift_preferences": [2, 1, 3],
            "work_center_preferences": [1, 2],
            "delta": 0.5
        }
    )
    employee_id = create_response.json()["id"]

    # Now, get the employee
    response = client.get(f"/api/employees/{employee_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Jane Doe"
