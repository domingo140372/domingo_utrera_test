#### Models of messages
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime, timezone
from uuid import UUID, uuid4
from app.users.models import Users

class Messages(SQLModel, table=True):
    """Modelo para los mensajes con todos los metadatos."""
    message_id: Optional[str] = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    session_id: str = Field(index=True)
    user_id: UUID = Field(foreign_key="users.id")
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sender: str  # 'user' o 'system'
    message_length: int
    word_count: int
    
    user: Users = Relationship(back_populates="messages")
