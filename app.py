from flask import Flask, flash, redirect, render_template, request, jsonify, url_for, send_from_directory, make_response
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import os
import datetime
import argparse
import hashlib

UPLOAD_FOLDER = './uploads'
TEMPLATE_FOLDER = './pages'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'mp3', 'mp4'}

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, template_folder=TEMPLATE_FOLDER)
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'bob'

db = SQLAlchemy(app)


# Very good security practice :)
users = {
    '3d2ce9e6f831206186e356376a913dc7d440b1d7eb2f804d4b66f37449af58f4941027bbca79afe96144fdea13349c3c659c44f3157e75256e7b52315d2c3a6b': 'Rui',
    '51279e6ba0c7f6655582898572536c131a32172b72d17c81b85380c712f4fde80b059f69a4d88adb4775c9685f1c0c5e844aa09c029b675e20254a8418428090': 'Kian',
    'Bob': 'asdf',
    'Bobob': 'asdf',
    'Bobinsky': 'asdf',
    'Bobo': 'asdf',
    'Bobby': 'asdf',
}


class FileEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    project_year = db.Column(db.Integer, nullable=False)
    project_month = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True),
                           server_default=func.now())
    description = db.Column(db.String(2200), nullable=False)
    approved = db.Column(db.Boolean, default=False, nullable=False)
    filename = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<FileEntry {self.filename}>'


class CommentEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fileentry_id = db.Column(db.Integer, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True),
                           server_default=func.now())

    def __repr__(self):
        return f'<CommentEntry {self.id}>'


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html', family_photos=[a for a in os.listdir('./static/assets/family') if
                                                        a.split('.')[-1].upper() == 'JPG'])


@app.route('/directory')
def directory():
    return render_template('directory.html', files=FileEntry.query.all())


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'RB_MEMBER_CODE' not in request.cookies:
        if request.method == 'POST':
            cookie_hash = hashlib.sha512(bytes(request.form['memberid'], 'utf-8')).hexdigest()
            if cookie_hash in users.keys():
                resp = make_response(render_template('upload.html'))
                resp.set_cookie('RB_MEMBER_CODE', cookie_hash)
                return resp
        return render_template('authenticate.html')

    if hashlib.sha512(bytes(request.cookies.get('RB_MEMBER_CODE'), 'utf-8')).hexdigest() not in users.keys():
        return render_template('authenticate.html')

    if request.method == 'POST':
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
            db.session.add(FileEntry(author=request.form['author'], project_year=request.form['year'],
                                     project_month=request.form['month'], title=request.form['title'],
                                     description=request.form['description'], filename=filename))
            db.session.commit()
    return render_template('upload.html')


@app.route('/download/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)


@app.route('/delete/<int:id>')
def delete(id):
    if request.cookies.get('RB_MEMBER_CODE') not in users.keys():
        return redirect(url_for('upload'))
    file = FileEntry.query.filter(FileEntry.id == id).one()
    db.session.delete(file)
    db.session.commit()
    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
    return render_template('directory.html', files=FileEntry.query.all())


@app.route('/approve/<int:id>')
def approve(id):
    if request.cookies.get('RB_MEMBER_CODE') not in users.keys():
        return redirect(url_for('upload'))
    file = FileEntry.query.filter(FileEntry.id == id).one()
    file.approved = not file.approved
    db.session.commit()
    return render_template('directory.html', files=FileEntry.query.all())


@app.route('/comment', methods=['POST'])
def postComment():
    if request.cookies.get('RB_MEMBER_CODE') not in users.keys():
        return "UNAUTHORIZED"
    db.session.add(
        CommentEntry(author=users[request.cookies.get('RB_MEMBER_CODE')], text=request.form['text'], fileentry_id=request.form['postid']))
    db.session.commit()
    return "OK"


@app.route('/comment/<int:id>', methods=['GET'])
def listComment(id):
    return jsonify([{'id': row.id, 'author': row.author, 'text': row.text, 'created_at': row.created_at} for row in
                    CommentEntry.query.filter(CommentEntry.fileentry_id == id)])


@app.route('/dbjson')
def dbjson():
    return jsonify([{'id': x.id, 'approved': x.approved, 'creation_date': x.created_at, 'project_year': x.project_year,
                     'project_month': x.project_month, 'author': x.author, 'title': x.title,
                     'description': x.description, 'filename': x.filename} for x in FileEntry.query.all()])


@app.errorhandler(404)
def lost(e):
    return render_template('lost.html')


if __name__ == '__main__':
    parser = argparse.ArgumentParser("RBSite App")
    parser.add_argument("prod", help="An integer specifying to run in production (1 for yes, 0 for no)", type=int)
    args = parser.parse_args()
    if args.prod:
        from waitress import serve

        print("Started running production thing")
        serve(app, host="0.0.0.0", port=80)
    else:
        app.run(debug=True, port=3000, host='0.0.0.0')
