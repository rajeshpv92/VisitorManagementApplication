from datetime import datetime
from . import db

class EmployeeInfo(db.Model):
    __tablename__ = 'Employee'

    ID = db.Column(db.Integer, primary_key=True)
    EMPNO = db.Column(db.Integer, primary_key=True)
    EMPNAME = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    MobileNo = db.Column(db.String(15), nullable=False)  # Keeping as String for flexibility
    DEPTNO = db.Column(db.Integer, db.ForeignKey('DEPT.DEPTNO'), nullable=False)  # ForeignKey referencing DEPT
    CreatedBy = db.Column(db.String(255), nullable=False)
    CreatedTime = db.Column(db.DateTime, default=datetime.now)
    UpdatedBy = db.Column(db.String(255), nullable=False)
    UpdatedTime = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Establish the relationship with the DepartmentInfo model
    department = db.relationship('DepartmentInfo', backref='employees')

    def __repr__(self):
        return f"EmployeeInfo(empno={self.EMPNO}, empname={self.EMPNAME}, mobile={self.MobileNo})"
