"""
Results are never persisted as their own table — every result is recomputed
from Mark rows at request time. This is a deliberate trade-off: it costs a
bit more computation per view, but makes "a result silently disagreeing with
the marks it's supposed to reflect" structurally impossible (there's nothing
stored to go stale).

Overall pass/fail requires passing EVERY subject with a recorded mark, not
just clearing an aggregate percentage — this matches how real school report
cards work (failing one subject fails the exam overall) and is the same
principle the spec's Result Calculation section describes.
"""
from app.models import Mark, Student
from app.models.enums import StudentStatus
from app.services.grading_service import grade_for_percentage


def compute_student_result(exam, student_id: int) -> dict:
    exam_subjects = exam.exam_subjects
    marks_by_es = {
        m.exam_subject_id: m
        for m in Mark.query.filter(
            Mark.exam_subject_id.in_([es.id for es in exam_subjects]), Mark.student_id == student_id
        ).all()
    }

    subjects = []
    total_max = 0
    total_obtained = 0.0
    overall_pass = True
    any_marks = False

    for es in exam_subjects:
        mark = marks_by_es.get(es.id)
        obtained = float(mark.obtained_marks) if mark else None
        passed = (obtained >= es.passing_marks) if obtained is not None else None

        if obtained is not None:
            any_marks = True
            total_max += es.max_marks
            total_obtained += obtained
            if not passed:
                overall_pass = False

        subjects.append({
            "subject": es.subject, "exam_subject": es, "max_marks": es.max_marks,
            "passing_marks": es.passing_marks, "obtained_marks": obtained, "passed": passed,
        })

    percentage = round(total_obtained / total_max * 100, 2) if total_max else None
    grade = grade_for_percentage(exam.school_id, percentage) if percentage is not None else None

    return {
        "subjects": subjects,
        "total_max": total_max,
        "total_obtained": total_obtained,
        "percentage": percentage,
        "grade": grade,
        "overall_pass": overall_pass if any_marks else None,  # None = nothing marked yet, not "failed"
        "has_any_marks": any_marks,
        "complete": bool(subjects) and all(s["obtained_marks"] is not None for s in subjects),
    }


def compute_class_ranking(exam) -> list[dict]:
    """Competition ranking (1-2-2-4 style): tied percentages share a rank, and
    the next distinct value skips ahead by the number tied.

    Known limitation: ranking is by percentage, not raw total, so a student
    marked in only a subset of subjects is compared on equal footing with one
    marked in all of them. This is simpler than trying to only compare
    students with an identical set of marked subjects, but means a partially-
    entered result can rank misleadingly high until all marks are in — worth
    treating class rankings as provisional until every subject is fully marked.
    """
    students = Student.query.filter_by(
        school_id=exam.school_id, current_class_id=exam.class_id, status=StudentStatus.ACTIVE
    ).all()

    results = []
    for student in students:
        result = compute_student_result(exam, student.id)
        if result["has_any_marks"]:
            results.append({"student": student, **result})

    results.sort(key=lambda r: r["percentage"], reverse=True)

    rank = 0
    previous_percentage = None
    for i, r in enumerate(results):
        if r["percentage"] != previous_percentage:
            rank = i + 1
        r["rank"] = rank
        previous_percentage = r["percentage"]

    return results
