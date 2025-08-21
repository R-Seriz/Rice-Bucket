from werkzeug.security import generate_password_hash, check_password_hash

from app import app, User, db

def hash_existing_db():
    """
    Functionality to securely hash existing DB passworrds
    """
    with app.app_context():
        user_list = User.query.all()
        for user in user_list:
            if not user.password.startswith('scrypt:'):
                # Most likely not a hashed password. Update it.
                user.password = generate_password_hash(user.password, method='scrypt')
        db.session.commit()

def db_frorm_csv(filename: str):
    """
    :param filename: name of file in same directory as script to format

    Utility function for re-formatting user database information from a csv file.
    NOTE: Does not clear the database.
    """
    import csv
    with app.app_context():
        with open(filename, 'r', encoding='utf-8') as rice:
            reader = csv.reader(rice)
            for row in reader:
                username = row[1]
                password = row[2]
                email = row[3]
                # Check if user already exists
                if not User.query.filter_by(username=username).first():
                    new_user = User(username=username, password=password, email=email)
                    db.session.add(new_user)
            db.session.commit()