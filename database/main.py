# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import engine, get_db
from models import User, CourseOrder
from crud import create_course_order, create_user
from schemas import UserCreate, CourseOrderCreate, CourseOrderResponse, UserResponse

# Create the FastAPI app
app = FastAPI()

# ---------------------

# API endpoint to create a user and the associated course order
@app.post("/users/", response_model=UserResponse)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = create_user(db, user)
        return db_user
    except Exception as e:
        print(f"Error while creating user: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# API endpoint to create a course order by user_id
# Endpoint to create a course order for an existing user
@app.post("/orders/", response_model=CourseOrderResponse)
def create_course_order_endpoint(order: CourseOrderCreate, db: Session = Depends(get_db)):
    # Ensure the user exists before creating an order
    db_user = db.query(User).filter(User.id == order.user_id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_order = create_course_order(db, order)
    return db_order


