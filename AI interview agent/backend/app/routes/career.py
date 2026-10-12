from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.agents import CareerChat
from app.models.student import Student
from app.schemas.agents import CareerChatHistoryItem, CareerChatRequest, CareerChatResponse
from app.services.agent_services import chat_career_assistant
from app.services.auth_service import get_current_student

router = APIRouter(prefix="/career", tags=["Career Assistant"])
assistant_router = APIRouter(prefix="/career-assistant", tags=["Career Assistant"])


@router.post("/chat", response_model=CareerChatResponse)
def chat(
    data: CareerChatRequest,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    result = chat_career_assistant(db, current_student, data.message, data.job_id)
    record = CareerChat(
        student_id=current_student.student_id,
        message=data.message,
        response=result["response"],
        routed_agent=result["routed_agent"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {
        "chat_id": record.chat_id,
        "routed_agent": result["routed_agent"],
        "response": result["response"],
        "context_used": result.get("context_used", []),
        "suggestions": result.get("suggestions", []),
    }


@router.get("/history", response_model=List[CareerChatHistoryItem])
def history(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    return (
        db.query(CareerChat)
        .filter(CareerChat.student_id == current_student.student_id)
        .order_by(CareerChat.created_at.desc())
        .all()
    )


@assistant_router.post("/chat", response_model=CareerChatResponse)
def assistant_chat(
    data: CareerChatRequest,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    return chat(data, current_student, db)


@assistant_router.get("/history", response_model=List[CareerChatHistoryItem])
def assistant_history(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    return history(current_student, db)
