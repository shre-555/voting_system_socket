from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import rsa

db = SQLAlchemy()
bcrypt = Bcrypt()

# RSA Keys for encryption
with open("public.pem", "rb") as pub_file:
    public_key = rsa.PublicKey.load_pkcs1(pub_file.read())

with open("private.pem", "rb") as priv_file:
    private_key = rsa.PrivateKey.load_pkcs1(priv_file.read())

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

# Admin Model (Separate from Users)
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

# PhotoNomination Model
class PhotoNomination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255), nullable=False)

# Vote Model
class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    photo_id = db.Column(db.Integer, db.ForeignKey('photo_nomination.id'), nullable=False)
    encrypted_vote = db.Column(db.LargeBinary, nullable=False)

    @staticmethod
    def encrypt_vote(photo_id):
        return rsa.encrypt(str(photo_id).encode(), public_key)

    @staticmethod
    def decrypt_vote(encrypted_vote):
        return int(rsa.decrypt(encrypted_vote, private_key).decode())
