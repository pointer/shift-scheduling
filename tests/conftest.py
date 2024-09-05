import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base
from app.core.config import settings
import yaml
from selenium.webdriver import FirefoxOptions, Firefox, ChromeOptions, Chrome
from selenium.webdriver.chrome.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.chrome import ChromeDriverManager

from send_report import send_report

@pytest.fixture
async def test_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture(scope="function")
async def db_session():
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URL, echo=True)
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture(scope="function")
async def sample_data(db_session):
    # Add your sample data creation logic here
    pass


with open('config.yaml', encoding='utf-8') as f:
    config = yaml.safe_load(f)

@pytest.fixture
def rest_login():
    return login(config["username"], config["password"])

@pytest.fixture
def post_data():
    return "How I spent my summer.", "A story about how I spent my summer holidays.", "Normal."


@pytest.fixture(scope='session')
def browser():
    browser = config["selenium_browser"]
    if browser == 'firefox':
        service = Service(executable_path=GeckoDriverManager().install())
        options = FirefoxOptions()
        driver = Firefox(service=service, options=options)
    else:
        service = Service(executable_path=ChromeDriverManager().install())
        options = ChromeOptions()
        driver = Chrome(service=service, options=options)
    driver.implicitly_wait(config["selenium_implicitly_wait"])
    yield driver
    driver.quit()


@pytest.fixture
def login_fail_data():
    return "test", "test"


@pytest.fixture
def login_fail_error_code():
    return "401"


@pytest.fixture
def login_success_data():
    return config["username"], config["password"]


@pytest.fixture
def contact_us_data():
    return config["username"], "test@test.test", "Test test test"


@pytest.fixture
def contact_us_alert_text():
    return "Form successfully submitted"


def pytest_unconfigure():
    send_report()