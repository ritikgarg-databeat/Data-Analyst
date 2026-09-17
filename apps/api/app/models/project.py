from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import CaseAttemptStatus, CaseCategory, ProjectArtifactType


class ProjectTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A substantial, multi-milestone project scenario (Phase 8, spec
    sections 29-30, 57) — content-authored and synced from
    `content/projects/*.yaml`, exactly like Case. Starting one instantiates
    a `Project` row plus its `ProjectMilestone` rows from `milestones`."""

    __tablename__ = "project_templates"

    slug: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[CaseCategory] = mapped_column(Enum(CaseCategory, native_enum=False, length=30))
    business_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    objective: Mapped[str] = mapped_column(Text)
    requirements: Mapped[list] = mapped_column(JSON, default=list)
    suggested_datasets: Mapped[list] = mapped_column(JSON, default=list)
    milestones: Mapped[list] = mapped_column(JSON, default=list)  # [{title, description}], in order
    required_skills: Mapped[list] = mapped_column(JSON, default=list)
    rubric: Mapped[list] = mapped_column(JSON, default=list)  # same shape as Case.rubric
    learning_objectives: Mapped[list] = mapped_column(JSON, default=list)
    estimated_hours: Mapped[float | None] = mapped_column(nullable=True)
    tags: Mapped[list] = mapped_column(JSON, default=list)

    version: Mapped[int] = mapped_column(Integer, default=1)
    content_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    projects: Mapped[list["Project"]] = relationship(back_populates="template")


class Project(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A project — either a free-form shell started from a dataset (Phase 5's
    original "Create Project from Dataset", `template_id` left null) or an
    instance of a curated `ProjectTemplate` (Phase 8). Extended in place
    rather than replaced, so every Phase 5 project row/route keeps working.

    `documentation` and `presentation` are JSON blobs (the 9 named
    documentation sections / slide deck, spec sections 34 & 40) — read and
    written as a whole from one editor, the same reasoning already applied
    to `Chart.config` and `DataModelTable.columns`."""

    __tablename__ = "projects"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    dataset_id: Mapped[str | None] = mapped_column(
        ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    template_id: Mapped[str | None] = mapped_column(
        ForeignKey("project_templates.id", ondelete="SET NULL"), nullable=True, index=True
    )
    data_model_id: Mapped[str | None] = mapped_column(
        ForeignKey("data_models.id", ondelete="SET NULL"), nullable=True, index=True
    )

    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[CaseAttemptStatus] = mapped_column(
        Enum(CaseAttemptStatus, native_enum=False, length=20), default=CaseAttemptStatus.NOT_STARTED
    )

    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    # NOT NULL JSON columns added to an already-populated table need a
    # server_default so existing rows get a real value (see the migration) —
    # kept here too (not just historically in the migration) so the model and
    # the live schema never drift; `default=` is still what the ORM actually
    # uses for new inserts.
    requirements: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    dbt_model_refs: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")

    documentation: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")
    presentation: Mapped[list] = mapped_column(JSON, default=list, server_default="[]")
    rubric_selections: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")
    score: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    reflection: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    template: Mapped["ProjectTemplate | None"] = relationship(back_populates="projects")
    milestones: Mapped[list["ProjectMilestone"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", order_by="ProjectMilestone.display_order"
    )
    artifacts: Mapped[list["ProjectArtifact"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", order_by="ProjectArtifact.created_at"
    )
    project_datasets: Mapped[list["ProjectDataset"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class ProjectMilestone(UUIDPrimaryKeyMixin, Base):
    """One milestone within a project (spec section 31) — seeded from the
    template's `milestones` list when the project is created; a free-form
    (non-template) project simply has none."""

    __tablename__ = "project_milestones"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_completed: Mapped[bool] = mapped_column(default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="milestones")


class ProjectArtifact(UUIDPrimaryKeyMixin, Base):
    """A linked deliverable (spec section 33) — SQL/Python/chart/model
    artifacts point back at a real row elsewhere (see
    ProjectArtifactType's docstring); NOTE artifacts (markdown, a CSV
    export, a diagram description) carry their content directly in
    `snapshot` since there's no other row to link to."""

    __tablename__ = "project_artifacts"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    artifact_type: Mapped[ProjectArtifactType] = mapped_column(
        Enum(ProjectArtifactType, native_enum=False, length=20)
    )
    ref_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    label: Mapped[str] = mapped_column(String(300))
    snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="artifacts")


class ProjectDataset(UUIDPrimaryKeyMixin, Base):
    """Which datasets a project actually uses, and why (spec section 36) —
    a join row rather than reusing ProjectArtifact, matching this
    codebase's existing dataset-join-table precedent (LessonDataset)."""

    __tablename__ = "project_datasets"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="project_datasets")
