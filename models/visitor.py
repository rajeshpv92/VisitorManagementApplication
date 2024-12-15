from datetime import datetime
from . import db

class VisitorInfo(db.Model):
    __tablename__ = 'Visitor'

    ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(255), nullable=False)
    ContactNumber = db.Column(db.String(20), nullable=False)
    Purpose = db.Column(db.String(255), nullable=False)
    Address = db.Column(db.String(255), nullable=True)
    CreatedBy = db.Column(db.String(255), nullable=False)
    CreatedTime = db.Column(db.DateTime, default=datetime.now)
    UpdatedBy = db.Column(db.String(255), nullable=False)
    UpdatedTime = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    CheckIn = db.Column(db.DateTime, nullable=False)
    CheckOut = db.Column(db.DateTime, nullable=True)
    Photo = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return (f"VisitorInfo(name={self.Name}, contact_number={self.ContactNumber}, "f"purpose={self.Purpose}, check_in={self.CheckIn}, check_out={self.CheckOut}, "f"photo={self.Photo})")
