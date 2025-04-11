from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_socketio import SocketIO
from models import db, User, Admin, PhotoNomination, Vote, bcrypt
import os
import socket
import ssl
from werkzeug.utils import secure_filename

app = Flask(__name__)
socketio = SocketIO(app)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///voting_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'c935029642182c11ea08a2aab86250eb'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db.init_app(app)
bcrypt.init_app(app)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash("Username already taken!", "danger")
            return redirect(url_for('register'))

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password!", "danger")

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("You need to log in first.", "warning")
        return redirect(url_for('login'))

    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/register_admin', methods=['GET', 'POST'])
def register_admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if Admin.query.filter_by(username=username).first():
            flash("Admin username already taken.", "danger")
            return redirect(url_for('register_admin'))

        new_admin = Admin(username=username)
        new_admin.set_password(password)
        db.session.add(new_admin)
        db.session.commit()

        flash("Admin registered successfully!", "success")
        return redirect(url_for('admin_login'))

    return render_template('register_admin.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            flash("Admin login successful!", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid admin credentials!", "danger")

    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        flash("Admin access required.", "warning")
        return redirect(url_for('admin_login'))

    nominations = PhotoNomination.query.all()
    return render_template('admin_dashboard.html', nominations=nominations)

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_id', None)
    flash("Admin logged out.", "info")
    return redirect(url_for('admin_login'))

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    if 'user_id' not in session:
        flash("You need to log in first.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    user_vote = Vote.query.filter_by(user_id=user_id).first()

    if request.method == 'POST':
        photo_id = request.form['photo_id']

        if user_vote:
            flash("You have already voted!", "danger")
            return redirect(url_for('vote'))

        encrypted_vote = Vote.encrypt_vote(photo_id)
        new_vote = Vote(user_id=user_id, photo_id=photo_id, encrypted_vote=encrypted_vote)
        db.session.add(new_vote)
        db.session.commit()

        # Socket communication with SSL
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            with socket.create_connection(('127.0.0.1', 65432)) as sock:
                with context.wrap_socket(sock, server_hostname='localhost') as ssock:
                    message = f"VOTE|{user_id}|{photo_id}"
                    ssock.sendall(message.encode())
        except Exception as e:
            print("Socket Error:", e)

        socketio.emit('update_leaderboard', get_leaderboard())

        flash("Vote cast successfully!", "success")
        return redirect(url_for('dashboard'))

    nominations = PhotoNomination.query.all()
    return render_template('vote.html', nominations=nominations, user_vote=user_vote)

def get_leaderboard():
    results = db.session.query(
        PhotoNomination.id,
        PhotoNomination.title,
        PhotoNomination.image_filename,
        db.func.count(Vote.id).label('vote_count')
    ).outerjoin(Vote, PhotoNomination.id == Vote.photo_id
    ).group_by(PhotoNomination.id
    ).order_by(db.desc('vote_count')).all()

    leaderboard = []
    last_votes = None
    current_rank = 0

    for i, row in enumerate(results, 1):
        if row.vote_count != last_votes:
            current_rank = i

        leaderboard.append({
            "id": row.id,
            "title": row.title,
            "image_filename": row.image_filename,
            "votes": row.vote_count,
            "rank": current_rank
        })

        last_votes = row.vote_count

    return leaderboard


@app.route('/leaderboard')
def leaderboard():
    return render_template('leaderboard.html', leaderboard=get_leaderboard())

@socketio.on('request_leaderboard')
def send_leaderboard():
    socketio.emit('update_leaderboard', get_leaderboard())

@app.route('/add_nomination', methods=['GET', 'POST'])
def add_nomination():
    if 'admin_id' not in session:
        flash("Admin access required.", "warning")
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        image = request.files['image']

        if image:
            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(filepath)

            new_nomination = PhotoNomination(title=title, description=description, image_filename=filename)
            db.session.add(new_nomination)
            db.session.commit()

            flash("Nomination added successfully!", "success")
            return redirect(url_for('admin_dashboard'))

    return render_template('add_nomination.html')

if __name__ == '__main__':
    socketio.run(app, debug=True)
