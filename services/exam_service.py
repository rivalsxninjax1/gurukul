from database.connection import get_session
from models.exam import Exam, ExamSubject, StudentResult
from models.student import Student
import logging

logger = logging.getLogger(__name__)


# ── Exam CRUD ─────────────────────────────────────────────────────────────────

def get_all_exams() -> list:
    session = get_session()
    exams = session.query(Exam).order_by(Exam.created_at.desc()).all()
    result = [{"id": e.id, "name": e.name,
               "subject_count": len(e.subjects)} for e in exams]
    session.close()
    return result


def create_exam(name: str) -> int:
    session = get_session()
    e = Exam(name=name)
    session.add(e)
    session.commit()
    eid = e.id
    session.close()
    return eid


def delete_exam(exam_id: int):
    session = get_session()
    e = session.query(Exam).get(exam_id)
    if e:
        session.delete(e)
        session.commit()
    session.close()


# ── Subject CRUD ──────────────────────────────────────────────────────────────

def get_subjects_for_exam(exam_id: int) -> list:
    session = get_session()
    subs = session.query(ExamSubject).filter_by(exam_id=exam_id).all()
    result = [{
        "id":           s.id,
        "subject_name": s.subject_name,
        "full_marks":   s.full_marks,
        "pass_marks":   s.pass_marks,
    } for s in subs]
    session.close()
    return result


def add_subject(exam_id: int, subject_name: str,
                full_marks: float, pass_marks: float) -> int:
    session = get_session()
    s = ExamSubject(
        exam_id      = exam_id,
        subject_name = subject_name,
        full_marks   = full_marks,
        pass_marks   = pass_marks,
    )
    session.add(s)
    session.commit()
    sid = s.id
    session.close()
    return sid


def delete_subject(subject_id: int):
    session = get_session()
    s = session.query(ExamSubject).get(subject_id)
    if s:
        session.delete(s)
        session.commit()
    session.close()


# ── Results ───────────────────────────────────────────────────────────────────

def save_result(student_id: int, exam_id: int,
                subject_id: int, marks: float):
    session = get_session()
    existing = session.query(StudentResult).filter_by(
        student_id=student_id,
        exam_id=exam_id,
        subject_id=subject_id
    ).first()
    if existing:
        existing.marks = marks
    else:
        session.add(StudentResult(
            student_id = student_id,
            exam_id    = exam_id,
            subject_id = subject_id,
            marks      = marks,
        ))
    session.commit()
    session.close()


def get_results_for_student(student_id: int) -> list:
    """Returns grouped results by exam."""
    session = get_session()
    exams = session.query(Exam).all()
    output = []
    for exam in exams:
        subjects_data = []
        total_full   = 0
        total_scored = 0
        has_any      = False
        for sub in exam.subjects:
            res = session.query(StudentResult).filter_by(
                student_id=student_id,
                exam_id=exam.id,
                subject_id=sub.id
            ).first()
            marks = res.marks if res else None
            passed = (marks >= sub.pass_marks) if marks is not None else None
            subjects_data.append({
                "subject":    sub.subject_name,
                "full":       sub.full_marks,
                "pass":       sub.pass_marks,
                "marks":      marks,
                "passed":     passed,
            })
            if marks is not None:
                has_any = True
                total_full   += sub.full_marks
                total_scored += marks

        if has_any or exam.subjects:
            pct = (round(total_scored / total_full * 100, 1)
                   if total_full > 0 else 0)
            output.append({
                "exam_id":  exam.id,
                "exam":     exam.name,
                "subjects": subjects_data,
                "total_full":   total_full,
                "total_scored": total_scored,
                "percentage":   pct,
                "has_results":  has_any,
            })
    session.close()
    return output