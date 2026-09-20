from app.models import GradeBand


def find_overlapping_band(school_id: int, min_pct: float, max_pct: float, exclude_id: int | None = None):
    """Returns the first existing band whose range overlaps [min_pct, max_pct],
    or None. Used to keep the grading scale unambiguous — every percentage
    must map to exactly one grade."""
    query = GradeBand.query.filter_by(school_id=school_id)
    if exclude_id:
        query = query.filter(GradeBand.id != exclude_id)
    for band in query.all():
        if min_pct <= band.max_percentage and max_pct >= band.min_percentage:
            return band
    return None


def grade_for_percentage(school_id: int, percentage: float) -> str | None:
    band = GradeBand.query.filter(
        GradeBand.school_id == school_id,
        GradeBand.min_percentage <= percentage,
        GradeBand.max_percentage >= percentage,
    ).first()
    return band.grade if band else None
