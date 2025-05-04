from sqlalchemy.orm import Session
from models import User, CourseOrder
from schemas import UserCreate, CourseOrderCreate


# Create a new user
def create_user(db: Session, user: UserCreate):
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# Create a course order for a user (course order is created after user creation)
def create_course_order(db: Session, order: CourseOrderCreate):
    db_user = db.query(User).filter(User.id == order.user_id).first()

    if not db_user:
        raise ValueError(f"User with ID {order.user_id} does not exist.")

    db_order = CourseOrder(user_id=order.user_id, course_name=order.course_name)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


