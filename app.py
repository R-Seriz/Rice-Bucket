import os
import argparse
import hashlib
from urllib.parse import urlparse, parse_qs
from operator import itemgetter

from flask import Flask, flash, redirect, render_template, request, jsonify, url_for, send_from_directory, make_response
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
    UserMixin,
)
from dotenv import load_dotenv

load_dotenv()

UPLOAD_FOLDER = './uploads'
TEMPLATE_FOLDER = './pages'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'mp3', 'mp4'}

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, template_folder=TEMPLATE_FOLDER)
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")

db = SQLAlchemy(app)
with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=True)
    bio = db.Column(db.Text, default="")
    profile_pic = db.Column(db.String(120), default="default-pfp.png")

    files = db.relationship('FileEntry', back_populates='user')

class FileEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(100), nullable=False)
    project_year = db.Column(db.Integer, nullable=False)
    project_month = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True),
                           server_default=func.now())
    description = db.Column(db.String(2200), nullable=False)
    approved = db.Column(db.Boolean, default=False, nullable=False)
    filetype = db.Column(db.Integer, nullable=False) # 0:JPG, 1:PNG, 2:MP3, 3:MP4, 4:YT
    filename = db.Column(db.Text, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='files')

    def __repr__(self):
        return f'<FileEntry {self.filename}>'


class CommentEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    fileentry_id = db.Column(db.Integer, db.ForeignKey('file_entry.id'), nullable=False)
    fileentry = db.relationship('FileEntry', backref='comments')

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='comments')

    text = db.Column(db.String(500), nullable=False)

    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f'<CommentEntry {self.id}>'


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def home():
    return render_template('home.html', auth=current_user.is_authenticated)


@app.route('/about')
def about():
    return render_template('about.html', family_photos=[a for a in os.listdir('./static/assets/family') if
                                                        a.split('.')[-1].upper() == 'JPG'], auth=current_user.is_authenticated)


@app.route('/directory')
@login_required
def directory():
    files = FileEntry.query.all()
    print(files)
    return render_template('directory.html', files=files)

@app.route('/members')
@login_required
def members():
    profile_pic = current_user.profile_pic or "default-pfp.png"
    bio = current_user.bio or "This user hasn't written a bio yet."

    return render_template('members.html',
                           current_user=current_user,
                           currentUserProfilePic=profile_pic,
                           userBio=bio)

