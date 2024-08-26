import sys
import os

sys.path.append(os.getcwd())

from fastapi import HTTPException, Depends
from app.models import User
from app.services.user import UserService
from app.schemas.user import UserCreateRequest
from app.helpers.enums import UserRole
from app.core.config import settings
from app.core.security import verify_password, get_password_hash
from app.db.base import engine
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError


def create_super_user():
    engine = create_engine(settings.DATABASE_URL, pool_size=20, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    session = SessionLocal()
    session.rollback()
    session.commit()

    # superuser
    try:
        new_user = User(
            username=settings.SUPERUSER_NAME,
            hashed_password=get_password_hash(settings.SUPERUSER_PASSWORD),
            is_active = True,
            role = 'admin'
        )
        session.add(new_user)
        session.commit()
        print('Admin created successfully.')
    except IntegrityError as e:
        if "duplicate key value violates unique constraint" in str(e.orig):
            print("User already exists.")
        else:
            print("An error occurred:", str(e))
        session.rollback()
    except Exception as e:
        session.rollback()
        raise e

    finally:
        session.close()

if __name__ == '__main__':
    create_super_user()