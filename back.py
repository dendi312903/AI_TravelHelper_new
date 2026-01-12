from fastapi import FastAPI, HTTPException, Depends, Response
from pydantic import BaseModel
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from authx import AuthX, AuthXConfig
from typing import Optional, List
import requests

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

# Модель для входных данных
class PlaceRequest(BaseModel):
    city_name: str
    amenity: str
    radius: Optional[int] = 1500
    limit: Optional[int] = 10

# Модель для выходных данных
class PlaceResponse(BaseModel):
    name: str
    lat: float
    lon: float
    address: str
    type: str
    website: Optional[str] = None
    phone: Optional[str] = None
    opening_hours: Optional[str] = None

# Находим координаты по названию города
def citygeocodes(city_name):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': city_name,
        'format': 'json',
        'limit': 1
    }
    headers = {"User-Agent": "AI_TravelHelper"}
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    
    if not data:
        return None
    return float(data[0]['lat']), float(data[0]['lon'])

# Запрос к апи OSM с выбором категории
def search_places(lat, lon, place_type="cafe", radius=1500, limit=10):
    """
    Ищет места определенного типа в радиусе от координат.
    
    Доступные типы мест:
    - cafe, restaurant, fast_food - еда и напитки
    - bar, pub, biergarten - бары и пабы
    - museum, theatre, cinema - культура
    - hotel, hostel, guest_house - жилье
    - pharmacy, hospital, clinic - медицина
    - bank, atm - финансы
    - supermarket, mall - магазины
    - park, playground - парки и отдых
    """
    
    # Словарь соответствия типов мест тегам OSM
    place_tags = {
        # Еда и напитки
        "cafe": ["amenity", "cafe"],
        "restaurant": ["amenity", "restaurant"],
        "fast_food": ["amenity", "fast_food"],
        "bar": ["amenity", "bar"],
        "pub": ["amenity", "pub"],
        "biergarten": ["amenity", "biergarten"],
        
        # Культура и развлечения
        "museum": ["tourism", "museum"],
        "theatre": ["amenity", "theatre"],
        "cinema": ["amenity", "cinema"],
        "gallery": ["tourism", "gallery"],
        
        # Жилье
        "hotel": ["tourism", "hotel"],
        "hostel": ["tourism", "hostel"],
        "guest_house": ["tourism", "guest_house"],
        
        # Медицина
        "pharmacy": ["amenity", "pharmacy"],
        "hospital": ["amenity", "hospital"],
        "clinic": ["amenity", "clinic"],
        
        # Финансы
        "bank": ["amenity", "bank"],
        "atm": ["amenity", "atm"],
        
        # Магазины
        "supermarket": ["shop", "supermarket"],
        "mall": ["shop", "mall"],
        
        # Парки и отдых
        "park": ["leisure", "park"],
        "playground": ["leisure", "playground"],
        
        # Достопримечательности
        "attraction": ["tourism", "attraction"],
        "monument": ["historic", "monument"],
    }
    
    # Получаем тег для выбранного типа
    if place_type not in place_tags:
        tag_key, tag_value = "amenity", "cafe"
    else:
        tag_key, tag_value = place_tags[place_type]
    
    # Формируем запрос Overpass QL
    query = f'''
    [out:json];
    (
      node["{tag_key}"="{tag_value}"](around:{radius},{lat},{lon});
      way["{tag_key}"="{tag_value}"](around:{radius},{lat},{lon});
      relation["{tag_key}"="{tag_value}"](around:{radius},{lat},{lon});
    );
    out center;
    '''
    
    url = "https://overpass-api.de/api/interpreter"
    response = requests.post(url, data=query)
    
    if response.status_code != 200:
        return []
    
    data = response.json()
    
    places = []
    
    for element in data["elements"][:limit]:
        # Получение названия
        tags = element.get("tags", {})
        name = tags.get("name", "Без названия")
        
        # Получение координат
        if "lat" in element and "lon" in element:
            place_lat = element["lat"]
            place_lon = element["lon"]
        elif "center" in element:
            place_lat = element["center"]["lat"]
            place_lon = element["center"]["lon"]
        else:
            continue  # Пропускаем если нет координат
        
        # Получение адреса
        street = tags.get("addr:street", "")
        house = tags.get("addr:housenumber", "")
        city = tags.get("addr:city", "")
        postcode = tags.get("addr:postcode", "")
        
        # Создание полного адреса
        parts = [city, street, house, postcode]
        address = ", ".join([p for p in parts if p])
        
        # Дополнительная информация
        website = tags.get("website", "")
        phone = tags.get("phone", "")
        opening_hours = tags.get("opening_hours", "")
        
        places.append({
            "name": name,
            "lat": place_lat,
            "lon": place_lon,
            "address": address if address else "Адрес не указан",
            "type": place_type,
            "website": website,
            "phone": phone,
            "opening_hours": opening_hours
        })
    
    return places

@app.post('/get_places')
async def get_places(request: PlaceRequest):
    # Получаем координаты города
    coords = citygeocodes(request.city_name)
    
    if not coords:
        return {
            "error": "Город не найден",
            "message": "Проверьте правильность написания названия города"
        }
    
    lat, lon = coords
    
    # Ищем места
    places = search_places(
        lat=lat, 
        lon=lon, 
        place_type=request.amenity, 
        radius=request.radius, 
        limit=request.limit
    )
    
    # Возвращаем результат
    return {
        "city": request.city_name,
        "coordinates": {"latitude": lat, "longitude": lon},
        "amenity": request.amenity,
        "radius": request.radius,
        "found": len(places),
        "places": places
    }

# Дополнительный эндпоинт для проверки работы API
@app.get('/')
async def root():
    return {
        "message": "API для поиска мест работает!",
        "usage": "Отправьте POST запрос на /get_places",
        "example": {
            "city_name": "Москва",
            "amenity": "cafe",
            "radius": 1500,
            "limit": 10
        }
    }