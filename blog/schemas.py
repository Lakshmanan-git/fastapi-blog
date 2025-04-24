from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date
from typing import Optional	

#For BLog
class BlogCreate(BaseModel):
	title: str
	author_name : str
	body: str
	created_by : str

class BlogOut(BaseModel):
    blog_id: int
    title: str
    author_name: str
    body: str
    created_by: str
    created_date: date
    updated_datetime: Optional[datetime]

    model_config = {
    "from_attributes": True
}

class BlogUpdate(BaseModel):
    title: str
    author_name: str
    body: str
    created_by: str
    updated_datetime: Optional[datetime]

    model_config = {
        "from_attributes": True
    }


class ShowBlog(BaseModel):
    blog_id: int
    title: str
    author_name: str
    body: str
    created_by: str
    created_date: date
    
    class Config:
        orm_mode = True

#For User
class User(BaseModel):
	name: str
	password: str
	email: EmailStr

# For Ratings
class Rating(BaseModel):
	rating: int = Field(..., ge=1, le=5)
	email: EmailStr
	blog_name: str

# For showing a rating in a response
class RatingOut(Rating):
    id: int

    model_config = {
    "from_attributes": True
}

#Ratings Update
class RatingUpdate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    email: EmailStr
    blog_name: str

    model_config = {
        "from_attributes": True
    }

#Ratings Update
class Login(BaseModel):
    username: EmailStr
    password: str

#Not used. If used it written name and useremail when try to login instead we used Token
class LoginOut(BaseModel):
    name: str
    username: EmailStr

    model_config = {
        "from_attributes": True
    }

class Token(BaseModel):
     access_token: str
     token_type: str


class TokenData(BaseModel):
     email: Optional[str] = None