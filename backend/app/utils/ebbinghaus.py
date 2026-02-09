"""Ebbinghaus forgetting curve review scheduling.

Review intervals in minutes:
- 20 minutes (1st review)
- 60 minutes (2nd review)
- 540 minutes (9 hours, 3rd review)
- 1440 minutes (1 day, 4th review)
- 2880 minutes (2 days, 5th review)
- 8640 minutes (6 days, 6th review)
- 44640 minutes (31 days, 7th review)
"""

from datetime import datetime, timedelta
from typing import Optional

# Ebbinghaus review intervals in minutes
REVIEW_INTERVALS = [20, 60, 540, 1440, 2880, 8640, 44640]


def calculate_next_review(
    consecutive_correct: int,
    is_correct: bool,
    last_review_at: Optional[datetime] = None,
) -> tuple[datetime, int]:
    """Calculate next review time based on Ebbinghaus forgetting curve.

    Args:
        consecutive_correct: Number of consecutive correct reviews
        is_correct: Whether the last review was correct
        last_review_at: Last review time (defaults to now)

    Returns:
        Tuple of (next_review_time, new_consecutive_correct)

    Examples:
        >>> calculate_next_review(0, True)
        (datetime + 20 minutes, 1)
        
        >>> calculate_next_review(3, True)
        (datetime + 1440 minutes, 4)
        
        >>> calculate_next_review(2, False)
        (datetime + 20 minutes, 0)
    """
    if last_review_at is None:
        last_review_at = datetime.utcnow()

    # Reset consecutive count if incorrect
    if not is_correct:
        new_consecutive = 0
        interval_index = 0
    else:
        new_consecutive = consecutive_correct + 1
        # Cap at maximum interval
        interval_index = min(new_consecutive, len(REVIEW_INTERVALS)) - 1

    # Get interval in minutes
    interval_minutes = REVIEW_INTERVALS[interval_index]

    # Calculate next review time
    next_review = last_review_at + timedelta(minutes=interval_minutes)

    return next_review, new_consecutive


def calculate_mastery_level(
    correct_count: int,
    incorrect_count: int,
    consecutive_correct: int,
) -> int:
    """Calculate mastery level (0-100) based on review history.

    Args:
        correct_count: Total correct reviews
        incorrect_count: Total incorrect reviews
        consecutive_correct: Current consecutive correct streak

    Returns:
        Mastery level from 0 to 100

    Formula:
        - Base score from correct ratio: 50 * (correct / total)
        - Bonus for consecutive correct: up to 50 points
        - Penalty for consecutive incorrect
    """
    total_reviews = correct_count + incorrect_count

    if total_reviews == 0:
        return 0

    # Base score from correct ratio (0-50)
    correct_ratio = correct_count / total_reviews
    base_score = int(correct_ratio * 50)

    # Bonus for consecutive correct (0-50)
    # 5+ consecutive = 50 bonus
    consecutive_bonus = min(consecutive_correct, 5) * 10

    # Calculate final score
    mastery = base_score + consecutive_bonus

    # Cap at 100
    return min(mastery, 100)


def get_review_status(
    next_review_at: datetime,
    current_time: Optional[datetime] = None,
) -> str:
    """Get review status based on next review time.

    Args:
        next_review_at: Scheduled next review time
        current_time: Current time (defaults to now)

    Returns:
        Status: "due", "overdue", or "scheduled"
    """
    if current_time is None:
        current_time = datetime.utcnow()

    time_diff = (current_time - next_review_at).total_seconds()

    if time_diff >= 0:
        return "overdue"
    elif time_diff >= -3600:  # Within 1 hour
        return "due"
    else:
        return "scheduled"


def minutes_until_review(next_review_at: datetime, current_time: Optional[datetime] = None) -> int:
    """Calculate minutes until next review.

    Args:
        next_review_at: Scheduled next review time
        current_time: Current time (defaults to now)

    Returns:
        Minutes until review (negative if overdue)
    """
    if current_time is None:
        current_time = datetime.utcnow()

    time_diff = next_review_at - current_time
    return int(time_diff.total_seconds() / 60)
