from Models.Course_Tables.course_details import CourseTable
from Models.Progress.EnrollmentTable import EnrollmentTable
from Models.User_Tables.User_Profile import user_profile_table
from fastapi import FastAPI, UploadFile, File, HTTPException
import cloudinary
import cloudinary.uploader
from utils.Emailservice import send_email
from Database.DB import get_db
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import time
import uuid


load_dotenv()
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

class UserService:
    def delete_cloudinary(public_id):
        cloudinary.uploader.destroy(public_id)
    async def get_user_profile(self, token: dict, db: Session):
        user_id = token.get("user_id")
        user = db.query(user_profile_table).filter(
            user_profile_table.user_id == user_id
        ).first()
    
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "user_id": user.user_id,
            "email": user.user_email,
            "user_name": user.user_name,
            "user_pic": user.user_pic,
            "user_number": user.user_number,
            "user_dob": user.user_dob,
            "user_gender": user.user_gender,
            "user_city": user.user_city,
            "user_state": user.user_state,
            "email_verified": user.user_email_verified
        }
    
    async def update_user_profile(self, Data, user_gender,background_tasks, user_pic: UploadFile | None, token: dict, db: Session):
        user_id = token.get("user_id")
        cloud_start = 0
        cloud_end = 0
        cloud_dstart = 0
        cloud_dend = 0
        user = db.query(user_profile_table).filter(
            user_profile_table.user_id == user_id
        ).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        try:
            if user_pic:
                if user.user_pic and "res.cloudinary.com" in user.user_pic:
                    file_name = user.user_pic.split("/")[-1]
                    public_id = file_name.split(".")[0]
                    cloud_dstart = time.time()
                    background_tasks.add_task(self.delete_cloudinary, public_id)
                    cloud_dend = time.time()
                cloud_start = time.time()
                upload_result = cloudinary.uploader.upload(user_pic.file)
                cloud_end = time.time()
                user.user_pic = upload_result.get("secure_url")
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Image upload failed: {str(e)}"
            )
        user.user_name = Data.user_name
        user.user_number = Data.user_number
        user.user_dob = Data.user_dob
        user.user_gender = user_gender
        user.user_city = Data.user_city
        user.user_state = Data.user_state
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return {
            "message": "User profile updated successfully",
            "user_id": user.user_id,
            "email": user.user_email,
            "user_name": user.user_name,
            "user_pic": user.user_pic,
            "user_number": str(user.user_number) if user.user_number else None,
            "user_dob": user.user_dob,
            "user_gender": user.user_gender,
            "user_city": user.user_city,
            "user_state": user.user_state,
            "cloud_upload_time": cloud_end - cloud_start,
            "cloud_delete_time":cloud_dend - cloud_dstart
        }
    
    async def enroll_course(self, course_id: str, db: Session,token: dict):

        course = db.query(CourseTable).filter(
            CourseTable.course_id == course_id,
            CourseTable.is_active == True
        ).first()

        if not course:
            raise HTTPException(status_code=404, detail="Course not found or inactive")
    
        existing = db.query(EnrollmentTable).filter(
            EnrollmentTable.User_ID == token.get('user_id'),
            EnrollmentTable.Course_ID == course_id
        ).first()
    
        if existing:
            raise HTTPException(status_code=400, detail="Already enrolled in this course")
    
        enrollment = EnrollmentTable(
            Enrollment_ID=f"ENROLL-{uuid.uuid4().hex[:8]}",
            User_ID=token.get('user_id'),
            Course_ID=course_id,
            Status="ACTIVE",
            Enrolled_AT=datetime.utcnow()
        )
    
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)
    
        return {
            "enrollment_id": enrollment.Enrollment_ID,
            "message": "Successfully enrolled"
        }
    
    async def enrolled_course(self,db:Session,token:dict):
        try:
            user_id = token.get("user_id")
            enrollments = db.query(EnrollmentTable).filter(
                EnrollmentTable.User_ID == user_id,
            ).all()
    
            course_ids = [enrollment.Course_ID for enrollment in enrollments]
    
            courses = db.query(CourseTable).filter(
                CourseTable.course_id.in_(course_ids)
            ).all()
    
            return [
                {
                    "course_id": course.course_id,
                    "course_name": course.course_name,
                    "course_description": course.course_description,
                    "course_pic": course.course_pic
                }
                for course in courses
            ]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    async def mark_live_attendance(self, live_class_id: str, module_id: str, attended_live: bool, watched_recording: bool, token: dict, db: Session):
        from Models.Progress.LiveAttendanceTable import LiveAttendanceTable
        user_id = token.get("user_id")

        if not attended_live and not watched_recording:
            raise HTTPException(status_code=400, detail="Must mark either live attendance or recording view as true")

        attendance = db.query(LiveAttendanceTable).filter(
            LiveAttendanceTable.User_ID == user_id,
            LiveAttendanceTable.Live_Class_ID == live_class_id
        ).first()

        if attendance:
            # Update existing attendance
            if attended_live:
                attendance.Attended_Live = True
            if watched_recording:
                attendance.Watched_Recording = True
            attendance.Is_Present = True
            attendance.updated_at = datetime.utcnow()
            message = "Attendance updated successfully"
        else:
            # Create new attendance record
            attendance = LiveAttendanceTable(
                Live_Attendance_ID=f"LIVE-ATT-{uuid.uuid4().hex[:8]}",
                User_ID=user_id,
                Live_Class_ID=live_class_id,
                Module_ID=module_id,
                Attended_Live=attended_live,
                Watched_Recording=watched_recording,
                Is_Present=True,
                Completed_At=datetime.utcnow()
            )
            db.add(attendance)
            message = "Attendance marked successfully"

        db.commit()
        return {
            "message": message,
            "is_present": attendance.Is_Present
        }
