"""Create the configured admin, or reset its password when explicitly asked."""
import argparse

from config import settings
from database import SessionLocal
from models import User
from utils.security import hash_password


def create_bootstrap_admin(reset_password: bool = False):
    """Create the admin if missing; reset its password only on explicit request."""
    if not settings.bootstrap_admin_email or not settings.bootstrap_admin_password:
        print("Admin bootstrap skipped: set both BOOTSTRAP_ADMIN values to create one.")
        return

    with SessionLocal() as db:
        existing = db.query(User).filter(User.email == settings.bootstrap_admin_email).first()

        if existing:
            if reset_password:
                if existing.role != "admin":
                    raise ValueError(
                        "The configured bootstrap email belongs to a non-admin user. "
                        "Choose the correct admin email in .env before resetting."
                    )
                existing.hashed_password = hash_password(settings.bootstrap_admin_password)
                db.commit()
                print("Bootstrap admin password reset successfully.")
                return

            print("Bootstrap admin already exists.")
            return

        admin = User(
            name="Administrator",
            email=settings.bootstrap_admin_email,
            hashed_password=hash_password(settings.bootstrap_admin_password),
            role="admin",
        )
        db.add(admin)
        db.commit()
        print("Bootstrap admin created.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create or reset the configured bootstrap admin.")
    parser.add_argument(
        "--reset-password",
        action="store_true",
        help="replace the existing admin password with the BOOTSTRAP_ADMIN_PASSWORD value",
    )
    args = parser.parse_args()
    create_bootstrap_admin(reset_password=args.reset_password)
