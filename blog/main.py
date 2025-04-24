from fastapi import FastAPI, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import HTTPException
from fastapi_pagination import Page, add_pagination, paginate
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from . import schemas, models
from .database import engine
from .deps import get_db
from .auth import create_access_token, get_current_user

app = FastAPI()
add_pagination(app)
models.Base.metadata.create_all(bind = engine) 

#Authentication
@app.post('/login', status_code=status.HTTP_200_OK, response_model=schemas.Token, tags=["Authentication"])

def login(request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == request.username).first()
    if not user:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Credentials")
    if not verify_password(request.password, user.password):
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Password")
    access_token = create_access_token(data = {"sub" : user.email})
    return {"access_token": access_token, "token_type": "bearer"}

#Hashed Password
pwd_cnt = CryptContext(schemes=["bcrypt"], deprecated = "auto")

#Create an USER
@app.post('/user',status_code=status.HTTP_201_CREATED, tags=["User"])
def create_user(request: schemas.User, db: Session = Depends(get_db)):
    hashed_password = pwd_cnt.hash(request.password)
    existing_user = db.query(models.User).filter(models.User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    new_user = models.User(
		email=request.email,
		name = request.name,
		password=hashed_password
	)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

#Create a Blog.
@app.post('/blog', status_code=status.HTTP_201_CREATED, response_model=schemas.BlogOut, tags=["Blog"])
def create_blog(request: schemas.BlogCreate, db: Session = Depends(get_db)):
    existing_blog = db.query(models.Blog).filter(models.Blog.title == request.title).first()
    existing_author_name = db.query(models.Blog).filter(models.Blog.author_name == request.author_name).first()
    if existing_blog and existing_author_name:
        raise HTTPException(status_code=400, detail="Blog already exists")
    new_blog = models.Blog(
        title=request.title,
        author_name=request.author_name,
        body=request.body,
        created_by=request.created_by
    )
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)
    return new_blog

#Get all Blog Detials from Blog Tag
@app.get('/blog',  response_model=Page[schemas.ShowBlog], status_code= status.HTTP_200_OK, tags=["Blog"])
async def get_blog(db: Session = Depends(get_db), current_user: schemas.User= Depends(get_current_user)):
	blogs = db.query(models.Blog).all()
	return paginate(blogs)


add_pagination(app)
# Get Single Blog Details from Blog Tag
@app.get('/blog/{id}', status_code=status.HTTP_200_OK, tags=["Blog"])
def get_blog_by_id(id: int, db: Session = Depends(get_db), current_user: schemas.User= Depends(get_current_user)):
    blog = db.query(models.Blog).filter(models.Blog.blog_id == id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    blog_name = db.query(models.Blog.title).filter(models.Blog.blog_id == id).scalar()
    review = db.query(models.Ratings).filter(models.Ratings.blog_name == blog_name).all()
    return {
    "blog": blog,
    "reviews": review
    }


#Update a Blog
@app.put('/blog/{id}', status_code=status.HTTP_200_OK, tags=["Blog"])
def update(id: int, request: schemas.BlogUpdate ,db: Session = Depends(get_db), current_user: schemas.User= Depends(get_current_user)):
    blog = db.query(models.Blog).filter(models.Blog.blog_id == id)
    if not blog.first():
          raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Blog with {id} not found")
    blog.update(request.model_dump(), synchronize_session=False)
    db.commit()
    return blog

#Delte a blog
@app.delete('/blog/{id}', status_code=status.HTTP_404_NOT_FOUND, tags=["Blog"])
def delete_blog_by_id(id: int, db: Session = Depends(get_db), current_user: schemas.User= Depends(get_current_user)):
    blog = db.query(models.Blog).filter(models.Blog.blog_id == id).delete(synchronize_session=False)
    db.commit()
    return "done"

#Create a Rating
@app.post('/rating', status_code=status.HTTP_201_CREATED, tags = ["Ratings"])
def create_rating(request: schemas.Rating, db: Session = Depends(get_db), current_user: schemas.User= Depends(get_current_user)):
    blog = db.query(models.Blog).filter(models.Blog.title == request.blog_name).first()
    if not blog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blog with title '{request.blog_name}' does not exist"
        )
    new_rating = models.Ratings(
        email=request.email,
        rating=request.rating,
        blog_name=request.blog_name
    )
    db.add(new_rating)
    db.commit()
    db.refresh(new_rating)
    return new_rating
	
#Get all Rating Detials
@app.get('/rating/rating', status_code= status.HTTP_200_OK, tags=["Ratings"])
def get_ratings(db: Session = Depends(get_db), current_user: schemas.User= Depends(get_current_user)):
	blogs = db.query(models.Ratings).all()
	return blogs

# Update a Rating
@app.put('/rating/update', status_code=status.HTTP_200_OK, tags=["Ratings"])
def update(title: str, request: schemas.RatingUpdate, db: Session = Depends(get_db), current_user: schemas.User= Depends(get_current_user)):
    rating = db.query(models.Ratings).filter(models.Ratings.blog_name == title).first()
    
    if not rating:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Blog with title '{title}' not found")
    
    # Update fields manually
    rating.rating = request.rating
    rating.email = request.email
    rating.blog_name = request.blog_name

    db.commit()
    db.refresh(rating)
    return rating

#Delte a Rating
@app.delete('/rating/delete', status_code=status.HTTP_404_NOT_FOUND, tags=["Ratings"])
def delete_blog_by_title(title: str, db: Session = Depends(get_db), current_user: schemas.User= Depends(get_current_user)):
    blog = db.query(models.Blog).filter(models.Blog.blog_name == title).delete(synchronize_session=False)
    db.commit()
    return "done"


def verify_password(plain_password, hashed_password):
    return pwd_cnt.verify(plain_password, hashed_password)
