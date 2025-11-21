from fastapi import FastAPI, HTTPException, Depends, Response
from pydantic import BaseModel
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from authx import AuthX, AuthXConfig

app = FastAPI()
engine = create_async_engine('sqlite+aiosqlite:///database.db')

new_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    async with new_session() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]

class Base(DeclarativeBase):
    pass

class PlaceModel(Base):
    __tablename__ = "places"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    adding_data: Mapped[str]

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post('/setup_database')
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    return {"ok": True}

class PlaceAddSchema(BaseModel):
    name: str
    adding_data: str

class PlaceSchema(PlaceAddSchema):
    id: int


@app.get('/places')
async def get_places(session: SessionDep):
    query = select(PlaceModel)
    result = await session.execute(query)
    return result.scalars().all()

class NewPlace(BaseModel):
    name: str
    adding_data: str

# @app.post('/places')
# async def add_places(data: PlaceAddSchema, session: SessionDep):
#     new_place = PlaceModel(
#         name=data.name,
#         adding_data=data.adding_data
#     )
#     session.add(new_place)
#     await session.commit()
#     return {"ok": True}

@app.post('/places')
async def add_places(
    name: str,
    adding_data: str,
    session: SessionDep
):
    new_place = PlaceModel(
        name=name,
        adding_data=adding_data
    )
    session.add(new_place)
    await session.commit()
    return {"ok": True}

config = AuthXConfig()
config.JWT_SECRET_KEY = "SECRET_KEY"
config.JWT_ACCESS_COOKIE_NAME = "my_access_token"
config.JWT_TOKEN_LOCATION = ["cookies"]

security = AuthX(config=config)


@app.post('/login')
def login(username: str, password: str, response: Response):
    if username == "dendi31" and password == "12345qwerty":
        token = security.create_access_token(uid=username)
        response.set_cookie(config.JWT_ACCESS_COOKIE_NAME, token)
        return {"access_token": token}
    raise HTTPException(401, detail={"message": "Bad credentials"})


@app.get("/protected", dependencies=[Depends(security.access_token_required)])
def get_protected():
    return {"message": "Hello World"}