"""Idempotently convert the legacy user into the initial local administrator."""

import argparse
import logging
import shutil
from pathlib import Path

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.security import hash_password, normalize_email, validate_password
from app.models.ai import AISettings
from app.models.dataset import Dataset
from app.models.enums import AccountStatus, DatasetSourceType, UserRole
from app.models.sql_lab import SqlTable
from app.models.user import User

logger = logging.getLogger(__name__)
REPO_ROOT = Path(__file__).resolve().parents[4]


def bootstrap() -> User:
    settings = get_settings()
    if len(settings.auth_jwt_secret.encode()) < 32:
        raise RuntimeError("AUTH_JWT_SECRET must contain at least 32 bytes.")
    email = normalize_email(settings.initial_admin_email)
    with SessionLocal() as db:
        admin = db.scalar(select(User).where(User.role == UserRole.ADMIN).order_by(User.created_at))
        if admin:
            logger.info("An administrator already exists; credentials were left unchanged.")
        else:
            if not settings.initial_admin_password:
                raise RuntimeError("INITIAL_ADMIN_PASSWORD is required for first-time bootstrap.")
            validate_password(settings.initial_admin_password, email)
            admin = db.scalar(select(User).order_by(User.created_at))
            if admin is None:
                admin = User(name="Administrator", email=email)
                db.add(admin)
                db.flush()
            admin.email = email
            admin.password_hash = hash_password(settings.initial_admin_password)
            admin.role = UserRole.ADMIN
            admin.status = AccountStatus.ACTIVE
            admin.must_change_password = True
            db.flush()
        ai = db.scalar(select(AISettings).where(AISettings.user_id == admin.id))
        if not ai:
            db.add(
                AISettings(
                    user_id=admin.id,
                    enabled=True,
                    admin_access_enabled=True,
                    admin_daily_request_limit=settings.auth_default_ai_quota,
                )
            )
        else:
            ai.admin_access_enabled = True
        # Anything outside data/sample is a legacy private import. Preserve IDs
        # and claim it for the converted administrator.
        user_root = REPO_ROOT / "data" / "users" / admin.id
        user_root.mkdir(parents=True, exist_ok=True)
        for dataset in db.scalars(select(Dataset)).all():
            paths = [dataset.file_path, *(table.file_path for table in dataset.tables)]
            is_private = (
                dataset.source_type == DatasetSourceType.KAGGLE
                or dataset.source == "local upload"
                or any(path and not path.replace("\\", "/").startswith("data/sample/") for path in paths)
            )
            if not is_private:
                continue
            dataset.owner_user_id = admin.id
            for kind in ("raw", "processed", "datasets"):
                source = REPO_ROOT / "data" / kind / dataset.slug
                target = user_root / kind / dataset.slug
                if source.exists() and not target.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(source), str(target))
                old_prefix = f"data/{kind}/{dataset.slug}"
                new_prefix = f"data/users/{admin.id}/{kind}/{dataset.slug}"
                if dataset.file_path:
                    dataset.file_path = dataset.file_path.replace("\\", "/").replace(old_prefix, new_prefix)
                for dataset_table in dataset.tables:
                    dataset_table.file_path = dataset_table.file_path.replace("\\", "/").replace(
                        old_prefix, new_prefix
                    )
                for sql_table in db.scalars(
                    select(SqlTable).where(SqlTable.dataset_id == dataset.id)
                ).all():
                    sql_table.file_path = sql_table.file_path.replace("\\", "/").replace(
                        old_prefix, new_prefix
                    )
        warehouse = REPO_ROOT / "data" / "warehouse" / "dev.duckdb"
        private_warehouse = user_root / "warehouse" / "dev.duckdb"
        if warehouse.exists() and not private_warehouse.exists():
            private_warehouse.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(warehouse), str(private_warehouse))
        dbt_target = REPO_ROOT / "dbt" / "target"
        private_target = user_root / "dbt-target"
        if dbt_target.exists() and not private_target.exists():
            shutil.move(str(dbt_target), str(private_target))
        db.commit()
        db.refresh(admin)
        logger.info("Initial administrator bootstrapped without changing the legacy user id.")
        return admin


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert the legacy local account into the initial administrator."
    )
    parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    bootstrap()


if __name__ == "__main__":
    main()
