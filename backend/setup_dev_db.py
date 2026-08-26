from app.database.connection import init_db, SessionLocal
from app.models.models import User, Farm

print("Initializing DB...")
init_db()
db = SessionLocal()
if not db.query(User).first():
    user = User(name="Dev User", email="dev@example.com")
    db.add(user)
    db.commit()
    db.refresh(user)
    farm = Farm(owner_id=user.id, name="Dev Farm", latitude=0.0, longitude=0.0, location_name="Dev Loc")
    db.add(farm)
    db.commit()
    print("Created Dev User and Farm. Farm ID:", farm.id)
else:
    print("Dev User already exists.")
db.close()
