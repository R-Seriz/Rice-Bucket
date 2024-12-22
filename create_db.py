from app import db, FileEntry, app

with app.app_context():
    db.create_all()