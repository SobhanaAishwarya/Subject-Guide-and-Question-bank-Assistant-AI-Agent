import os
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from utils.logger import logger

# Initialize Declarative Base for ORM Schemas
Base = declarative_base()

# Resolve Database URL from Environment Variables (Fallback to local SQLite)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///agentic_study_assistant.db")

logger.info(f"Initializing database engine with target URL: {DATABASE_URL}")

try:
    # SQLite requires special threading arguments since Streamlit runs multi-threaded
    connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True  # Detects and recovers stale connections immediately
    )
    
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    
    logger.info("SQLAlchemy database engine and SessionLocal factory initialized successfully.")
except Exception as e:
    logger.critical(f"Failed to initialize database engine: {str(e)}", exc_info=True)
    raise e

def init_db() -> None:
    """
    Creates all defined database tables according to schema declarations.
    This should be called during application startup.
    """
    try:
        logger.info("Executing database table initialization...")
        Base.metadata.create_all(bind=engine)
        logger.info("All database tables synced and created successfully.")
    except Exception as e:
        logger.error(f"Error occurred during database initialization: {str(e)}", exc_info=True)
        raise e

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager providing a transactional database session context.
    Ensures that connections are safely rolled back on errors and closed after use.
    """
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database transaction error caught; rolled back changes: {str(e)}", exc_info=True)
        raise e
    finally:
        session.close()