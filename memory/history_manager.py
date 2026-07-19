import datetime
from typing import List
from sqlalchemy.orm import Session
from database.schemas import ChatHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from utils.logger import logger

class HistoryManager:
    """
    Production-grade Session Memory manager that serializes runtime graph message 
    exchanges directly to relational SQLite storage and hydrates LangGraph memory pipelines.
    """

    @staticmethod
    def save_chat_turn(session: Session, user_id: int, question: str, answer: str) -> bool:
        """
        Persists a user interaction turn into the chat_history database table.
        """
        try:
            logger.info(f"Saving new conversation turn to database for user_id={user_id}")
            chat_entry = ChatHistory(
                user_id=user_id,
                question=question.strip(),
                answer=answer.strip(),
                timestamp=datetime.datetime.utcnow()
            )
            session.add(chat_entry)
            session.flush()
            logger.info(f"Successfully saved chat turn ID={chat_entry.id} for user_id={user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to commit chat turn history to database: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def get_serialized_messages(session: Session, user_id: int, limit: int = 20) -> List[BaseMessage]:
        """
        Fetches historical chat logs from database and maps them to clean LangChain message objects
        (HumanMessage/AIMessage pairs) for processing context windows.
        """
        try:
            logger.debug(f"Hydrating historical chat interactions for user_id={user_id} with limit={limit}")
            records = (
                session.query(ChatHistory)
                .filter(ChatHistory.user_id == user_id)
                .order_by(ChatHistory.timestamp.desc())
                .limit(limit)
                .all()
            )
            
            # Reverse records to reconstruct chronological order
            records.reverse()
            
            langchain_messages: List[BaseMessage] = []
            for rec in records:
                langchain_messages.append(HumanMessage(content=rec.question))
                langchain_messages.append(AIMessage(content=rec.answer))
                
            logger.info(f"Hydrated {len(langchain_messages)} systemic messages for user_id={user_id}")
            return langchain_messages
        except Exception as e:
            logger.error(f"Error hydrating session context window memory for user_id={user_id}: {str(e)}", exc_info=True)
            return []

    @staticmethod
    def clear_user_history(session: Session, user_id: int) -> bool:
        """
        Purges historical chat records matching user signature cleanly out of data tables.
        """
        try:
            logger.warning(f"Executing database history purge request for user_id={user_id}")
            session.query(ChatHistory).filter(ChatHistory.user_id == user_id).delete()
            logger.info(f"Successfully cleared all chat records for user_id={user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear chat history tables for user_id={user_id}: {str(e)}", exc_info=True)
            return False