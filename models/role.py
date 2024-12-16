from datetime import datetime
from . import db

class RoleInfo(db.Model):
    __tablename__ = 'Roles'

    RoleID = db.Column(db.Integer, primary_key=True)
    Role = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<Role {self.Role}>"
