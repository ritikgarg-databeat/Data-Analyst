from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.db.bootstrap_admin as bootstrap_module
from app.core.config import Settings
from app.core.database import Base
from app.core.security import hash_password, verify_password
from app.models.ai import AISettings
from app.models.enums import UserRole
from app.models.user import User


def test_bootstrap_preserves_legacy_id_and_never_overwrites_changed_credentials(
    monkeypatch, tmp_path: Path
) -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    local_session = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)
    try:
        with local_session() as db:
            legacy = User(name="Analyst", email="legacy@example.com", password_hash="!unusable")
            db.add(legacy)
            db.commit()
            legacy_id = legacy.id

        settings = Settings(
            auth_jwt_secret="z" * 48,
            initial_admin_email="admin@dataanalyst.com",
            initial_admin_password="admin@dataanalyst",
        )
        monkeypatch.setattr(bootstrap_module, "SessionLocal", local_session)
        monkeypatch.setattr(bootstrap_module, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(bootstrap_module, "get_settings", lambda: settings)

        first = bootstrap_module.bootstrap()
        assert first.id == legacy_id
        assert first.role == UserRole.ADMIN
        assert first.must_change_password is True
        assert verify_password("admin@dataanalyst", first.password_hash)

        changed_hash = hash_password("changed admin password 456")
        with local_session() as db:
            admin = db.get(User, legacy_id)
            assert admin is not None
            admin.email = "changed-admin@example.com"
            admin.password_hash = changed_hash
            admin.must_change_password = False
            db.commit()

        second = bootstrap_module.bootstrap()
        assert second.id == legacy_id
        assert second.email == "changed-admin@example.com"
        assert second.password_hash == changed_hash
        assert second.must_change_password is False
        with local_session() as db:
            ai_settings = db.scalar(select(AISettings).where(AISettings.user_id == legacy_id))
            assert ai_settings is not None
            assert ai_settings.admin_access_enabled is True
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
