# from typing import Union, Optional, Any, AsyncGenerator
# from sqlalchemy.ext.asyncio import AsyncSession
# from app.db.database import SessionLocal
# from app.core.config import settings


# # async def get_db() -> AsyncSession:
# #     async with SessionLocal() as session:
# #         yield session
        
# async def get_db() -> AsyncGenerator[AsyncSession, None]:
#     db_config = ConnectionConfig(
#         service="mysql",
#         driver="asyncmy",
#         user=settings.DB_USER,
#         password=settings.DB_PASS,
#         host=settings.DB_HOST,
#         database=settings.DB_NAME,
#     )
#     engine = create_async_engine(
#             get_db_url(config=db_config), echo=settings.DEVELOPMENT
#         )
#     async with AsyncSession(engine) as session:
#         yield session        