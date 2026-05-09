"""Database initialization script"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sigmaprice.db.models import Base, User, UserRole
from sigmaprice.core.config import get_database_url
from sigmaprice.core.logger import get_logger

logger = get_logger(__name__)


def init_database():
    """Create all tables in the database"""
    engine = create_engine(get_database_url())
    Base.metadata.create_all(engine)
    logger.info("Database tables created successfully")


def create_admin_user(username: str = "admin", password: str = "admin123"):
    """Create the first admin user"""
    from passlib.hash import bcrypt

    engine = create_engine(get_database_url())
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        existing = session.query(User).filter_by(username=username).first()
        if existing:
            logger.warning(f"User {username} already exists")
            return

        admin = User(
            username=username,
            password_hash=bcrypt.hash(password),
            role=UserRole.ADMIN,
            is_trusted=True
        )
        session.add(admin)
        session.commit()
        logger.info(f"Admin user '{username}' created successfully")
    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        session.rollback()
    finally:
        session.close()


def reset_database():
    """Drop all tables and recreate"""
    engine = create_engine(get_database_url())
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    logger.info("Database reset completed")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "reset":
            reset_database()
            logger.info("Database has been reset")
        elif sys.argv[1] == "admin":
            username = sys.argv[2] if len(sys.argv) > 2 else "admin"
            password = sys.argv[3] if len(sys.argv) > 3 else "admin123"
            create_admin_user(username, password)
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("Usage: python init_db.py [reset|admin [username] [password]]")
    else:
        init_database()
        logger.info("Database initialized successfully")