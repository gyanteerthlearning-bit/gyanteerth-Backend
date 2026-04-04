from pydantic import BaseModel, Field, field_validator
from enum import Enum
import re
from datetime import date

class GenderEnum(str, Enum):
    male = "male"
    female = "female"


class UpdateUserProfileRequest(BaseModel):
    user_name: str 
    user_number: int
    user_dob: date
    user_city: str
    user_state: str

    @field_validator("user_name")
    @classmethod
    def validate_username(cls, value: str):
        if " " in value:
            raise ValueError("Username must not contain spaces")
        if not re.fullmatch(r"[A-Za-z]+", value):
            raise ValueError("Username must contain only letters")
        return value
    
    
    @field_validator("user_number")
    @classmethod
    def validate_phone(cls, value: int):
        if not isinstance(value, int):
            raise ValueError("Phone number must be an integer")
        if len(str(value)) != 10:
            raise ValueError("Phone number must be exactly 10 digits")
        return value
    
from pydantic import BaseModel
from typing import Optional
from datetime import date

class UserProfile_response(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    user_name: Optional[str] = None
    user_pic: Optional[str] = None
    user_number: Optional[int] = None
    user_dob: Optional[date] = None
    user_gender: Optional[GenderEnum] = None
    user_city: Optional[str] = None
    user_state: Optional[str] = None
    email_verified: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "USER-1234-abcd",
                "email": "user_email@gmail.com",
                "user_name": "John Doe",
                "user_pic": "https://res.cloudinary.com/demo/image/upload/1234567890/user_pic.jpg",
                "user_number": 1234567890,
                "user_dob": "1990-01-01",
                "user_gender": "male",
                "user_city": "New York",
                "user_state": "NY",
                "email_verified": True
            }
        }
class update_profile_response(BaseModel):
    message: str
    user_id:str
    email:str
    user_name:str
    user_pic:str | None
    user_number:str
    user_dob:date
    user_gender:GenderEnum
    user_city:str
    user_state:str
    cloud_upload_time: float | None = None
    cloud_delete_time: float | None = None
    class Config:
        json_schema_extra = {
            "example":{
                "message": "User profile updated successfully",
                "user_id": "USER-1234-abcd",
                "email": "user@gmail.com",
                "user_name": "John Doe",
                "user_pic": "https://res.cloudinary.com/demo/image/upload/1234567890/user_pic.jpg",
                "user_number": "1234567890",
                "user_dob": "1990-01-01",
                "user_gender": "male",
                "user_city": "New York",
                "user_state": "NY",
                "cloud_upload_time": 0.5,
                "cloud_delete_time": 0.3
            }
        }

class EnrollCourseRequest(BaseModel):
    course_id: str

class EnrollCourseResponse(BaseModel):
    enrollment_id: str
    message: str

class MarkLiveAttendanceRequest(BaseModel):
    live_class_id: str
    module_id: str
    attended_live: bool = False
    watched_recording: bool = False

class MarkLiveAttendanceResponse(BaseModel):
    message: str
    is_present: bool