@app.route('/user-files/<username>')
def get_user_files(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    filetype_map = {0: "JPG", 1: "PNG", 2: "MP3", 3: "MP4", 4: "YT"}
    files = FileEntry.query.filter_by(user_id=user.id).all()
    return jsonify({
        'files': [
            {
                'title': f.title,
                'description': f.description,
                'filetype': filetype_map.get(f.filetype, f.filetype),
                'filename': f.filename,
                'project_year': f.project_year,
                'project_month': f.project_month,
                'author': username
            } for f in files
        ],
        'bio': user.bio or "",
        'profile_pic': user.profile_pic or "default-pfp.png"
    })


@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    # Handle JSON bio update
    if request.is_json:
        data = request.get_json()
        bio = data.get('bio')
        if bio is not None:
            current_user.bio = bio
            db.session.commit()
            return jsonify({'status': 'success'})

        return jsonify({'status': 'error', 'message': 'No bio provided'}), 400

    # Handle multipart/form-data profile_pic upload
    if 'profile_pic' in request.files:
        file = request.files['profile_pic']
        filename = secure_filename(file.filename)
        path = os.path.join('static', 'assets', 'pfps', filename)
        file.save(path)
        current_user.profile_pic = filename
        db.session.commit()
        return jsonify({'success': True, 'new_filename': filename})

    return jsonify({'status': 'error', 'message': 'Invalid request'}), 400

@app.route('/update-bio', methods=['POST'])
@login_required
def update_bio():
    data = request.get_json()
    bio = data.get('bio', '')

    current_user.bio = bio
    db.session.commit()

    return jsonify({'status': 'success'})

@app.route("/login", methods = ['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user_query = User.query.filter_by(username=username).first()

        if not user_query:
            return "No such username", 400

        if user_query.password != password:
            return "Wrong password", 400

        login_user(user_query)

        return redirect(url_for('home'))
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route('/feed')
@login_required
def member_feed():
    return render_template('feed.html')


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        print(request.form)
        if request.form['filetype'] in ["4"]: # Check if filetype is YT link (logic prepared for expansion)
            url_data = urlparse(request.form['youtube-link'])
            query = parse_qs(url_data.query)
            video = query["v"][0]
            db.session.add(FileEntry(user_id=current_user.id, project_year=request.form['year'],
                                     project_month=request.form['month'], title=request.form['title'],
                                     description=request.form['description'].replace('\\n','<br/>'),
                                     filetype=request.form['filetype'], filename=video))
            db.session.commit()

        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            db.session.add(FileEntry(user_id=current_user.id, project_year=request.form['year'],
                                     project_month=request.form['month'], title=request.form['title'],
                                     description=request.form['description'].replace('\\n','<br/>'),
                                     filetype=request.form['filetype'], filename=filename))
            db.session.commit()
    return render_template('upload.html')


@app.route('/download/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)


@app.route('/delete/<int:id>')
@login_required
def delete(id):
    file = FileEntry.query.filter(FileEntry.id == id).one()
    db.session.delete(file)
    db.session.commit()
    if file.filetype in [0, 1, 2, 3]:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
    return render_template('directory.html', files=FileEntry.query.all())


@app.route('/approve/<int:id>')
@login_required
def approve(id):
    file = FileEntry.query.filter(FileEntry.id == id).one()
    file.approved = not file.approved
    db.session.commit()
    return render_template('directory.html', files=FileEntry.query.all())


@app.route('/comment', methods=['POST'])
@login_required
def postComment():
    db.session.add(
        CommentEntry(user_id=current_user.id, text=request.form['text'], fileentry_id=request.form['postid']))
    db.session.commit()
    return "OK"


@app.route('/comment/<int:id>', methods=['GET'])
def listComment(id):
    return jsonify([{'id': row.id, 'text': row.text, 'created_at': row.created_at} for row in
                    CommentEntry.query.filter(CommentEntry.fileentry_id == id)])


@app.route('/dbjson')
def dbjson():
    return jsonify(sorted([{'id': x.id, 'approved': x.approved, 'creation_date': x.created_at, 'project_year': x.project_year,
                     'project_month': x.project_month, 'title': x.title,
                     'author': x.user.username if x.user else "Unknown",
                     'description': x.description, 'filetype': x.filetype, 'filename': x.filename} for x in FileEntry.query.all()], reverse=True, key=itemgetter('project_year', 'project_month')))


@app.errorhandler(404)
def lost(e):
    return render_template('lost.html')

if __name__ == '__main__':
    parser = argparse.ArgumentParser("RBSite App")
    parser.add_argument("prod", help="An integer specifying to run in production (1 for yes, 0 for no)", type=int)
    args = parser.parse_args()
    if args.prod == 3:
        with app.app_context():
            users = User.query.all()
            for i, user in enumerate(users):
                print(f'{user.id}: {user.username}')
            target = int(input("id to delete: "))
            db.session.delete(db.session.get(User, target))
            db.session.commit()

    elif args.prod == 2:
        with app.app_context():
            db.create_all()
            new_user = User(username=input("Enter username: "), email=input("Enter email: "), password=input("Enter password: "))
            db.session.add(new_user)
            db.session.commit()
    elif args.prod == 1:
        from waitress import serve

        print("Started running production thing")
        serve(app, host="0.0.0.0", port=80, url_scheme='https')
    elif args.prod == 0:
        app.run(debug=True, port=3000, host='0.0.0.0')
