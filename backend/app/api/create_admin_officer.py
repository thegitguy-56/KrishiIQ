from app.database import SessionLocal
from app.models.user import User, UserRole
from app.services import auth_service

db = SessionLocal()

hash_password = (
    auth_service.get_password_hash
    if hasattr(auth_service, "get_password_hash")
    else auth_service.hash_password
)

users = [
    ("9000000001", "officer@gmail.com", "officer123", UserRole.OFFICER),
    ("9000000003", "admin@gmail.com", "admin123", UserRole.ADMIN),
]

for phone, email, password, role in users:
    user = db.query(User).filter(User.phone == phone).first()

    if user:
        user.email = email
        user.hashed_password = hash_password(password)
        user.role = role
        user.is_active = True
        user.preferred_language = "en"
        print("Updated", phone)
    else:
        user = User(
            phone=phone,
            email=email,
            hashed_password=hash_password(password),
            role=role,
            is_active=True,
            preferred_language="en",
        )
        db.add(user)
        print("Created", phone)

db.commit()

for u in db.query(User).all():
    print(u.phone, u.role, u.is_active)