from datetime import datetime
from . import db

class DepartmentInfo(db.Model):
    __tablename__ = 'DEPT'

    DEPTNO = db.Column(db.Integer, primary_key=True)
    DNAME = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<Department {self.DNAME}>"
