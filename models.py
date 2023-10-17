from app import db
def avs():
    pass
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    company = db.Column(db.String(50), nullable=False)
    criterion1 = db.Column(db.Integer, nullable=False)
    criterion2 = db.Column(db.Integer, nullable=False)
    criterion3 = db.Column(db.Integer, nullable=False)
    criterion4 = db.Column(db.Integer, nullable=False)
    criterion5 = db.Column(db.Integer, nullable=False)
