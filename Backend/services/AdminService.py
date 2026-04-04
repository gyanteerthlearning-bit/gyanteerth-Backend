from Models.User_Tables.User_Profile import user_profile_table
from Models.User_Tables.User_Refresh_Token import user_refresh_token_table
from Models.User_Tables.User_Access import user_access_table
from Models.Course_Tables.Course_Category import CategoryCourseTable
from Models.Course_Tables.course_details import CourseTable
from fastapi import FastAPI, UploadFile, File, HTTPException,status
from Models.Course_Tables.Course_Demo import CourseDemoTable
from Models.Course_Tables.Course_Module import CourseModuleTable
from Models.Course_Tables.Course_Note import CourseNotesTable
from Models.Course_Tables.Course_Prerec_Video import CourseVideoTable
from Models.Course_Tables.Live_Course import LiveCourseTable
from Models.Course_Tables.Recorded_live import CourseRecVideoTable
from Models.Assessment_Tables.Assessment_table import AssessmentTable
from Models.Assessment_Tables.Question_table import QuestionTable 
from Models.Assessment_Tables.Options_table import optionTable
from sqlalchemy import func, exists, and_
from schemas.admin import CreateModuleRequest,CreateNotesRequest,CreateVideoRequest,CreateLiveCourseRequest,CreateRecVideoRequest,CreateAssessmentRequest,CreateQuestionRequest,CreateOptionRequest,UpdateCourseDemoRequest,UpdateModuleRequest,UpdateNotesRequest, UpdateVideoRequest,UpdateLiveCourseRequest,UpdateRecVideoRequest,UpdateAssessmentRequest,UpdateQuestionRequest,UpdateOptionRequest
from utils.email_templates.wecome_trainer_design import welcome_trainer_template
from utils.email_templates.coursecreate import course_created_template
from utils.email_templates.courseactive import course_active_template
from utils.Emailservice import send_email
from utils.google_meet import create_google_meet
from Database.DB import get_db
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta, timezone
import uuid
import re
from datetime import datetime, timedelta
from utils.security import hash_password,create_refresh_token
from dotenv import load_dotenv
load_dotenv()
import os

REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

