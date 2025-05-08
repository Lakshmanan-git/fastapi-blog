from fastapi import FastAPI, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
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

#Welcome Message
@app.get('/',tags=["Welcome Message"])
def hello():
     return {"Message" : "Welcome to the blog app."}

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
    return {"msg": f"New User successfully created."}

#Update a User
@app.put('/user/{email}', status_code=status.HTTP_200_OK, tags=["User"])
def update_user(email:str, request: schemas.UserUpdate ,db: Session = Depends(get_db), current_user: schemas.User= Depends(get_current_user)):
    new_email = db.query(models.User).filter(models.User.email == email)
    if not new_email.first():
          raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"User with {email} not found")
    if request.password:
        hashed_password = pwd_cnt.hash(request.password)
        update_data = request.model_dump()
        update_data["password"] = hashed_password
    else:
        update_data = request.model_dump(exclude_unset=True)

    new_email.update(update_data, synchronize_session=False)
    db.commit()

    return {"msg": f"User {email} updated successfully."}

#Get all Blog Detials 
@app.get('/blog',  response_model=Page[schemas.ShowBlog], status_code= status.HTTP_200_OK, tags=["Blog"])
async def get_blog(db: Session = Depends(get_db)):
	blogs = db.query(models.Blog).all()
	return paginate(blogs)

# Get Blog by ID
@app.get('/blog/{id}', status_code=status.HTTP_200_OK, tags=["Blog"])
def get_blog_by_id(id: int, db: Session = Depends(get_db)):
    blog = db.query(models.Blog).filter(models.Blog.blog_id == id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    blog_name = db.query(models.Blog.title).filter(models.Blog.blog_id == id).scalar()
    review = db.query(models.Ratings).filter(models.Ratings.blog_name == blog_name).all()
    return {
    "blog": blog,
    "reviews": review
    }

#Create a Blog.
@app.post('/blog', status_code=status.HTTP_201_CREATED, response_model=schemas.BlogOut, tags=["Blog"])
def create_blog(request: schemas.BlogCreate, db: Session = Depends(get_db), current_user: schemas.User= Depends(get_current_user)):
    existing_blog = db.query(models.Blog).filter(models.Blog.title == request.title).first()
    existing_author_name = db.query(models.Blog).filter(models.Blog.author_name == request.author_name).first()
    if existing_blog and existing_author_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Blog already exists")
    new_blog = models.Blog(
        title=request.title,
        author_name=request.author_name,
        body=request.body,
        created_by =  current_user.email
    )
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)
    return new_blog

add_pagination(app)

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
@app.delete('/blog', status_code=status.HTTP_404_NOT_FOUND, tags=["Blog"])
def delete_blog(request:schemas.BlogDelete, db: Session = Depends(get_db), current_user: schemas.User= Depends(get_current_user)):
    if(request.email != current_user.email):
         raise HTTPException(
              status_code = status.HTTP_403_FORBIDDEN,
              detail="The current user is not authorized to delete this blog."
         )
    blog_query = db.query(models.Blog).filter(
        models.Blog.created_by == request.email,
        models.Blog.title == request.title
    )
    blog = blog_query.first()
    if not blog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Blog is found that is created by the current user."
        )
    blog_query.delete(synchronize_session=False)
    db.commit()
    return {"detail": "Blog deleted successfully"}

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
        email=current_user.email,
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

# Update Ratings
@app.put('/rating/update', status_code=status.HTTP_200_OK, tags=["Ratings"])
def update_rating(
    request: schemas.RatingUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    rating_query = db.query(models.Ratings).filter(
        models.Ratings.blog_name == request.blog_name,
        models.Ratings.email == current_user.email
    )
    rating = rating_query.first()
    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You do not have a rating for this blog, or the blog does not exist."
        )
    rating_query.update(request.model_dump(exclude_unset=True), synchronize_session=False)
    db.commit()
    return {"msg": "Rating updated successfully"}


#Delte a Rating
@app.delete('/rating/delete', status_code=status.HTTP_200_OK, tags=["Ratings"])
def delete_blog(request: schemas.RatingDelete,
                         db: Session = Depends(get_db),
                         current_user: schemas.User= Depends(get_current_user)):
    if request.email != current_user.email:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                             detail="The current user is not authorized to delete this rating."
        )
    rating_query = db.query(models.Ratings).filter(
        models.Ratings.email == request.email,
        models.Ratings.blog_name == request.blog_name
    )
    rating = rating_query.first()
    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No rating found for this blog by the current user."
        )
    rating_query.delete(synchronize_session=False)
    db.commit()
    return {"detail": "Rating deleted successfully"}


def verify_password(plain_password, hashed_password):
    return pwd_cnt.verify(plain_password, hashed_password)
