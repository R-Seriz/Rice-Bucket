from werkzeug.security import generate_password_hash, check_password_hash

from app import app, User, db

def hash_existing_db():
    """
    Functionality to securely hash existing DB passworrds
    """
    with app.app_context():
        user_list = User.query.all()
        for user in user_list:
            if not user.password.startswith('argon2:'):
                # Most likely not a hashed password. Update it.
                user.password = generate_password_hash(user.password, method='argon2')
        db.session.commit()