class AdminService:
    async def create_trainer_services(self, Data, trainer_gender, background_tasks, token: dict, db: Session):

        trainer = db.query(user_profile_table).filter(
            user_profile_table.user_email == Data.trainer_email
        ).first()
    
        if trainer:
            raise HTTPException(status_code=400, detail="Trainer with this email already exists")
    
        try:
    
            new_trainer = user_profile_table(
                user_id=f"USER-{uuid.uuid4()}",
                user_email=Data.trainer_email,
                user_name=Data.trainer_name,
                user_number=Data.trainer_number,
                user_dob=Data.trainer_dob,
                user_pic=None,
                user_gender=trainer_gender,
                user_city=Data.trainer_city,
                user_state=Data.trainer_state,
                user_email_verified=True,
                Status = "Active"
            )
    
            db.add(new_trainer)
            db.commit()
            db.refresh(new_trainer)
    
            refresh_token = create_refresh_token(new_trainer.user_id)
    
            trainer_refresh_token = user_refresh_token_table(
                refresh_token_id=f"RefreshToken-{uuid.uuid4()}",
                user_id=new_trainer.user_id,
                refresh_token=refresh_token,
                ip_address="admin_created",
                user_agent="admin_created",
                device_name="admin_created",
                expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
                is_revoked=False
            )
    
            access = user_access_table(
                access_id=f"Access-{uuid.uuid4()}",
                user_id=new_trainer.user_id,
                provider_id=f"Email-{uuid.uuid4()}",
                provider_name="Email",
                role="trainer",
                password_hash=hash_password(Data.trainer_pass)
            )
    
            db.add_all([access, trainer_refresh_token])
            db.commit()
    
            subject = f"Welcome to Gyanteerth - Trainer Account Created"
    
            body = welcome_trainer_template(
                Data.trainer_name,
                Data.trainer_email,
                Data.trainer_pass
            )
    
            background_tasks.add_task(
                send_email,
                Data.trainer_email,
                subject,
                body
            )
    
            return {"message": "Trainer profile created successfully"}
    
        except Exception as e:
            db.rollback()
    
            raise HTTPException(
                status_code=500,
                detail="An error occurred while creating the trainer profile"
            )


    async def get_trainer_profile(self, Data, token: dict, db: Session):
        try:
            trainer = db.query(user_profile_table).filter(
                user_profile_table.user_email == Data.trainer_email
            ).first()
    
            if not trainer:
                raise HTTPException(status_code=404, detail="Trainer not found")
    
            return {
                "email": trainer.user_email,
                "user_name": trainer.user_name,
                "user_pic": trainer.user_pic,
                "user_number": trainer.user_number,
                "user_dob": trainer.user_dob,
                "user_gender": trainer.user_gender,
                "user_city": trainer.user_city,
                "user_state": trainer.user_state,
                "email_verified": trainer.user_email_verified
            }
    
        except HTTPException as http_err:
            raise http_err
    
        except Exception as e:
            print(f"Trainer profile error: {str(e)}")
    
            raise HTTPException(
                status_code=500,
                detail="Internal server error while fetching trainer profile"
            )
    
    async def all_trainer_email(self, token: dict, db: Session):
        try:
    
            result = (
                db.query(user_profile_table, user_access_table)
                .join(
                    user_access_table,
                    user_access_table.user_id == user_profile_table.user_id
                )
                .filter(
                    user_access_table.role == "trainer"
                )
                .all()
            )
    
            if not result:
                raise HTTPException(status_code=404, detail="No Trainers Found")
    
            inactive_trainer_emails = []
            active_trainer_emails = []

            for user_profile, user_access in result:
                if(user_profile.Status == "Inactive"):
                    p={}
                    p[user_profile.user_id]=user_profile.user_email
                    inactive_trainer_emails.append(p)
                else:
                    p={}
                    p[user_profile.user_id]=user_profile.user_email
                    active_trainer_emails.append(p)
            return {
                "success": True,
                "active_trainer_email": active_trainer_emails,
                "inactive_trainer_email":inactive_trainer_emails
            }
    
        except HTTPException as http_err:
            raise http_err
    
        except Exception as e:
            print(f"Trainer email fetch error: {str(e)}")
    
            raise HTTPException(
                status_code=500,
                detail="Internal server error while fetching trainer emails"
            )
    
    async def update_trainer_service(self,Data,db:Session,token:dict):
        try:
            trainer = db.query(user_profile_table).filter(
                user_profile_table.user_email == Data.trainer_email
            ).first()

            if not trainer:
                raise HTTPException(status_code=404, detail="No Trainers Found")
            
            trainer.user_name = Data.trainer_name
            trainer.user_number = Data.trainer_number
            trainer.user_email = Data.trainer_email
            trainer.user_gender = Data.trainer_gender
            trainer.user_dob = Data.trainer_dob
            trainer.user_city = Data.trainer_city
            trainer.user_state = Data.trainer_state

            trainer_Access = db.query(user_access_table).filter(
                user_access_table.user_id == trainer.user_id
            ).first()

            trainer_Access.password_hash = hash_password(Data.password)

            db.commit()
            return {
                "success":True,
                "message":"successfully_profile_updated"
            }
        except HTTPException as http_err:
            raise http_err
    
        except Exception as e:
            print(f"Trainer email fetch error: {str(e)}")
    
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error{str(e)}"
            )
        
    async def inactive_trainer(self,Data,db:Session,token:dict):
        try:
            trainer = db.query(user_profile_table).filter(
                user_profile_table.user_email == Data.trainer_email
            ).first()

            if not trainer:
                raise HTTPException(status_code=404, detail="No Trainers Found")
            
            if(trainer.Status == "Inactive"):
                trainer.Status = "active"
                db.commit()
                return {
                    "success":True,
                    "message":"successfully_trainer_profile_active"
                }
            else:
                trainer.Status = "Inactive"
                db.commit()
                return {
                    "success":True,
                    "message":"successfully_trainer_profile_inactive"
                }
        except HTTPException as http_err:
            raise http_err
    
        except Exception as e:
            print(f"Trainer email fetch error: {str(e)}")
    
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error{str(e)}"
            )
        
    async def get_all_categories(self,db: Session,token:dict):
    
        categories = db.query(CategoryCourseTable).all()
    
        category_map = {}
        root_categories = []
    
        for cat in categories:
            category_map[cat.Category_ID] = {
                "Category_ID": cat.Category_ID,
                "Category_Name": cat.Category_Name,
                "slug": cat.slug,
                "Course_Description": cat.Course_Description,
                "Icon": cat.Icon,
                "Thumbnail": cat.Thumbnail,
                "subcategories": []
            }
    
        for cat in categories:
            if cat.Parent_ID:
                parent = category_map.get(cat.Parent_ID)
                if parent:
                    parent["subcategories"].append(category_map[cat.Category_ID])
            else:
                root_categories.append(category_map[cat.Category_ID])
    
        return {"categories": root_categories}
    
    async def create_category(self,data, db: Session,token:dict):
    
        if data.Parent_ID:
            parent = db.query(CategoryCourseTable).filter(
                CategoryCourseTable.Category_ID == data.Parent_ID
            ).first()
    
            if not parent:
                raise HTTPException(status_code=404, detail="Parent category not found")
    
        new_category = CategoryCourseTable(
            Category_ID=f"CAT-{uuid.uuid4()}",
            Category_Name=data.Category_Name,
            slug=data.slug,
            Parent_ID=data.Parent_ID,
            Course_Description=data.Course_Description,
            Icon=data.Icon,
            Thumbnail=data.Thumbnail
        )
    
        db.add(new_category)
        db.commit()
        db.refresh(new_category)
    
        return new_category
    
    async def update_category(self, category_id: str, data, db: Session, token: dict):

        category = db.query(CategoryCourseTable).filter(
            CategoryCourseTable.Category_ID == category_id
        ).first()
    
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    
        update_data = data.dict(exclude_unset=True)
        print(update_data)
    
        def generate_slug(name: str):
            return re.sub(r'\s+', '-', name.strip().lower())
    
        def get_unique_slug(base_slug: str):
            slug = base_slug
            counter = 1
    
            while db.query(CategoryCourseTable).filter(
                CategoryCourseTable.slug == slug,
                CategoryCourseTable.Category_ID != category_id
            ).first():
                slug = f"{base_slug}-{counter}"
                counter += 1
    
            return slug
    
        def is_circular(parent_id: str):
            while parent_id:
                if parent_id == category_id:
                    return True
    
                parent = db.query(CategoryCourseTable).filter(
                    CategoryCourseTable.Category_ID == parent_id
                ).first()
    
                if not parent:
                    break
    
                parent_id = parent.Parent_ID
    
            return False
        if "Parent_ID" in update_data:
            parent_id = update_data["Parent_ID"] or None  
    
            if parent_id == category_id:
                raise HTTPException(status_code=400, detail="Category cannot be its own parent")
    
            if parent_id:
                parent = db.query(CategoryCourseTable).filter(
                    CategoryCourseTable.Category_ID == parent_id
                ).first()
    
                if not parent:
                    raise HTTPException(status_code=404, detail="Parent category not found")
    
                if is_circular(parent_id):
                    raise HTTPException(status_code=400, detail="Circular hierarchy not allowed")
    
            update_data["Parent_ID"] = parent_id
        else:
            update_data["Parent_ID"] = None
    
        if "slug" in update_data or "Category_Name" in update_data:
    
            base_slug = update_data.get("slug")
    
            if not base_slug and "Category_Name" in update_data:
                base_slug = generate_slug(update_data["Category_Name"])
    
            if base_slug:
                update_data["slug"] = get_unique_slug(base_slug)
    
        for key, value in update_data.items():
            setattr(category, key, value)
    
        db.commit()
        db.refresh(category)
    
        return category
    
    async def delete_category(self, category_id: str, db: Session,token:dict):
    
        category = db.query(CategoryCourseTable).filter(
            CategoryCourseTable.Category_ID == category_id
        ).first()
    
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    
        course_exists = db.query(CourseTable).filter(
            CourseTable.category_id == category_id
        ).first()
    
        if course_exists:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete category because courses exist under it"
            )
    
        db.delete(category)
        db.commit()
    
        return {"message": "Category deleted successfully"}
    
    async def create_course(self, data, instructor_id, db: Session,background_tasks, token: dict):

        try:
            trainer_id = db.query(user_access_table).filter(user_access_table.user_id == instructor_id ).first()

            if not trainer_id or trainer_id.role != "trainer":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Instructor with ID '{instructor_id}' not found or given id is not trainer id "
                )

            cate = db.query(CategoryCourseTable).filter(CategoryCourseTable.Category_ID == data.category_id).first()

            if not cate:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"category not found"
                )
        
            course_id = f"COURSE-{uuid.uuid4()}"
    
            slug = data.course_title.lower().replace(" ", "-")
    
            course = CourseTable(
                course_id=course_id,
                instructor_id=instructor_id,
                category_id=data.category_id,
                course_Type = data.course_Type,
                course_title=data.course_title,
                course_description=data.course_description,
                slug=slug,
                skill_set=data.skill_set,
                required_knowledge=data.required_knowledge,
                benefits=data.benefits,
                thumbnail=data.thumbnail,
                duration=data.duration,
                level=data.level,
                language=data.language,
                original_pay=data.original_pay,
                discount_pay=data.discount_pay
            )
    
            db.add(course)
            db.commit()
            db.refresh(course)

            trainer_email = instructor_id 
            trainer = db.query(user_profile_table).filter(user_profile_table.user_id == trainer_email).first()

            subject = "Course Draft Created – Information"

            body = course_created_template(course,trainer.user_name)
    

            background_tasks.add_task(send_email, trainer.user_email, subject, body)
            
            return {
                "status": True,
                "message": "Course created successfully",
                "course_id": course.course_id
            }
    
        except SQLAlchemyError as db_error:
    
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Database error occurred while creating course {db_error}"
            )

    async def create_course_demo(self, data, db: Session):

        try:

            demo_id = f"DEMO-{uuid.uuid4()}"

            demo = CourseDemoTable(
                Demo_ID=demo_id,
                Course_ID=data.course_id,
                Title=data.title,
                Video_URL=data.video_url,
                Duration=data.duration
            )

            db.add(demo)
            db.commit()
            db.refresh(demo)

            return {
                "status": True,
                "message": "Course demo added successfully",
                "demo_id": demo_id
            }

        except SQLAlchemyError as db_error:

            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Database error occurred while creating demo"
            )

        except Exception as e:

            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Something went wrong while adding course demo"
            )
        
    async def create_module_service(self, data: CreateModuleRequest, db: Session):
        try:

            course = db.query(CourseTable).filter(
                CourseTable.course_id == data.Course_ID
            ).first()

            module_exist = db.query(CourseModuleTable).filter(CourseModuleTable.Course_ID == data.Course_ID , CourseModuleTable.Position == data.Position).all()

            if module_exist:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                detail=f"this position already have other module"
                )
            if not course:
                raise HTTPException(
                    status_code=404,
                    detail="Course not found"
                )
            if data.Position <=0:
                raise HTTPException(
                    status_code=404,
                    detail="invalid position"
                )

            new_module = CourseModuleTable(
                Module_ID=f"MODULE-{uuid.uuid4()}",
                Course_ID=data.Course_ID,
                Title=data.Title,
                Course_Description=data.Course_Description,
                Position=data.Position
            )

            db.add(new_module)
            db.commit()
            db.refresh(new_module)

            return new_module

        except HTTPException:
            raise

        except Exception as e:

            db.rollback()

            raise HTTPException(
                status_code=500,
                detail=f"Module creation failed: {str(e)}"
            )
        
    async def create_notes_service(self, data: CreateNotesRequest, db: Session):

        try:

            course = db.query(CourseTable).filter(
                CourseTable.course_id == data.Course_ID
            ).first()

            if not course:
                raise HTTPException(
                    status_code=404,
                    detail="Course not found"
                )

            new_notes = CourseNotesTable(
                Notes_ID=f"NOTES-{uuid.uuid4()}",
                Course_ID=data.Course_ID,
                Title=data.Title,
                File_URL=data.File_URL,
                File_Type=data.File_Type
            )

            db.add(new_notes)
            db.commit()
            db.refresh(new_notes)

            return new_notes

        except HTTPException:
            raise

        except Exception as e:

            db.rollback()

            raise HTTPException(
                status_code=500,
                detail=f"Notes creation failed: {str(e)}"
            )
    
    async def create_video_service(self, data: CreateVideoRequest, db: Session):
        try:
            course = db.query(CourseTable).filter(
                CourseTable.course_id == data.Course_ID
            ).first()

            if not course:
                raise HTTPException(
                    status_code=404,
                    detail="Course not found"
                )

            if course.course_Type.lower() == "live":
                raise HTTPException(
                    status_code=400,
                    detail="Videos cannot be added to Live courses"
                )

            module = db.query(CourseModuleTable).filter(
                CourseModuleTable.Module_ID == data.Module_ID
            ).first()

            if not module:
                raise HTTPException(
                    status_code=404,
                    detail="Module not found"
                )

            new_video = CourseVideoTable(
                Video_ID=f"VIDEO-{uuid.uuid4()}",
                Module_ID=data.Module_ID,
                Course_ID=data.Course_ID,
                Video_URL=data.Video_URL,
                course_description=data.course_description
            )

            db.add(new_video)
            db.commit()
            db.refresh(new_video)

            return new_video

        except HTTPException:
            raise

        except Exception as e:

            db.rollback()

            raise HTTPException(
                status_code=500,
                detail=f"Video creation failed: {str(e)}"
            )
        
    async def create_live_course_service(self, data: CreateLiveCourseRequest, db: Session):
        try:
            course = db.query(CourseTable).filter(
                CourseTable.course_id == data.Course_ID
            ).first()

            if not course:
                raise HTTPException(
                    status_code=404,
                    detail="Course not found"
                )

            if course.course_Type.lower() != "live":
                raise HTTPException(
                    status_code=400,
                    detail="Live sessions can only be created for Live courses"
                )

            module = db.query(CourseModuleTable).filter(
                CourseModuleTable.Module_ID == data.Module_ID
            ).first()

            if not module:
                raise HTTPException(
                    status_code=404,
                    detail="Module not found"
                )

            if data.End_time <= data.Start_time:
                raise HTTPException(
                    status_code=400,
                    detail="End time must be greater than start time"
                )
            
            current_time = datetime.now(timezone.utc)  
            min_allowed_time = current_time 
            
            # Make Start_time timezone-aware for comparison if it's naive
            start_aware = data.Start_time
            if start_aware.tzinfo is None:
                start_aware = start_aware.replace(tzinfo=timezone.utc)

            if start_aware <= min_allowed_time:
                raise HTTPException(
                    status_code=400,
                    detail="Start time must be in the future"
                )

            # Auto-generate Google Meet URL using Google Calendar API
            try:
                meet_url = create_google_meet(
                    title=data.Title,
                    start_time=data.Start_time,
                    end_time=data.End_time,
                )
            except FileNotFoundError as e:
                raise HTTPException(
                    status_code=503,
                    detail=f"Google Meet setup error: {str(e)}"
                )
            except Exception as e:
                # Add a small debug hint to see which client ID is being used
                import os
                debug_hint = os.getenv("GOOGLE_CLIENT_ID", "MISSING")[:15]
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to generate Google Meet link (Debug:{debug_hint}): {str(e)}"
                )

            new_live = LiveCourseTable(
                Live_ID=f"LIVE-{uuid.uuid4()}",
                Course_ID=data.Course_ID,
                Module_ID=data.Module_ID,
                Meeting_URL=meet_url,
                Provider="Google Meet",
                Start_time=data.Start_time,
                End_time=data.End_time,
                Status=data.Status
            )

            db.add(new_live)
            db.commit()
            db.refresh(new_live)

            return new_live

        except HTTPException:
            raise

        
    async def create_recorded_video_service(self, data: CreateRecVideoRequest, db: Session):

        try:
            course = db.query(CourseTable).filter(
                CourseTable.course_id == data.Course_ID
            ).first()

            if not course:
                raise HTTPException(
                    status_code=404,
                    detail="Course not found"
                )

            if course.course_type.lower() != "live":
                raise HTTPException(
                    status_code=400,
                    detail="Recorded videos can only be added to Live courses"
                )

            live_session = db.query(LiveCourseTable).filter(
                LiveCourseTable.Live_ID == data.Live_ID
            ).first()
            current_time = datetime.utcnow()   

            if not live_session:
                raise HTTPException(
                    status_code=404,
                    detail="Live session not found"
                )
            
            if current_time < live_session.End_time:
                raise HTTPException(
                    status_code=401,
                    detail="wait for completion of live course"
                )

            new_video = CourseRecVideoTable(
                Rec_Video_ID=f"RECVIDEO-{uuid.uuid4()}",
                Live_ID=data.Live_ID,
                Course_ID=data.Course_ID,
                Rec_Video_URL=data.Rec_Video_URL,
                Duration=data.Duration
            )

            db.add(new_video)
            db.commit()
            db.refresh(new_video)

            return new_video

        except HTTPException:
            raise

        except Exception as e:

            db.rollback()

            raise HTTPException(
                status_code=500,
                detail=f"Recorded video creation failed: {str(e)}"
            )
        
    async def create_assessment_service(self, data: CreateAssessmentRequest, db: Session):

        try:
            module = db.query(CourseModuleTable).filter(
                CourseModuleTable.Module_ID == data.Module_ID
            ).first()

            if not module:
                raise HTTPException(
                    status_code=404,
                    detail="Module not found"
                )

            if data.Passing_Mark > data.Total_Mark:
                raise HTTPException(
                    status_code=400,
                    detail="Passing mark cannot be greater than total mark"
                )

            if data.Duration <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Duration must be greater than 0"
                )

            if data.Attempt_Limit <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Attempt limit must be greater than 0"
                )

            new_assessment = AssessmentTable(
                Assessment_ID=f"ASSESS-{uuid.uuid4()}",
                Module_ID=data.Module_ID,
                Title=data.Title,
                Description=data.Description,
                Total_Mark=data.Total_Mark,
                Passing_Mark=data.Passing_Mark,
                Duration=data.Duration,
                Attempt_Limit=data.Attempt_Limit,
                Status=data.Status
            )

            db.add(new_assessment)
            db.commit()
            db.refresh(new_assessment)

            return new_assessment

        except HTTPException:
            raise

        except Exception as e:

            db.rollback()

            raise HTTPException(
                status_code=500,
                detail=f"Assessment creation failed: {str(e)}"
            )
        
    async def create_question_service(self, data: CreateQuestionRequest, db: Session):

        try:

            assessment = db.query(AssessmentTable).filter(
                AssessmentTable.Assessment_ID == data.Assessment_ID
            ).first()
            question_pos = db.query(QuestionTable).filter(
                QuestionTable.Position == data.Position
            ).first()

            if not assessment:
                raise HTTPException(
                    status_code=404,
                    detail="Assessment not found"
                )

            if data.Mark <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Mark must be greater than 0"
                )

            if data.Position <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Position must be greater than 0"
                )
            
            if question_pos :
                raise HTTPException(
                    status_code=400,
                    detail="Position already taken by other question"
                )

            new_question = QuestionTable(
                Question_ID=f"QUES-{uuid.uuid4()}",
                Assessment_ID=data.Assessment_ID,
                Question_Txt=data.Question_Txt,
                Mark=data.Mark,
                Question_Type=data.Question_Type,
                Explanation=data.Explanation,
                Position=data.Position
            )

            db.add(new_question)
            db.commit()
            db.refresh(new_question)

            return new_question

        except HTTPException:
            raise

        except Exception as e:

            db.rollback()

            raise HTTPException(
                status_code=500,
                detail=f"Question creation failed: {str(e)}"
            )
        
    async def create_option_service(self, data: CreateOptionRequest, db: Session):

        try:
            question = db.query(QuestionTable).filter(
                QuestionTable.Question_ID == data.Question_ID
            ).first()

            option_pos = db.query(optionTable).filter(
                optionTable.Position == data.Position
            ).first()

            if not question:
                raise HTTPException(
                    status_code=404,
                    detail="Question not found"
                )

            if data.Position <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Position must be greater than 0"
                )
        
            if option_pos:
                raise HTTPException(
                    status_code=400,
                    detail="OPTION filled with other option"
                )

            if data.Is_Correct:

                existing_correct = db.query(optionTable).filter(
                    optionTable.Question_ID == data.Question_ID,
                    optionTable.Is_Correct == True
                ).first()

                if existing_correct:
                    raise HTTPException(
                        status_code=400,
                        detail="Correct option already exists for this question"
                    )

            new_option = optionTable(
                Option_ID=f"OPT-{uuid.uuid4()}",
                Question_ID=data.Question_ID,
                Option_Txt=data.Option_Txt,
                Is_Correct=data.Is_Correct,
                Position=data.Position
            )

            db.add(new_option)
            db.commit()
            db.refresh(new_option)

            return new_option

        except HTTPException:
            raise

        except Exception as e:

            db.rollback()

            raise HTTPException(
                status_code=500,
                detail=f"Option creation failed: {str(e)}"
            )
        
    async def update_course(self, course_id, data, instructor_id, db: Session, token: dict):

        try:
            course = db.query(CourseTable).filter(
                CourseTable.course_id == course_id,
                CourseTable.is_active == False
            ).first()
    
            if not course:
                raise HTTPException(
                    status_code=404,
                    detail="Course not found or is not active check draft"
                )
    
            slug = data.course_title.lower().replace(" ", "-")
            course.instructor_id = instructor_id
            course.category_id = data.category_id
            course.course_title = data.course_title
            course.course_description = data.course_description
            course.slug = slug
            course.skill_set = data.skill_set
            course.required_knowledge = data.required_knowledge
            course.benefits = data.benefits
            course.thumbnail = data.thumbnail
            course.duration = data.duration
            course.level = data.level
            course.language = data.language
            course.original_pay = data.original_pay
            course.discount_pay = data.discount_pay
    
            db.commit()
            db.refresh(course)
    
            return {
                "status": True,
                "message": "Course updated successfully",
                "course_id": course.course_id
            }
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Database error occurred while updating course"
            )
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Something went wrong while updating course"
            )
        
    async def update_course_demo(self, demo_id: str, data: UpdateCourseDemoRequest, db: Session):

        try:
            demo = db.query(CourseDemoTable).filter(
                CourseDemoTable.Demo_ID == demo_id
            ).first()
    
            if not demo:
                raise HTTPException(
                    status_code=404,
                    detail="Course demo not found"
                )
    
            demo.Title = data.title
            demo.Video_URL = data.video_url
            demo.Duration = data.duration
            db.commit()
            db.refresh(demo)
    
            return {
                "status": True,
                "message": "Course demo updated successfully",
                "demo_id": demo.Demo_ID
            }
    
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Database error occurred while updating demo"
            )
    
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Something went wrong while updating course demo"
            )
        
    async def update_module_service(self, module_id: str, data: UpdateModuleRequest, db: Session):

        try:
            module = db.query(CourseModuleTable).filter(
                CourseModuleTable.Module_ID == module_id
            ).first()
    
            if not module:
                raise HTTPException(
                    status_code=404,
                    detail="Module not found"
                )
    
            module.Title = data.Title
            module.Course_Description = data.Course_Description
            db.commit()
            db.refresh(module)
    
            return {
                "status": True,
                "message": "Module updated successfully",
                "module_id": module.Module_ID
            }
    
        except HTTPException:
            raise
    
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Module update failed: {str(e)}"
            )
        
    async def update_notes_service(self, notes_id: str, data: UpdateNotesRequest, db: Session):

        try:
    
            notes = db.query(CourseNotesTable).filter(
                CourseNotesTable.Notes_ID == notes_id
            ).first()
    
            if not notes:
                raise HTTPException(
                    status_code=404,
                    detail="Notes not found"
                )
    
            notes.Title = data.Title
            notes.File_URL = data.File_URL
            notes.File_Type = data.File_Type
    
            db.commit()
            db.refresh(notes)
    
            return {
                "status": True,
                "message": "Notes updated successfully",
                "notes_id": notes.Notes_ID
            }
    
        except HTTPException:
            raise
    
        except Exception as e:
    
            db.rollback()
    
            raise HTTPException(
                status_code=500,
                detail=f"Notes update failed: {str(e)}"
            )
        
    async def update_video_service(self, video_id: str, data: UpdateVideoRequest, db: Session):

        try:
    
            video = db.query(CourseVideoTable).filter(
                CourseVideoTable.Video_ID == video_id
            ).first()
    
            if not video:
                raise HTTPException(
                    status_code=404,
                    detail="Video not found"
                )
    
            course = db.query(CourseTable).filter(
                CourseTable.course_id == data.Course_ID
            ).first()
    
            if not course:
                raise HTTPException(
                    status_code=404,
                    detail="Course not found"
                )
    
            if course.course_Type.lower() == "live":
                raise HTTPException(
                    status_code=400,
                    detail="Videos cannot be added to Live courses"
                )
    
            module = db.query(CourseModuleTable).filter(
                CourseModuleTable.Module_ID == data.Module_ID
            ).first()
    
            if not module:
                raise HTTPException(
                    status_code=404,
                    detail="Module not found"
                )
    
            video.Video_URL = data.Video_URL
            video.course_description = data.course_description
    
            db.commit()
            db.refresh(video)
    
            return {
                "status": True,
                "message": "Video updated successfully",
                "video_id": video.Video_ID
            }
    
        except HTTPException:
            raise
    
        except Exception as e:
    
            db.rollback()
    
            raise HTTPException(
                status_code=500,
                detail=f"Video update failed: {str(e)}"
            )
    
    async def update_live_course_service(self, live_id: str, data: UpdateLiveCourseRequest, db: Session):

        try:
    
            live_session = db.query(LiveCourseTable).filter(
                LiveCourseTable.Live_ID == live_id
            ).first()
    
            if not live_session:
                raise HTTPException(
                    status_code=404,
                    detail="Live session not found"
                )
    
            course = db.query(CourseTable).filter(
                CourseTable.course_id == data.Course_ID
            ).first()
    
            if not course:
                raise HTTPException(
                    status_code=404,
                    detail="Course not found"
                )
    
            if course.course_type.lower() != "live":
                raise HTTPException(
                    status_code=400,
                    detail="Live sessions can only be created for Live courses"
                )
    
            module = db.query(CourseModuleTable).filter(
                CourseModuleTable.Module_ID == data.Module_ID
            ).first()
    
            if not module:
                raise HTTPException(
                    status_code=404,
                    detail="Module not found"
                )
    
            if data.End_time <= data.Start_time:
                raise HTTPException(
                    status_code=400,
                    detail="End time must be greater than start time"
                )
    
            live_session.Meeting_URL = data.Meeting_URL
            live_session.Provider = data.Provider
            live_session.Start_time = data.Start_time
            live_session.End_time = data.End_time
            live_session.Status = data.Status
    
            db.commit()
            db.refresh(live_session)
    
            return {
                "status": True,
                "message": "Live session updated successfully",
                "live_id": live_session.Live_ID
            }
    
        except HTTPException:
            raise
    
        except Exception as e:
    
            db.rollback()
    
            raise HTTPException(
                status_code=500,
                detail=f"Live session update failed: {str(e)}"
            )
    
    async def update_recorded_video_service(self,rec_video_id: str,data: UpdateRecVideoRequest,db: Session):

        try:
    
            rec_video = db.query(CourseRecVideoTable).filter(
                CourseRecVideoTable.Rec_Video_ID == rec_video_id
            ).first()
    
            if not rec_video:
                raise HTTPException(
                    status_code=404,
                    detail="Recorded video not found"
                )
    
            course = db.query(CourseTable).filter(
                CourseTable.course_id == data.Course_ID
            ).first()
    
            if not course:
                raise HTTPException(
                    status_code=404,
                    detail="Course not found"
                )
    
            if course.course_type.lower() != "live":
                raise HTTPException(
                    status_code=400,
                    detail="Recorded videos can only be added to Live courses"
                )
    
            live_session = db.query(LiveCourseTable).filter(
                LiveCourseTable.Live_ID == data.Live_ID
            ).first()
    
            if not live_session:
                raise HTTPException(
                    status_code=404,
                    detail="Live session not found"
                )
            rec_video.Rec_Video_URL = data.Rec_Video_URL
            rec_video.Duration = data.Duration
    
            db.commit()
            db.refresh(rec_video)
    
            return {
                "status": True,
                "message": "Recorded video updated successfully",
                "rec_video_id": rec_video.Rec_Video_ID
            }
    
        except HTTPException:
            raise
    
        except Exception as e:
    
            db.rollback()
    
            raise HTTPException(
                status_code=500,
                detail=f"Recorded video update failed: {str(e)}"
            )
    
    async def update_assessment_service(self,assessment_id: str,data: UpdateAssessmentRequest,db: Session):
        try:
            assessment = db.query(AssessmentTable).filter(
                AssessmentTable.Assessment_ID == assessment_id
            ).first()
    
            if not assessment:
                raise HTTPException(
                    status_code=404,
                    detail="Assessment not found"
                )
    
            module = db.query(CourseModuleTable).filter(
                CourseModuleTable.Module_ID == data.Module_ID
            ).first()
    
            if not module:
                raise HTTPException(
                    status_code=404,
                    detail="Module not found"
                )
    
            if data.Passing_Mark > data.Total_Mark:
                raise HTTPException(
                    status_code=400,
                    detail="Passing mark cannot be greater than total mark"
                )
    
            if data.Duration <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Duration must be greater than 0"
                )
    
            if data.Attempt_Limit <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Attempt limit must be greater than 0"
                )
    
            assessment.Title = data.Title
            assessment.Description = data.Description
            assessment.Total_Mark = data.Total_Mark
            assessment.Passing_Mark = data.Passing_Mark
            assessment.Duration = data.Duration
            assessment.Attempt_Limit = data.Attempt_Limit
            assessment.Status = data.Status
    
            db.commit()
            db.refresh(assessment)
    
            return {
                "status": True,
                "message": "Assessment updated successfully",
                "assessment_id": assessment.Assessment_ID
            }
    
        except HTTPException:
            raise
    
        except Exception as e:
    
            db.rollback()
    
            raise HTTPException(
                status_code=500,
                detail=f"Assessment update failed: {str(e)}"
            )
        
    async def update_question_service(self,question_id: str,data: UpdateQuestionRequest,db: Session):
        try:
    
            question = db.query(QuestionTable).filter(
                QuestionTable.Question_ID == question_id
            ).first()
    
            if not question:
                raise HTTPException(
                    status_code=404,
                    detail="Question not found"
                )
    
            assessment = db.query(AssessmentTable).filter(
                AssessmentTable.Assessment_ID == data.Assessment_ID
            ).first()
    
            if not assessment:
                raise HTTPException(
                    status_code=404,
                    detail="Assessment not found"
                )
    
            if data.Mark <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Mark must be greater than 0"
                )
    
            if data.Position <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Position must be greater than 0"
                )
    
            question.Question_Txt = data.Question_Txt
            question.Mark = data.Mark
            question.Question_Type = data.Question_Type
            question.Explanation = data.Explanation
    
            db.commit()
            db.refresh(question)
    
            return {
                "status": True,
                "message": "Question updated successfully",
                "question_id": question.Question_ID
            }
    
        except HTTPException:
            raise
    
        except Exception as e:
    
            db.rollback()
    
            raise HTTPException(
                status_code=500,
                detail=f"Question update failed: {str(e)}"
            )
        
    async def update_option_service(self,option_id: str,data: UpdateOptionRequest,db: Session):
        try:
    
            option = db.query(optionTable).filter(
                optionTable.Option_ID == option_id
            ).first()
    
            if not option:
                raise HTTPException(
                    status_code=404,
                    detail="Option not found"
                )
    
            question = db.query(QuestionTable).filter(
                QuestionTable.Question_ID == data.Question_ID
            ).first()
    
            if not question:
                raise HTTPException(
                    status_code=404,
                    detail="Question not found"
                )
    
            if data.Position <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Position must be greater than 0"
                )
    
            if data.Is_Correct:
    
                existing_correct = db.query(optionTable).filter(
                    optionTable.Question_ID == data.Question_ID,
                    optionTable.Is_Correct == True,
                    optionTable.Option_ID != option_id
                ).first()
    
                if existing_correct:
                    raise HTTPException(
                        status_code=400,
                        detail="Correct option already exists for this question"
                    )
    
            option.Option_Txt = data.Option_Txt
            option.Is_Correct = data.Is_Correct
    
            db.commit()
            db.refresh(option)
    
            return {
                "status": True,
                "message": "Option updated successfully",
                "option_id": option.Option_ID
            }
    
        except HTTPException:
            raise
    
        except Exception as e:
    
            db.rollback()
    
            raise HTTPException(
                status_code=500,
                detail=f"Option update failed: {str(e)}"
            )

    async def get_full_course_details(self, course_id: str, db: Session):
        try:
            course = db.query(CourseTable).filter(
                CourseTable.course_id == course_id
            ).first()
    
            if not course:
                raise HTTPException(status_code=404, detail="Course not found")
    
            demos = db.query(CourseDemoTable).filter(
                CourseDemoTable.Course_ID == course_id
            ).all()
    
            demo_list = [
                {
                    "demo_id": d.Demo_ID,
                    "title": d.Title,
                    "video_url": d.Video_URL,
                    "duration": d.Duration
                }
                for d in demos
            ]
    
            notes = db.query(CourseNotesTable).filter(
                CourseNotesTable.Course_ID == course_id
            ).all()
    
            notes_list = [
                {
                    "notes_id": n.Notes_ID,
                    "title": n.Title,
                    "file_url": n.File_URL,
                    "file_type": n.File_Type
                }
                for n in notes
            ]
    
            modules = db.query(CourseModuleTable).filter(
                CourseModuleTable.Course_ID == course_id
            ).order_by(CourseModuleTable.Position).all()
    
            module_data = []
    
            for module in modules:
    
                module_dict = {
                    "module_id": module.Module_ID,
                    "title": module.Title,
                    "description": module.Course_Description,
                    "position": module.Position,
                    "content": {}
                }
    
                if course.course_Type.lower() != "live":
    
                    videos = db.query(CourseVideoTable).filter(
                        CourseVideoTable.Module_ID == module.Module_ID
                    ).all()
    
                    module_dict["content"]["videos"] = [
                        {
                            "video_id": v.Video_ID,
                            "video_url": v.Video_URL,
                            "description": v.course_description
                        }
                        for v in videos
                    ]
    
                else:
    
                    live_sessions = db.query(LiveCourseTable).filter(
                        LiveCourseTable.Module_ID == module.Module_ID
                    ).all()
    
                    live_list = []
    
                    for live in live_sessions:
    
                        rec_videos = db.query(CourseRecVideoTable).filter(
                            CourseRecVideoTable.Live_ID == live.Live_ID
                        ).all()
    
                        live_list.append({
                            "live_id": live.Live_ID,
                            "meeting_url": live.Meeting_URL,
                            "provider": live.Provider,
                            "start_time": live.Start_time,
                            "end_time": live.End_time,
                            "status": live.Status,
                            "recordings": [
                                {
                                    "rec_video_id": r.Rec_Video_ID,
                                    "url": r.Rec_Video_URL,
                                    "duration": r.Duration
                                }
                                for r in rec_videos
                            ]
                        })
    
                    module_dict["content"]["live_sessions"] = live_list
    
                assessments = db.query(AssessmentTable).filter(
                    AssessmentTable.Module_ID == module.Module_ID
                ).all()
    
                assessment_list = []
    
                for assess in assessments:
    
                    questions = db.query(QuestionTable).filter(
                        QuestionTable.Assessment_ID == assess.Assessment_ID
                    ).order_by(QuestionTable.Position).all()
    
                    question_list = []
    
                    for q in questions:
    
                        options = db.query(optionTable).filter(
                            optionTable.Question_ID == q.Question_ID
                        ).order_by(optionTable.Position).all()
    
                        question_list.append({
                            "question_id": q.Question_ID,
                            "question_text": q.Question_Txt,
                            "mark": q.Mark,
                            "type": q.Question_Type,
                            "position": q.Position,
                            "options": [
                                {
                                    "option_id": o.Option_ID,
                                    "text": o.Option_Txt,
                                    "is_correct": o.Is_Correct,
                                    "position": o.Position
                                }
                                for o in options
                            ]
                        })
    
                    assessment_list.append({
                        "assessment_id": assess.Assessment_ID,
                        "title": assess.Title,
                        "total_mark": assess.Total_Mark,
                        "passing_mark": assess.Passing_Mark,
                        "duration": assess.Duration,
                        "questions": question_list
                    })
    
                module_dict["content"]["assessments"] = assessment_list
    
                module_data.append(module_dict)
    
            return {
                "status": True,
                "course": {
                    "course_id": course.course_id,
                    "title": course.course_title,
                    "description": course.course_description,
                    "type": course.course_Type,
                    "level": course.level,
                    "language": course.language,
                    "trainer_id":course.instructor_id,
                    "category_id":course.category_id,
                    "duration_hours":course.duration,
                    "key_skill":course.skill_set,
                    "benefits":course.benefits,
                    "required_knowlegde":course.required_knowledge,
                    "price": {
                        "original": course.original_pay,
                        "discount": course.discount_pay
                    },
                    "demo": demo_list,
                    "notes": notes_list,
                    "modules": module_data
                }
            }
    
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch course details: {str(e)}"
            )
    async def get_course_ids_by_status(self, db: Session):
        try:
    
            draft_courses = db.query(CourseTable.course_id).filter(
                CourseTable.draft == True,
                CourseTable.is_active == False
            ).all()
    
            active_courses = db.query(CourseTable.course_id).filter(
                CourseTable.draft == False,
                CourseTable.is_active == True
            ).all()
    
            inactive_courses = db.query(CourseTable.course_id).filter(
                CourseTable.draft == False,
                CourseTable.is_active == False
            ).all()
    
            return {
                "status": True,
                "courses": {
                    "draft": [c.course_id for c in draft_courses],
                    "active": [c.course_id for c in active_courses],
                    "inactive": [c.course_id for c in inactive_courses]
                }
            }
    
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch course IDs by status: {str(e)}"
            )
        
    async def get_instructor_live_sessions(self, user_id: str, db: Session):
        try:
            trainer = db.query(user_access_table).filter(
                user_access_table.user_id == user_id,
                user_access_table.role == "trainer"
            ).first()
    
            if not trainer:
                raise HTTPException(
                    status_code=404,
                    detail="User is not a trainer or does not exist"
                )
    
            live_sessions = db.query(LiveCourseTable).join(
                CourseTable,
                LiveCourseTable.Course_ID == CourseTable.course_id
            ).filter(
                CourseTable.instructor_id == user_id,
                CourseTable.draft == False,
                CourseTable.is_active == True,
                CourseTable.course_Type.ilike("live")
            ).order_by(LiveCourseTable.Start_time.asc()).all()
    
            if not live_sessions:
                return {
                    "status": True,
                    "message": "No live sessions found for this trainer",
                    "live_sessions": []
                }
    
            result = [
                {
                    "live_id": l.Live_ID,
                    "course_id": l.Course_ID,
                    "module_id": l.Module_ID,
                    "start_time": l.Start_time,
                    "end_time": l.End_time,
                    "status": l.Status
                }
                for l in live_sessions
            ]
    
            return {
                "status": True,
                "count": len(result),
                "live_sessions": result
            }
    
        except HTTPException:
            raise
    
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch live sessions: {str(e)}"
            )

    async def delete_course_service(self, course_id: str, db: Session):
        try:
            course = db.query(CourseTable).filter(
                CourseTable.course_id == course_id
            ).first()
    
            if not course:
                raise HTTPException(status_code=404, detail="Course not found")
    
            db.delete(course)
            db.commit()
    
            return {"status": True, "message": "Course deleted successfully (full cascade)"}
    
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_module_service(self, module_id: str, db: Session):
        try:
            module = db.query(CourseModuleTable).filter(
                CourseModuleTable.Module_ID == module_id
            ).first()
    
            if not module:
                raise HTTPException(status_code=404, detail="Module not found")
    
            db.delete(module)
            db.commit()
    
            return {"status": True, "message": "Module deleted successfully"}
    
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        
    async def delete_assessment_service(self, assessment_id: str, db: Session):
        try:
            assessment = db.query(AssessmentTable).filter(
                AssessmentTable.Assessment_ID == assessment_id
            ).first()
    
            if not assessment:
                raise HTTPException(status_code=404, detail="Assessment not found")
    
            db.delete(assessment)
            db.commit()
    
            return {"status": True, "message": "Assessment deleted successfully"}
    
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    
    async def delete_question_service(self, question_id: str, db: Session):
        try:
            question = db.query(QuestionTable).filter(
                QuestionTable.Question_ID == question_id
            ).first()
    
            if not question:
                raise HTTPException(status_code=404, detail="Question not found")
    
            db.delete(question)
            db.commit()
    
            return {"status": True, "message": "Question deleted successfully"}
    
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    
    async def delete_option_service(self, option_id: str, db: Session):
        try:
            option = db.query(optionTable).filter(
                optionTable.Option_ID == option_id
            ).first()
    
            if not option:
                raise HTTPException(status_code=404, detail="Option not found")
    
            db.delete(option)
            db.commit()
    
            return {"status": True, "message": "Option deleted successfully"}
    
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    
    async def delete_notes_service(self, notes_id: str, db: Session):
        try:
            notes = db.query(CourseNotesTable).filter(
                CourseNotesTable.Notes_ID == notes_id
            ).first()
    
            if not notes:
                raise HTTPException(status_code=404, detail="Notes not found")
    
            db.delete(notes)
            db.commit()
    
            return {"status": True, "message": "Notes deleted successfully"}
    
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        
    async def delete_demo_service(self, demo_id: str, db: Session):
        try:
            demo = db.query(CourseDemoTable).filter(
                CourseDemoTable.Demo_ID == demo_id
            ).first()
    
            if not demo:
                raise HTTPException(status_code=404, detail="Demo not found")
    
            db.delete(demo)
            db.commit()
    
            return {"status": True, "message": "Demo deleted successfully"}
    
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_video_service(self, video_id: str, db: Session):
        try:
            video = db.query(CourseVideoTable).filter(
                CourseVideoTable.Video_ID == video_id
            ).first()
    
            if not video:
                raise HTTPException(
                    status_code=404,
                    detail="Video not found"
                )
    
            db.delete(video)
            db.commit()
    
            return {
                "status": True,
                "message": "Video deleted successfully",
                "video_id": video_id
            }
    
        except HTTPException:
            raise
    
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Video deletion failed: {str(e)}"
            )
    
    async def delete_live_service(self, live_id: str, db: Session):
        try:
            live = db.query(LiveCourseTable).filter(
                LiveCourseTable.Live_ID == live_id
            ).first()
    
            if not live:
                raise HTTPException(
                    status_code=404,
                    detail="Live session not found"
                )
    
            db.delete(live)
            db.commit()
    
            return {
                "status": True,
                "message": "Live session deleted successfully",
                "live_id": live_id
            }
    
        except HTTPException:
            raise
    
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Live session deletion failed: {str(e)}"
            )
        
    async def delete_recorded_video_service(self, rec_video_id: str, db: Session):
        try:
            rec_video = db.query(CourseRecVideoTable).filter(
                CourseRecVideoTable.Rec_Video_ID == rec_video_id
            ).first()
    
            if not rec_video:
                raise HTTPException(
                    status_code=404,
                    detail="Recorded video not found"
                )
    
            db.delete(rec_video)
            db.commit()
    
            return {
                "status": True,
                "message": "Recorded video deleted successfully",
                "rec_video_id": rec_video_id
            }
    
        except HTTPException:
            raise
    
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Recorded video deletion failed: {str(e)}"
            )

    async def swap_module_position(self,module_id_1: str,module_id_2: str,db: Session):
        try:
            if module_id_1 == module_id_2:
                raise HTTPException(
                    status_code=400,
                    detail="Both module IDs cannot be the same"
                )
    
            module1 = db.query(CourseModuleTable).filter(
                CourseModuleTable.Module_ID == module_id_1
            ).with_for_update().first()
    
            module2 = db.query(CourseModuleTable).filter(
                CourseModuleTable.Module_ID == module_id_2
            ).with_for_update().first()
    
            if not module1 or not module2:
                raise HTTPException(
                    status_code=404,
                    detail="One or both modules not found"
                )
    
            if module1.Course_ID != module2.Course_ID:
                raise HTTPException(
                    status_code=400,
                    detail="Modules must belong to the same course"
                )
    
            temp_position = module1.Position
            module1.Position = module2.Position
            module2.Position = temp_position
    
            db.commit()
    
            return {
                "status": True,
                "message": "Module positions swapped successfully",
                "course_id": module1.Course_ID,
                "data": [
                    {
                        "module_id": module1.Module_ID,
                        "new_position": module1.Position
                    },
                    {
                        "module_id": module2.Module_ID,
                        "new_position": module2.Position
                    }
                ]
            }
    
        except HTTPException:
            raise
    
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Swap failed: {str(e)}"
            )
        
    async def swap_question_position(
        self,
        question_id_1: str,
        question_id_2: str,
        db: Session
    ):
        try:
            if question_id_1 == question_id_2:
                raise HTTPException(
                    status_code=400,
                    detail="Both question IDs cannot be the same"
                )
    
            q1 = db.query(QuestionTable).filter(
                QuestionTable.Question_ID == question_id_1
            ).with_for_update().first()
    
            q2 = db.query(QuestionTable).filter(
                QuestionTable.Question_ID == question_id_2
            ).with_for_update().first()
    
            if not q1 or not q2:
                raise HTTPException(
                    status_code=404,
                    detail="One or both questions not found"
                )
    
            if q1.Assessment_ID != q2.Assessment_ID:
                raise HTTPException(
                    status_code=400,
                    detail="Questions must belong to the same assessment"
                )
    
            temp = q1.Position
            q1.Position = q2.Position
            q2.Position = temp
    
            db.commit()
    
            return {
                "status": True,
                "message": "Question positions swapped successfully",
                "assessment_id": q1.Assessment_ID,
                "data": [
                    {
                        "question_id": q1.Question_ID,
                        "new_position": q1.Position
                    },
                    {
                        "question_id": q2.Question_ID,
                        "new_position": q2.Position
                    }
                ]
            }
    
        except HTTPException:
            raise
    
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Swap failed: {str(e)}"
            )
        
    async def swap_option_position(
        self,
        option_id_1: str,
        option_id_2: str,
        db: Session
    ):
        try:
            if option_id_1 == option_id_2:
                raise HTTPException(
                    status_code=400,
                    detail="Both option IDs cannot be the same"
                )
    
            opt1 = db.query(optionTable).filter(
                optionTable.Option_ID == option_id_1
            ).with_for_update().first()
    
            opt2 = db.query(optionTable).filter(
                optionTable.Option_ID == option_id_2
            ).with_for_update().first()
    
            if not opt1 or not opt2:
                raise HTTPException(
                    status_code=404,
                    detail="One or both options not found"
                )
    
            if opt1.Question_ID != opt2.Question_ID:
                raise HTTPException(
                    status_code=400,
                    detail="Options must belong to the same question"
                )
    
            temp = opt1.Position
            opt1.Position = opt2.Position
            opt2.Position = temp
    
            db.commit()
    
            return {
                "status": True,
                "message": "Option positions swapped successfully",
                "question_id": opt1.Question_ID,
                "data": [
                    {
                        "option_id": opt1.Option_ID,
                        "new_position": opt1.Position
                    },
                    {
                        "option_id": opt2.Option_ID,
                        "new_position": opt2.Position
                    }
                ]
            }
    
        except HTTPException:
            raise
    
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Swap failed: {str(e)}"
            )
        
    async def activate_course(self, course_id: str,db: Session,background_tasks):
        try:
            course = db.query(CourseTable).filter(
                CourseTable.course_id == course_id
            ).first()

            if not course:
                return False, "Course not found"

            video_exists = db.query(
                exists().where(CourseVideoTable.Course_ID == course_id)
            ).scalar()

            live_exists = db.query(
                exists().where(LiveCourseTable.Course_ID == course_id)
            ).scalar()

            if course.course_Type.lower() == "recorded":
                if not video_exists:
                    return False, "Recorded courses must contain at least one video."
                if live_exists:
                    return False, "Recorded courses cannot contain live sessions."

            elif course.course_Type.lower() == "live":
                if not live_exists:
                    return False, "Live courses must contain at least one scheduled live session."
                if video_exists:
                    return False, "Live courses cannot contain recorded videos."

                future_live = db.query(
                    exists().where(
                        and_(
                            LiveCourseTable.Course_ID == course_id,
                            LiveCourseTable.Start_time > datetime.now()
                        )
                    )
                ).scalar()

                if not future_live:
                    return False, "Live session must be scheduled in future"

            else:
                return False, "Invalid course type"

            module_exists = db.query(
                exists().where(CourseModuleTable.Course_ID == course_id)
            ).scalar()

            if not module_exists:
                return False, "Course must have at least one module"

            invalid_assessment = db.query(AssessmentTable.Assessment_ID)\
                .join(CourseModuleTable,
                      CourseModuleTable.Module_ID == AssessmentTable.Module_ID)\
                .filter(CourseModuleTable.Course_ID == course_id)\
                .outerjoin(QuestionTable,
                           QuestionTable.Assessment_ID == AssessmentTable.Assessment_ID)\
                .group_by(AssessmentTable.Assessment_ID)\
                .having(func.count(QuestionTable.Question_ID) == 0)\
                .first()

            if invalid_assessment:
                return False, "Assessment must contain at least one question"

            invalid_question = db.query(QuestionTable.Question_ID)\
                .join(AssessmentTable,
                      AssessmentTable.Assessment_ID == QuestionTable.Assessment_ID)\
                .join(CourseModuleTable,
                      CourseModuleTable.Module_ID == AssessmentTable.Module_ID)\
                .filter(CourseModuleTable.Course_ID == course_id)\
                .outerjoin(optionTable,
                           optionTable.Question_ID == QuestionTable.Question_ID)\
                .group_by(QuestionTable.Question_ID)\
                .having(func.count(optionTable.Option_ID) < 2)\
                .first()

            if invalid_question:
                return False, "Each question must have at least 2 options"

            db.query(CourseTable).filter(
                CourseTable.course_id == course_id
            ).update({
                CourseTable.is_active: True,
                CourseTable.draft: False
            })

            db.commit()

            trainer_email = course.instructor_id  
            trainer = db.query(user_profile_table).filter(user_profile_table.user_id == trainer_email).first()
            trainer_idd= trainer.user_email

            subject = "Course Activated – Now Live"
            
            body = course_active_template(course.course_id,course.course_title,course.course_Type,course.duration,course.level,course.language)
            background_tasks.add_task(send_email, trainer_idd, subject, body)
            return True, "Course activated successfully"
        except Exception as e:
            db.rollback()
            return False, f"Internal server error {str(e)}"

    
    