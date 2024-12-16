from datetime import datetime
from . import db

class UserInfo(db.Model):
    __tablename__ = "User_Info"
    
    
    ID = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(50), nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    UserID = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    countrycode = db.Column(db.String(50), nullable=False)
    Role_ID = db.Column(db.Integer, db.ForeignKey('Roles.RoleID'), nullable=False,  default=2)  # 1 for admin, 2 for user
    Password = db.Column(db.String(100), nullable=False)
    CreatedBy = db.Column(db.String(255), nullable=False)  # Column for creator
    CreatedTime = db.Column(db.DateTime, default=datetime.now())  # Timestamp for creation
    UpdatedBy = db.Column(db.String(255), nullable=False)  # Column for updater
    UpdatedTime = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())  # Timestamp for update

    # Establish the relationship with the RoleInfo model
    role = db.relationship('RoleInfo', backref='users')

    def __repr__(self):
        return f"UserInfo(name={self.Name}, userid={self.UserID}, role_id={self.Role_ID})"
