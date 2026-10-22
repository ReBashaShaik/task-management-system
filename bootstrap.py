"""Create the configured admin account once, if bootstrap credentials are set."""
from config import settings
from database import SessionLocal
from models import User
from utils.security import hash_password


def create_bootstrap_admin():
    if not settings.bootstrap_admin_email or not settings.bootstrap_admin_password:
        print("Admin bootstrap skipped: set both BOOTSTRAP_ADMIN values to create one.")
        return
    with SessionLocal() as db:
        existing = db.query(User).filter(User.email == settings.bootstrap_admin_email).first()
        if existing:
            print("Bootstrap admin already exists.")
            return
        admin = User(name="Administrator", email=settings.bootstrap_admin_email,
                     hashed_password=hash_password(settings.bootstrap_admin_password), role="admin")
        db.add(admin)
        db.commit()
        print("Bootstrap admin created.")


if __name__ == "__main__":
    create_bootstrap_admin()
