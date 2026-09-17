from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin


class ExcelExerciseTestResult(UUIDPrimaryKeyMixin, Base):
    """Per-check-cell pass/fail detail for one Excel ExerciseAttempt — mirrors
    SqlExerciseTestResult/PythonExerciseTestResult exactly. The attempt
    itself (score, status, submitted workbook JSON) already lives on the
    existing `ExerciseAttempt` row; this only adds the per-cell breakdown
    feedback shown after a submission (and later, on Question Review)."""

    __tablename__ = "excel_exercise_test_results"

    attempt_id: Mapped[str] = mapped_column(ForeignKey("exercise_attempts.id", ondelete="CASCADE"), index=True)
    test_name: Mapped[str] = mapped_column(String(200))
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    passed: Mapped[bool] = mapped_column(Boolean)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
