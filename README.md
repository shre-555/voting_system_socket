# Voting System Socket

## Project Details
This project is a secure voting system built using Flask and Flask-SocketIO. It leverages RSA encryption for secure communication and Flask-SQLAlchemy for database management. The system allows users to register, log in, and cast votes securely. It also includes real-time updates using WebSockets.

### Features
- User registration and authentication
- Secure communication using RSA encryption
- Real-time updates with Flask-SocketIO
- Database management with Flask-SQLAlchemy
- Flash messages for user feedback

## Steps to Run
1. Install the required dependencies:
   ```bash
   pip install flask flask-sqlalchemy flask-bcrypt flask-socketio rsa
   ```

2. Generate RSA keys (run this only once):
   ```bash
   python rsa_generate.py
   ```

3. Initialize the database (run this only once):
   ```bash
   python init_db.py
   ```

4. Start the Flask server:
   ```bash
   flask run
   ```
