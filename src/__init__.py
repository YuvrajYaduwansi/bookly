from fastapi import FastAPI,status
from src.books.routes import book_router
from contextlib import asynccontextmanager
from src.db.main import engine
from src.db.main import init_db
from src.auth.routes import auth_router
from src.reviews.routes import review_router
from src.tags.routes import tags_router
from .errors import register_all_errors
from src.middleware import register_middleware
@asynccontextmanager
async def lifespan(app:FastAPI):
    print("Starting up...")
    await init_db()
    yield
    print("Shutting down...")


version='v1'

# removed lifespan as it is not needed, we'll use alembic and not rely on lifespan for db changes
# app=FastAPI(title="Bookly",
#             description="A simple book API for book review web service",
#             version=version,
#             lifespan=lifespan)

app=FastAPI(title="Bookly",
            description="A simple book API for book review web service",
version=version)

register_all_errors(app)
register_middleware(app)


app.include_router(book_router,prefix=f"/api/{version}/books",tags=["books"])
app.include_router(auth_router,prefix=f"/api/{version}/auth",tags=["auth"])
app.include_router(review_router,prefix=f"/api/{version}/reviews",tags=["reviews"])
app.include_router(tags_router, prefix=f"/api/{version}/tags", tags=["tags"])
