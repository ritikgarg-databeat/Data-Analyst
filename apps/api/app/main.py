from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.routers import (
    ai,
    analytics_cases,
    assessments,
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
        "API for Personal Data Analyst Lab — a local-first Data Analyst learning & practice platform."
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
api_v1.include_router(users.router)
api_v1.include_router(domains.router)
api_v1.include_router(modules.router)
api_v1.include_router(lessons.router)
api_v1.include_router(skills.router)
api_v1.include_router(progress.router)
api_v1.include_router(exercises.router)
api_v1.include_router(assessments.router)
api_v1.include_router(datasets.router)
api_v1.include_router(tags.router)
api_v1.include_router(search.router)
api_v1.include_router(recommendations.router)
api_v1.include_router(sql.router)
api_v1.include_router(python_lab.router)
api_v1.include_router(kaggle.router)
api_v1.include_router(eda.router)
api_v1.include_router(eda_workspaces.router)
api_v1.include_router(charts.router)
api_v1.include_router(projects.router)
api_v1.include_router(statistics.router)
api_v1.include_router(experiments.router)
api_v1.include_router(metrics.router)
api_v1.include_router(analytics_cases.router)
api_v1.include_router(dbt.router)
api_v1.include_router(data_quality.router)
api_v1.include_router(data_modeling.router)
api_v1.include_router(cases.router)
api_v1.include_router(findings.router)
api_v1.include_router(excel_lab.router)
api_v1.include_router(interviews.router)
api_v1.include_router(interview_questions.router)
api_v1.include_router(interview_questions.bookmarks_router)
api_v1.include_router(interview_questions.notes_router)
api_v1.include_router(interview_readiness.router)
api_v1.include_router(ai.router)
api_v1.include_router(career.router)
api_v1.include_router(jobs.router)
api_v1.include_router(resume.router)
api_v1.include_router(portfolio.router)
api_v1.include_router(platform.router)

app.include_router(api_v1)
