from sqlalchemy import Column, String, BigInteger, DateTime, Date, func, ForeignKey, Integer, Boolean
from Models.User_Tables.User_Profile import Base

class LiveAttendanceTable(Base):
    __tablename__ = "live_attendance_table"

    Live_Attendance_ID = Column(String(50), primary_key=True)
    User_ID = Column(String(50),ForeignKey("user_profile.user_id"),nullable=False)
    Live_Class_ID = Column(String(50),ForeignKey("live_course_table.Live_ID"),nullable=False,)
    Module_ID = Column(String(50),ForeignKey("course_module_table.Module_ID"),nullable=False)
    
    Attended_Live = Column(Boolean, default=False)
    Watched_Recording = Column(Boolean, default=False)
    Is_Present = Column(Boolean, default=False)
    
    Completed_At = Column(DateTime)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, default=func.now())
