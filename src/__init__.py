from fastapi import FastAPI
from src.books.routes import book_router
from contextlib import asynccontextmanager
from src.db.main import engine
from src.db.main import init_db
from src.auth.routes import auth_router
from src.reviews.routes import review_router
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

app.include_router(book_router,prefix=f"/api/{version}/books",tags=["books"])
app.include_router(auth_router,prefix=f"/api/{version}/auth",tags=["auth"])
app.include_router(review_router,prefix=f"/api/{version}/reviews",tags=["reviews"])

