import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

# @pytest.mark.asyncio
# async def test_get_token(session: SessionTesting, create_user):
#     # async with AsyncClient(app=app, base_url='http://test') as ac:
#     user = User(
#     first_name='fixture',
#     last_name='fixture',
#     username='fixture',
#     password=await get_hash('fixture')
#     )
#     session.add(user)
#     await session.commit()
#     async with AsyncClient(app=app, base_url='http://localhost:8000') as ac:
#         credentials = {
#             'username': 'fixture',
#             'password': 'fixture'
#         }
#     response = await ac.post('/token/get_token', data=credentials, headers={"content-type": "application/x-www-form-urlencoded"})
#     assert response.status_code == 200