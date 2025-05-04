from pydantic import BaseModel
from datetime import date

# Base user schema (shared attributes)
class UserBase(BaseModel):
    name: str
    dob: date
    qualification: str
    phone_number: str
    email: str

    class Config:
        orm_mode = True


# For user creation (input only)
class UserCreate(UserBase):
    pass


# For returning user info (output)
class UserResponse(UserBase):
    id: int


# For creating a course order
class CourseOrderCreate(BaseModel):
    user_id: int
    course_name: str

    class Config:
        orm_mode = True


# For returning course order info (output)
class CourseOrderResponse(BaseModel):
    id: int
    user_id: int
    course_name: str

    class Config:
        orm_mode = True
