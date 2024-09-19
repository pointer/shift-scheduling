from sqlalchemy import select
from app.db.models import Employee  # Add this import

class Crud:
    @classmethod
    def read_by_id(cls, db_session, _id):
        return db_session.query(cls).get(_id)

    @classmethod
    def read_one(cls, db_session, _filter):
        return db_session.query(cls).filter(_filter).one_or_none()

    @classmethod
    def read(cls, db_session, _filter):
        return db_session.query(cls).filter(_filter).all()

    @classmethod
    def exists(cls, db_session, _id):
        return db_session.query(cls).get(_id).one_or_none() is not None

    # upsert by id (create and delete)
    def save(self, db_session):
        if self.id is None:
            db_session.add(self)
        db_session.commit()
        db_session.refresh(self)
        return self

    # delete
    def destroy(self, db_session):
        db_session.delete(self)
        db_session.commit()
        return self

    # Add your CRUD operations here
    async def get_employees(self,db):
        # Implement the get_employees function
        pass

    @classmethod
    async def get_employees(cls, db_session):
        result = await db_session.execute(select(Employee))
        return result.scalars().all()