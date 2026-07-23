from app.database import SessionLocal
from app.models.user import User
from passlib.context import CryptContext

pwd = CryptContext(schemes=['bcrypt'], deprecated='auto')
db = SessionLocal()

admin = db.query(User).filter(User.phone == '9000000003').first()
admin.hashed_password = pwd.hash('admin123')

officer = db.query(User).filter(User.phone == '9000000001').first()
officer.hashed_password = pwd.hash('officer123')

db.commit()
print('Passwords reset successfully')