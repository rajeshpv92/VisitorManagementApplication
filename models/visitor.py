# from flask_sqlalchemy import SQLAlchemy
# from flask_bcrypt import Bcrypt

# db = SQLAlchemy()
# bcrypt = Bcrypt()

# class User(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(100), unique=True, nullable=False)
#     password = db.Column(db.String(200), nullable=False)
#     role = db.Column(db.String(50), nullable=False, default='user')  # 'admin' or 'user'

#     def check_password(self, password):
#         return bcrypt.check_password_hash(self.password, password)

# class Visitor(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     contact = db.Column(db.String(100), nullable=False)
#     purpose = db.Column(db.String(255), nullable=False)
#     check_in = db.Column(db.DateTime, nullable=False)
#     check_out = db.Column(db.DateTime, nullable=True)
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(50), nullable=False)
    purpose = db.Column(db.String(200), nullable=False)
    check_in = db.Column(db.DateTime, nullable=False)
    check_out = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Visitor {self.name}>"
