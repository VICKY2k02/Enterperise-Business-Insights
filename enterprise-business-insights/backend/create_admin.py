
from getpass import getpass

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.utils.security import hash_password


def main():
    db: Session = SessionLocal()

    try:
        # Do not accidentally create multiple initial Admin accounts.
        existing_admin = (
            db.query(User)
            .filter(User.role == UserRole.ADMIN)
            .first()
        )

        if existing_admin:
            print("An Admin account already exists.")
            print("Use the existing account or ask an Admin to manage users.")
            return

        full_name = input("Enter Admin full name: ").strip()
        email = input("Enter Admin email: ").strip().lower()

        if not full_name or not email:
            print("Name and email are required.")
            return

        password = getpass("Create Admin password (minimum 12 characters): ")
        confirm_password = getpass("Confirm Admin password: ")

        if len(password) < 6:
            print("Password must contain at least 6 characters.")
            return

        if password != confirm_password:
            print("Passwords do not match.")
            return

        existing_user = db.query(User).filter(User.email == email).first()

        if existing_user:
            print("This email already belongs to a user.")
            return

        admin = User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
            is_enabled=True,
        )

        db.add(admin)
        db.commit()

        print("\nAdmin account created successfully.")
        print(f"Email: {admin.email}")
        print(f"Role: {admin.role.value}")
        print("You can now log in through the API.")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
