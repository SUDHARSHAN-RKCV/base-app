# seed_user.py

from app import create_app
from app.models import db, User
from werkzeug.security import generate_password_hash
import uuid

app = create_app()

def seed_user():
    with app.app_context():

        # Check if user already exists
        existing_user = User.query.filter_by(email="user1@mail.com").first()

        if existing_user:
            print("User already exists.")
            return

        # Create new user
        new_user = User(
            user_id=uuid.uuid4(),
            email="user1@mail.com",
            password=generate_password_hash("passq123"),
            role="admin",
            is_active=True
        )

        db.session.add(new_user)
        db.session.commit()

        print("Admin user created successfully.")

if __name__ == "__main__":
    seed_user()