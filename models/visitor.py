from datetime import datetime
from . import db

class VisitorInfo(db.Model):
    __tablename__ = 'Visitor'

    # Define columns
    ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(255), nullable=False)  # Visitor's name
    ContactNumber = db.Column(db.String(20), nullable=False)  # Contact number
    Purpose = db.Column(db.String(255), nullable=False)  # Purpose of visit
    Address = db.Column(db.String(255), nullable=True)  # Address (optional)
    photo = db.Column(db.String(255), nullable=True)  # Path to uploaded photo
    empno = db.Column(db.Integer, db.ForeignKey('Employee.EMPNO'), nullable=True)  # Get the emp no.
    CreatedBy = db.Column(db.String(255), nullable=False)  # Creator of record
    CreatedTime = db.Column(db.DateTime, default=datetime.now)  # Timestamp for creation
    UpdatedBy = db.Column(db.String(255), nullable=False)  # Updater of record
    UpdatedTime = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # Timestamp for updates
    CheckIn = db.Column(db.DateTime, nullable=False)  # Check-in time
    CheckOut = db.Column(db.DateTime, nullable=True)  # Check-out time (optional)

    # Establish the relationship with the EmployeeInfo model
    employee = db.relationship('EmployeeInfo', backref='visitor')

    def __repr__(self):
        """String representation of the VisitorInfo model."""
        return (
            f"<VisitorInfo(ID={self.ID}, Name={self.Name}, ContactNumber={self.ContactNumber}, "
            f"Purpose={self.Purpose}, Address={self.Address}, CheckIn={self.CheckIn}, "
            f"CheckOut={self.CheckOut}, Photo={self.Photo})>"
        )
