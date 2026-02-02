from fastapi import FastAPI, HTTPException, Depends, Response
from pydantic import BaseModel
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from authx import AuthX, AuthXConfig
from typing import Optional, List
import requests
import math
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
async def root():
    return {
        "message": "API для поиска мест работает!",
        "usage": "Отправьте POST запрос на /api/search_places",
        "example": {
            "city_name": "Москва",
            "amenity": "cafe",
            "radius": 1500,
            "limit": 10,
            "username": "dendi31"
        }
    }
    
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


@app.get('/api/places')
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
    username: Optional[str] = "dendi31" 

# Модель для выходных данных
class PlaceResponse(BaseModel):
    name: str
    lat: float
    lon: float
    address: str
    type: str
    distance: float 
    website: Optional[str] = None
    phone: Optional[str] = None
    opening_hours: Optional[str] = None
    score: Optional[float] = None

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Вычисляет расстояние между двумя точками на Земле в метрах
    """
    R = 6371000  # Радиус Земли в метрах
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2) ** 2
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return round(distance, 2)

# Находим координаты по названию города
def citygeocodes(city_name):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': city_name,
            'format': 'json',
            'limit': 1
        }
        headers = {"User-Agent": "AI_TravelHelper"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        
        if not data:
            return None
        return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        print(f"Ошибка геокодирования: {e}")
        return None

# Запрос к апи OSM с выбором категории
def search_places(lat, lon, place_type="cafe", radius=1500, limit=10):
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
        
        # Спорт
        "sports_centre": ["leisure", "sports_centre"],
        
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
    
    try:
        url = "https://overpass-api.de/api/interpreter"
        response = requests.post(url, data=query, timeout=30)
        
        if response.status_code != 200:
            return []
        
        data = response.json()
    except Exception as e:
        print(f"Ошибка запроса к Overpass API: {e}")
        return []
    
    places = []
    
    for element in data["elements"][:limit]:
        # Получение названия
        tags = element.get("tags", {})
        if "name" not in tags:
            continue
        name = tags.get("name", "Без названия")
        
        # Получение координат
        if "lat" in element and "lon" in element:
            place_lat = element["lat"]
            place_lon = element["lon"]
        elif "center" in element:
            place_lat = element["center"]["lat"]
            place_lon = element["center"]["lon"]
        else:
            continue
        
        distance = calculate_distance(lat, lon, place_lat, place_lon)
        
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
            "distance": distance,  
            "website": website,
            "phone": phone,
            "opening_hours": opening_hours
        })
    
    return places

@app.post('/api/search_places')
async def get_places_endpoint(request: PlaceRequest):
    coords = citygeocodes(request.city_name)

    if not coords:
        raise HTTPException(400, detail="Город не найден")

    lat, lon = coords

    places = search_places(
        lat=lat,
        lon=lon,
        place_type=request.amenity,
        radius=request.radius,
        limit=request.limit
    )

    if not places:
        return {
            "city": request.city_name,
            "amenity": request.amenity,
            "found": 0,
            "user": request.username,
            "places": []
        }
        
    username = request.username if request.username in USER_PROFILE else "dendi31"
    user_vector = USER_PROFILE[username]["vector"]

    for place in places:
        place_vector = place_to_vector(
            place["type"],
            place["distance"]
        )

        score = cosine_similarity(user_vector, place_vector)
        place["score"] = round(score, 3)

    # сортируем по релевантности
    places.sort(key=lambda x: x["score"], reverse=True)

    return {
        "city": request.city_name,
        "amenity": request.amenity,
        "found": len(places),
        "user": username,
        "places": places
    }


PLACE_TYPES = [
    "cafe",
    "restaurant",
    "park",
    "museum",
    "bar",
    "theatre",
    "cinema",
    "sports_centre",
    "hospital",
    "pharmacy",
    "bank",
    "hotel",
    "attraction",
    "monument",
    "mall"
]

TYPE_INDEX = {t: i for i, t in enumerate(PLACE_TYPES)}


def place_to_vector(place_type: str, distance: float):
    vector = [0.0] * (len(PLACE_TYPES) + 1)

    if place_type in TYPE_INDEX:
        vector[TYPE_INDEX[place_type]] = 1.0

    # расстояние: чем ближе — тем лучше
    vector[-1] = max(0.0, 1.0 - distance / 2000)

    return vector


def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


USER_PROFILE = {
    "dendi31": {
        # cafe, restaurant, park, museum, bar, theatre, cinema, sports_centre, 
        # hospital, pharmacy, bank, hotel, attraction, monument, mall, distance
        "vector": [1.0, 0.5, 0.6, 0.9, 0.5, 0.7, 0.8, 0.3, 0.1, 0.2, 0.1, 0.4, 0.9, 0.7, 0.3, 0.6]
    }
}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Запуск сервера на http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
