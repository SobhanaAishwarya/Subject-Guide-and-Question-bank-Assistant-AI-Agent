import bcrypt
from typing import Optional
from sqlalchemy.orm import Session
from database.schemas import User, StudyProgress
from utils.logger import logger

class AuthManager:
    """
    Handles secure authentication management operations including user registration,
    login validation, and session lifecycle operations with high-performance password hashing.
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Generates a secure, salted bcrypt hash from a raw text password string.
        """
        try:
            salt = bcrypt.gensalt(rounds=12)
            hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
            return hashed.decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to hash password safely: {str(e)}", exc_info=True)
            raise e

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verifies a raw text password against a stored secure bcrypt string hash.
        """
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except Exception as e:
            logger.error(f"Error executing password signature verification: {str(e)}")
            return False

    @classmethod
    def register_user(cls, session: Session, name: str, email: str, password: str) -> Optional[User]:
        """
        Registers a new user inside the persistent storage layer. Automatically instantiates
        associated records like user-specific study progression profiles.
        """
        try:
            clean_email = email.strip().lower()
            
            # Prevent creation of duplicate profiles
            existing_user = session.query(User).filter(User.email == clean_email).first()
            if existing_user:
                logger.warning(f"Registration rejected: Account email '{clean_email}' already exists.")
                return None

            hashed_pw = cls.hash_password(password)
            
            new_user = User(
                name=name.strip(),
                email=clean_email,
                password_hash=hashed_pw
            )
            session.add(new_user)
            session.flush()  # Extract the new user ID context before committing transaction
            
            # Automatically establish empty initialization metric record for learning progress tracks
            progress_entry = StudyProgress(
                user_id=new_user.id,
                completed_topics="",
                weak_topics="",
                study_time=0.0
            )
            session.add(progress_entry)
            
            logger.info(f"User account '{clean_email}' successfully created with structural metrics profiles.")
            return new_user

        except Exception as e:
            logger.error(f"Transaction abort: Error occurred while executing register_user: {str(e)}", exc_info=True)
            return None

    @classmethod
    def authenticate_user(cls, session: Session, email: str, password: str) -> Optional[User]:
        """
        Validates login access using supplied email coordinates and secure password checking.
        """
        try:
            clean_email = email.strip().lower()
            user = session.query(User).filter(User.email == clean_email).first()
            
            if not user:
                logger.warning(f"Authentication failure: No profile found for email '{clean_email}'.")
                return None
                
            if cls.verify_password(password, user.password_hash):
                logger.info(f"User authentication verified successfully for identity target: '{clean_email}'.")
                return user
            
            logger.warning(f"Authentication failure: Invalid credential payload supplied for email '{clean_email}'.")
            return None
            
        except Exception as e:
            logger.error(f"System logic error encountered during authenticate_user routing: {str(e)}", exc_info=True)
            return None