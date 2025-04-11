from app import app, db, bcrypt

# Create an application context before creating tables
with app.app_context():
    db.create_all()
    print("Database initialized successfully.")
