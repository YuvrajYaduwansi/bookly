from pydantic import BaseModel,Field
import uuid
from datetime import datetime,date



class ReviewModel(BaseModel):
    uid:uuid.UUID
    rating:int=Field(ge=1,le=5)
    review_text:str
    user_uid:uuid.UUID
    book_uid:uuid.UUID
    created_at:datetime
    updated_at:datetime


class ReviewCreateModel(BaseModel):
    rating:int
    review_text:str

