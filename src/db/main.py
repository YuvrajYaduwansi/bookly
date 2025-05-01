from sqlmodel import create_engine,SQLModel,text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from src.config import config
from src.db.models import Book
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker


# Replace postgresql:// with postgresql+asyncpg:// in the URL'
# async_db_url not needed anymore as we directly put +asyncpg in env var
# async_db_url = config.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')
engine = create_async_engine(config.DATABASE_URL, echo=True,connect_args={"ssl":"require"})

async def init_db():
    async with engine.begin() as conn:
        # statement=text("SELECT 'Hello World';")
        # result=await conn.execute(statement)
        # print(result.all())
        from src.db.models import Book
        await conn.run_sync(SQLModel.metadata.create_all)



async def get_session()->AsyncSession:
    
    Session=sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False

    )

    async with Session() as session:
        yield session