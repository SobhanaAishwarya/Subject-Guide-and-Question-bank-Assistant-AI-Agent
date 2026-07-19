import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Relationships
    pdfs = relationship("UploadedPDF", back_populates="user", cascade="all, delete-orphan")
    chats = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")
    quizzes = relationship("QuizResult", back_populates="user", cascade="all, delete-orphan")
    progress = relationship("StudyProgress", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>"


class UploadedPDF(Base):
    __tablename__ = "uploaded_pdfs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(512), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="pdfs")

    def __repr__(self) -> str:
        return f"<UploadedPDF(id={self.id}, filename='{self.filename}', user_id={self.user_id})>"


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="chats")

    def __repr__(self) -> str:
        return f"<ChatHistory(id={self.id}, user_id={self.user_id}, timestamp={self.timestamp})>"


class QuizResult(Base):
    __tablename__ = "quiz_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic = Column(String(255), nullable=False)
    score = Column(Float, nullable=False)  # Stored as a percentage or raw metric
    date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="quizzes")

    def __repr__(self) -> str:
        return f"<QuizResult(id={self.id}, topic='{self.topic}', score={self.score})>"


class StudyProgress(Base):
    __tablename__ = "study_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    completed_topics = Column(Text, default="", nullable=False)  # Comma-separated or serialized string data
    weak_topics = Column(Text, default="", nullable=False)       # Comma-separated or serialized string data
    study_time = Column(Float, default=0.0, nullable=False)       # Total calculated hours spent

    # Relationships
    user = relationship("User", back_populates="progress")

    def __repr__(self) -> str:
        return f"<StudyProgress(id={self.id}, user_id={self.user_id}, study_time={self.study_time}h)>"