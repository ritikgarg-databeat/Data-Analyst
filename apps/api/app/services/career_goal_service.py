"""Career Goal Planner (Phase 11, spec section 26). Marking a goal COMPLETED
writes a CareerMilestone directly (rather than via the sync-on-read pattern
used for cross-phase events) since goal completion is decided entirely
within this same service, with no other phase's commit path involved."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.career import CareerGoal, CareerMilestone
from app.models.enums import CareerGoalStatus, CareerMilestoneType
from app.schemas.career import CareerGoalSchema, CreateCareerGoalRequest, UpdateCareerGoalRequest


class CareerGoalService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_goals(self, user_id: str) -> list[CareerGoalSchema]:
        rows = self.db.execute(
            select(CareerGoal).where(CareerGoal.user_id == user_id).order_by(CareerGoal.created_at.desc())
        ).scalars().all()
        return [CareerGoalSchema.model_validate(g) for g in rows]

    def create_goal(self, user_id: str, payload: CreateCareerGoalRequest) -> CareerGoalSchema:
        goal = CareerGoal(
            user_id=user_id,
            goal_type=payload.goal_type,
            title=payload.title,
            description=payload.description,
            target_value=payload.target_value,
            target_date=payload.target_date,
        )
        self.db.add(goal)
        self.db.commit()
        self.db.refresh(goal)
        return CareerGoalSchema.model_validate(goal)

    def _get_owned(self, user_id: str, goal_id: str) -> CareerGoal:
        goal = self.db.get(CareerGoal, goal_id)
        if goal is None or goal.user_id != user_id:
            raise NotFoundError("Career goal was not found.")
        return goal

    def update_goal(self, user_id: str, goal_id: str, payload: UpdateCareerGoalRequest) -> CareerGoalSchema:
        goal = self._get_owned(user_id, goal_id)
        was_active = goal.status == CareerGoalStatus.ACTIVE

        for field in ("title", "description", "target_value", "current_value", "target_date", "status"):
            value = getattr(payload, field)
            if value is not None:
                setattr(goal, field, value)

        if was_active and goal.status == CareerGoalStatus.COMPLETED:
            self.db.add(
                CareerMilestone(
                    user_id=user_id,
                    milestone_type=CareerMilestoneType.GOAL_COMPLETED,
                    title=f"Completed goal: {goal.title}",
                    related_goal_id=goal.id,
                )
            )

        self.db.commit()
        self.db.refresh(goal)
        return CareerGoalSchema.model_validate(goal)

    def delete_goal(self, user_id: str, goal_id: str) -> None:
        goal = self._get_owned(user_id, goal_id)
        self.db.delete(goal)
        self.db.commit()
