from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.agents import Interview
from app.models.student import Student
from app.schemas.agents import (
    InterviewAnswerRequest,
    InterviewAnswerResponse,
    InterviewDetail,
    InterviewHistoryItem,
    InterviewPrepRequest,
    InterviewPrepResponse,
    InterviewResult,
    InterviewStartRequest,
    InterviewStartResponse,
)
from app.services.agent_services import (
    answer_interview,
    interview_detail,
    interview_result,
    next_interview_question,
    prepare_interview_questions,
    start_interview,
)
from app.services.auth_service import get_current_student

router = APIRouter(prefix="/interview", tags=["Interview Agent"])


@router.post("/prepare", response_model=InterviewPrepResponse)
def prepare(
    data: InterviewPrepRequest,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    return prepare_interview_questions(db, current_student, data)


@router.post("/questions", response_model=InterviewPrepResponse)
def questions(
    data: InterviewPrepRequest,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    return prepare_interview_questions(db, current_student, data)


@router.post("/start", response_model=InterviewStartResponse)
def start(data: InterviewStartRequest, current_student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    return start_interview(db, current_student, data)


@router.get("", response_model=list[InterviewHistoryItem])
def history(current_student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    records = db.query(Interview).filter(Interview.student_id == current_student.student_id).order_by(Interview.created_at.desc()).all()
    return [interview_detail(db, current_student, item.interview_id) for item in records]


@router.get("/{interview_id}", response_model=InterviewDetail)
def detail(interview_id: int, current_student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    return interview_detail(db, current_student, interview_id)


@router.post("/{interview_id}/answer", response_model=InterviewAnswerResponse)
def answer(interview_id: int, data: InterviewAnswerRequest, current_student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    return answer_interview(db, current_student, interview_id, data.answer)


@router.post("/{interview_id}/next", response_model=InterviewStartResponse)
def next_question(interview_id: int, current_student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    return next_interview_question(db, current_student, interview_id)


@router.get("/{interview_id}/result", response_model=InterviewResult)
def result(interview_id: int, current_student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    return interview_result(db, current_student, interview_id)


@router.get("/{interview_id}/report", response_model=InterviewResult)
def report(interview_id: int, current_student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    return interview_result(db, current_student, interview_id)

