import os
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.app import app
from app.db.database import get_db, Base
from app.core.security import create_access_token
import uuid
from app.db.models import EmployeeResponse, EmployeeCategory

# Disable Redis for tests
os.environ['USE_REDIS'] = 'False'

# Create a new async engine for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(TEST_DATABASE_URL, echo=True)

# Create a new session factory
TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
async def test_app():
    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def unique_id():
    return lambda: str(uuid.uuid4())

def get_test_token():
    test_user = {"sub": "testuser@example.com"}
    return create_access_token(test_user)

@pytest.mark.asyncio
async def test_create_employee_category(test_app: AsyncClient, unique_id):
    token = get_test_token()
    response = await test_app.post(
        "/employee-categories",
        json={
            "name": f"Test Category {unique_id()}",
            "level": 1,
            "hourly_rate": 15.0
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "Test Category" in response.json()["name"]
    assert response.json()["id"] is not None
    return response

@pytest.mark.asyncio
async def test_create_employee(test_app: AsyncClient, unique_id):
    category_response = await test_create_employee_category(test_app, unique_id)
    category_id = category_response.json()["id"]
    
    token = get_test_token()
    employee_data = {
        "name": f"John Doe {unique_id()}",
        "category_id": category_id,
        "off_day_preferences": {"Monday": 1},
        "shift_preferences": [1, 2, 3],
        "work_center_preferences": [1],
        "delta": 0.5
    }
    response = await test_app.post(
        "/employees",
        json=employee_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response text: {response.text}"
    
    response_data = response.json()
    assert response_data is not None, f"Response data is None. Response text: {response.text}"
    
    created_employee = EmployeeResponse.model_validate(response_data)
    assert "John Doe" in created_employee.name
    assert created_employee.category_id == category_id
    return created_employee

@pytest.mark.asyncio
async def test_get_employee(test_app: AsyncClient, unique_id):
    created_employee = await test_create_employee(test_app, unique_id)
    employee_id = created_employee.id
    assert employee_id is not None, "Created employee ID is None"

    token = get_test_token()
    response = await test_app.get(f"/employees/{employee_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response text: {response.text}"
    
    response_data = response.json()
    assert response_data is not None, f"Response data is None. Response text: {response.text}"
    
    retrieved_employee = EmployeeResponse.model_validate(response_data)
    assert retrieved_employee.name == created_employee.name
    assert retrieved_employee.category_id == created_employee.category_id

@pytest.mark.asyncio
async def test_create_task(test_app, unique_id):
    token = get_test_token()
    response = await test_app.post(
        "/tasks",
        json={
            "title": f"Test Task {unique_id()}",
            "description": "This is a test task"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "Test Task" in response.json()["title"]
    assert response.json()["id"] is not None
    return response.json()

@pytest.mark.asyncio
async def test_get_task(test_app, unique_id):
    created_task = await test_create_task(test_app, unique_id)
    task_id = created_task["id"]
    
    token = get_test_token()
    response = await test_app.get(f"/tasks/{task_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["id"] == task_id
    assert response.json()["title"] == created_task["title"]

@pytest.mark.asyncio
async def test_get_tasks(test_app, unique_id):
    await test_create_task(test_app, unique_id)
    await test_create_task(test_app, unique_id)
    
    token = get_test_token()
    response = await test_app.get("/tasks", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json()) >= 2

@pytest.mark.asyncio
async def test_update_task(test_app, unique_id):
    created_task = await test_create_task(test_app, unique_id)
    task_id = created_task["id"]
    
    token = get_test_token()
    new_title = f"Updated Task {unique_id()}"
    response = await test_app.put(
        f"/tasks/{task_id}",
        json={"title": new_title},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == task_id
    assert response.json()["title"] == new_title

@pytest.mark.asyncio
async def test_delete_task(test_app, unique_id):
    created_task = await test_create_task(test_app, unique_id)
    task_id = created_task["id"]
    
    token = get_test_token()
    response = await test_app.delete(f"/tasks/{task_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204
    
    # Verify that the task has been deleted
    get_response = await test_app.get(f"/tasks/{task_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_response.status_code == 404

@pytest.mark.asyncio
async def test_generate_fake_data(test_app: AsyncClient):
    token = get_test_token()

    # Check initial database state
    async def check_initial_state():
        categories_response = await test_app.get("/employee-categories", headers={"Authorization": f"Bearer {token}"})
        work_centers_response = await test_app.get("/work-centers", headers={"Authorization": f"Bearer {token}"})
        employees_response = await test_app.get("/employees", headers={"Authorization": f"Bearer {token}"})
        
        assert categories_response.status_code == 200, f"Failed to get initial categories. Status: {categories_response.status_code}, Content: {categories_response.text}"
        assert work_centers_response.status_code == 200, f"Failed to get initial work centers. Status: {work_centers_response.status_code}, Content: {work_centers_response.text}"
        assert employees_response.status_code == 200, f"Failed to get initial employees. Status: {employees_response.status_code}, Content: {employees_response.text}"
        
        return len(categories_response.json()), len(work_centers_response.json()), len(employees_response.json())

    initial_categories, initial_work_centers, initial_employees = await check_initial_state()

    # Generate fake data
    response = await test_app.post(
        "/generate-fake-data",
        params={
            "num_categories": 3,
            "num_work_centers": 2,
            "num_employees": 10
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response text: {response.text}"
    data = response.json()
    assert "message" in data, f"Expected 'message' in response, but got: {data}"
    assert data["message"] == "Fake data generated successfully", f"Unexpected message: {data['message']}"
    assert "categories_created" in data, f"Expected 'categories_created' in response, but got: {data}"
    assert data["categories_created"] == 3, f"Expected 3 categories created, but got: {data['categories_created']}"
    assert "work_centers_created" in data, f"Expected 'work_centers_created' in response, but got: {data}"
    assert data["work_centers_created"] == 2, f"Expected 2 work centers created, but got: {data['work_centers_created']}"
    assert "employees_created" in data, f"Expected 'employees_created' in response, but got: {data}"
    assert data["employees_created"] == 10, f"Expected 10 employees created, but got: {data['employees_created']}"

    # Verify that the data was actually created in the database
    categories_response = await test_app.get("/employee-categories", headers={"Authorization": f"Bearer {token}"})
    work_centers_response = await test_app.get("/work-centers", headers={"Authorization": f"Bearer {token}"})
    employees_response = await test_app.get("/employees", headers={"Authorization": f"Bearer {token}"})

    assert categories_response.status_code == 200, f"Failed to get categories after generation. Status: {categories_response.status_code}, Content: {categories_response.text}"
    assert work_centers_response.status_code == 200, f"Failed to get work centers after generation. Status: {work_centers_response.status_code}, Content: {work_centers_response.text}"
    assert employees_response.status_code == 200, f"Failed to get employees after generation. Status: {employees_response.status_code}, Content: {employees_response.text}"

    assert len(categories_response.json()) == initial_categories + 3, f"Expected {initial_categories + 3} categories, but got {len(categories_response.json())}"
    assert len(work_centers_response.json()) == initial_work_centers + 2, f"Expected {initial_work_centers + 2} work centers, but got {len(work_centers_response.json())}"
    assert len(employees_response.json()) == initial_employees + 10, f"Expected {initial_employees + 10} employees, but got {len(employees_response.json())}"
