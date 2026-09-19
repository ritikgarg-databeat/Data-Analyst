from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.dependencies.current_user import get_current_user
from app.routers import (
    admin,
    ai,
    analytics_cases,
    assessments,
    auth,
    career,
    cases,
    charts,
    data_modeling,
    data_quality,
    datasets,
    dbt,
    domains,
    eda,
    eda_workspaces,
    excel_lab,
    exercises,
    experiments,
    findings,
    health,
    interview_questions,
    interview_readiness,
    interviews,
    jobs,
    kaggle,
    lessons,
    metrics,
    modules,
    platform,
    portfolio,
    progress,
    projects,
    python_lab,
    recommendations,
    resume,
    search,
    skills,
    sql,
    statistics,
    tags,
    users,
)

settings = get_settings()
configure_logging()

# Abandoned Python Lab runtimes (e.g. the API crashed with containers still
# alive) are swept opportunistically instead of on a startup hook — see
# `python_lab.router`'s list_runtimes/create_runtime, which call
# PythonExecutionService.reap_idle_runtimes() on every request. A startup
# hook would need its own DB session independent of the request-scoped
# `get_db` dependency (which tests override; a hook can't be), risking a
# real-Postgres connection attempt in contexts — like this test suite —
# where only the overridden dependency is ever meant to be used.

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "API for Data Lab — an AI-powered personal data learning and practice platform."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)

register_exception_handlers(app)

api_v1 = APIRouter(prefix=settings.api_v1_prefix)
api_v1.include_router(health.router)
api_v1.include_router(auth.router)

protected = APIRouter(dependencies=[Depends(get_current_user)])
for protected_router in (
    users.router,
    domains.router,
    modules.router,
    lessons.router,
    skills.router,
    progress.router,
    exercises.router,
    assessments.router,
    datasets.router,
    tags.router,
    search.router,
    recommendations.router,
    sql.router,
    python_lab.router,
    kaggle.router,
    eda.router,
    eda_workspaces.router,
    charts.router,
    projects.router,
    statistics.router,
    experiments.router,
    metrics.router,
    analytics_cases.router,
    dbt.router,
    data_quality.router,
    data_modeling.router,
    cases.router,
    findings.router,
    excel_lab.router,
    interviews.router,
    interview_questions.router,
    interview_questions.bookmarks_router,
    interview_questions.notes_router,
    interview_readiness.router,
    ai.router,
    career.router,
    jobs.router,
    resume.router,
    portfolio.router,
    platform.router,
):
    protected.include_router(protected_router)
api_v1.include_router(protected)
api_v1.include_router(admin.router)

app.include_router(api_v1)
