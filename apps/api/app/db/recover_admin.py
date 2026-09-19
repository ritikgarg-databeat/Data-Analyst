"""Local emergency administrator password recovery.

Run in a trusted terminal: uv run --project apps/api python -m app.db.recover_admin
"""

import argparse
import getpass

from sqlalchemy import select, update

from app.core.database import SessionLocal
from app.core.security import hash_password, utc_now, validate_password
from app.models.auth import AuthSession
from app.models.enums import UserRole
from app.models.user import User


def recover() -> None:
    with SessionLocal() as db:
        admins = db.scalars(select(User).where(User.role == UserRole.ADMIN).order_by(User.created_at)).all()
        if not admins:
            raise RuntimeError("No administrator exists. Run app.db.bootstrap_admin first.")
        if len(admins) == 1:
            admin = admins[0]
        else:
            email = input("Administrator email: ").strip().lower()
            selected = next((row for row in admins if row.email == email), None)
            if not selected:
                raise RuntimeError("Administrator not found.")
            admin = selected
        password = getpass.getpass("New password: ")
        confirmation = getpass.getpass("Confirm new password: ")
        if password != confirmation:
            raise RuntimeError("Passwords do not match.")
        validate_password(password, admin.email)
        admin.password_hash = hash_password(password)
        admin.must_change_password = False
        admin.temporary_password_expires_at = None
        db.execute(update(AuthSession).where(AuthSession.user_id == admin.id).values(revoked_at=utc_now()))
        db.commit()
        print(f"Password replaced and sessions revoked for {admin.email}.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Securely replace a local administrator password and revoke its sessions."
    )
    parser.parse_args()
    recover()


if __name__ == "__main__":
    main()
