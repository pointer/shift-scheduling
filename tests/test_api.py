import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.app import app
from app.dependencies import get_db
from app.core.security import create_access_token
from httpx import AsyncClient

@pytest.fixture
async def override_get_db():
    async def _override_get_db():
        async with AsyncSession(engine) as session:
            yield session
    return _override_get_db

# @pytest.fixture
# async def test_client():
#     async with AsyncClient(app=app, base_url="http://test") as client:
#         yield client

@pytest.mark.asyncio
async def test_create_employee(test_client):
    token = get_test_token()
    response = await test_client.post(
        "/api/employees",
        json={
            "name": "John Doe",
            "category_id": 1,
            "off_day_preferences": {"Monday": 1},
            "shift_preferences": [1, 2, 3],
            "work_center_preferences": [1],
            "delta": 0.5
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "John Doe"

def get_test_token():
    test_user = {"sub": "testuser@example.com"}
    return create_access_token(test_user)

# def test_create_employee():
#     token = get_test_token()
#     response = client.post(
#         "/api/employees",
#         json={
#             "name": "John Doe",
#             "category_id": 1,
#             "off_day_preferences": {"Monday": 1},
#             "shift_preferences": [1, 2, 3],
#             "work_center_preferences": [1],
#             "delta": 0.5
#         },
#         headers={"Authorization": f"Bearer {token}"}
#     )
#     assert response.status_code == 200
#     assert response.json()["name"] == "John Doe"

@pytest.mark.asyncio
async def test_get_employee(test_client):
    token = get_test_token()
    # First, create an employee
    create_response = await test_client.post(
        "/api/employees",
        json={
            "name": "Jane Doe",
            "category_id": 1,
            "off_day_preferences": {"Tuesday": 1},
            "shift_preferences": [2, 1, 3],
            "work_center_preferences": [1, 2],
            "delta": 0.5
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_response.status_code == 200
    employee_id = create_response.json().get("id")
    assert employee_id is not None

    # Now, get the employee
    response = await test_client.get(f"/api/employees/{employee_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["name"] == "Jane Doe"
