from models.visitor import db
from flask_bcrypt import generate_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    @staticmethod
    def create_user(username, password, is_admin=False):
        hashed_password = generate_password_hash(password).decode("utf-8")
        user = User(username=username, password=hashed_password, is_admin=is_admin)
        db.session.add(user)
        db.session.commit()
