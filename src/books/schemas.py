from pydantic import BaseModel
import uuid
from datetime import datetime,date
from src.reviews.schemas import ReviewModel
from typing import List
class Book(BaseModel):
    uid:uuid.UUID
    title:str
    author:str
    language:str
    page_count:int
    publisher:str
    published_date:date
    created_at:datetime
    updated_at:datetime


class BookDetailModel(Book):
    reviews:List[ReviewModel]

class BookCreateModel(BaseModel):
    title:str
    author:str
    publisher:str
    language:str
    page_count:int
    published_date:str

class BookUpdateModel(BaseModel):
    title:str
    author:str
    publisher:str
    published_date:str
    page_count:int
    language:str

   