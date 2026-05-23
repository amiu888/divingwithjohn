from pydantic import BaseModel, EmailStr
from typing import Optional

class ContactCreate(BaseModel):
    name: Optional[str] = None
    email: EmailStr
    message: str

class BookingCreate(BaseModel):
    course_id: str
    user_email: EmailStr
    date: str

class UserCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    provider: Optional[str] = None
    provider_id: Optional[str] = None

class CourseIn(BaseModel):
    title: str
    description: Optional[str] = None
    level: Optional[str] = None
    stars: Optional[int] = 1
    depth: Optional[str] = None

class TestimonialIn(BaseModel):
    name: str
    location: Optional[str] = None
    quote: str
    stars: Optional[int] = 5
    sort_order: Optional[int] = 0

class GalleryItemIn(BaseModel):
    icon: Optional[str] = '🤿'
    caption: Optional[str] = None
    sort_order: Optional[int] = 0

class FAQItemIn(BaseModel):
    question: str
    answer: str
    sort_order: Optional[int] = 0

class LocationIn(BaseModel):
    flag: Optional[str] = None
    name: str
    description: Optional[str] = None
    sort_order: Optional[int] = 0
