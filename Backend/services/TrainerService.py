from fastapi import HTTPException
from sqlalchemy.orm import Session
from Models.Course_Tables.course_details import CourseTable
from Models.User_Tables.User_Access import user_access_table

class TrainerService:
    async def Trainer_have_course_ids(self,db:Session,token: str):
        try:
            trainer = db.query(user_access_table).filter(
                user_access_table.user_id == token.get("user_id"),
                user_access_table.role == "trainer"
            ).first()
    
            if not trainer:
                raise HTTPException(
                    status_code=404,
                    detail="User is not a trainer or does not exist"
                )
    
            courses = db.query(CourseTable.course_id).filter(
                CourseTable.instructor_id == token.get("user_id"),
                CourseTable.is_active == True,
                CourseTable.draft == False
            ).all()
    
            course_ids = [c.course_id for c in courses]
    
            return {
                "status": True,
                "course_ids": course_ids
            }
    
        except HTTPException:
            raise
    
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch course IDs: {str(e)}"
            )

    async def get_course_students_progress(self, course_id: str, db: Session, token: dict):
        try:
            user_id = token.get("user_id")
            role = token.get("role")

            # Admin or the assigned trainer can access
            is_admin = role == "admin"
            
            course = db.query(CourseTable).filter(CourseTable.course_id == course_id).first()
            if not course:
                raise HTTPException(status_code=404, detail="Course not found")

            if not is_admin and course.instructor_id != user_id:
                raise HTTPException(status_code=403, detail="Not authorized to view progress for this course")

            # Fetch students enrolled in this course
            from Models.Progress.EnrollmentTable import EnrollmentTable
            from Models.User_Tables.User_Profile import user_profile_table
            from Models.Progress.CourseProgressTable import CourseProgressTable
            from sqlalchemy import and_

            students = db.query(
                user_profile_table.user_id,
                user_profile_table.user_name,
                CourseProgressTable.Progress_Percentage,
                CourseProgressTable.Completed_Module,
                CourseProgressTable.Total_Modules
            ).join(
                EnrollmentTable,
                EnrollmentTable.User_ID == user_profile_table.user_id
            ).outerjoin(
                CourseProgressTable,
                and_(
                    CourseProgressTable.User_ID == user_profile_table.user_id,
                    CourseProgressTable.Course_ID == course_id
                )
            ).filter(
                EnrollmentTable.Course_ID == course_id
            ).all()

            data = [
                {
                    "user_id": s.user_id,
                    "user_name": s.user_name,
                    "progress_percentage": s.Progress_Percentage or 0,
                    "completed_modules": s.Completed_Module or 0,
                    "total_modules": s.Total_Modules or 0
                }
                for s in students
            ]

            return {
                "status": True,
                "course_id": course_id,
                "data": data
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch students progress: {str(e)}")