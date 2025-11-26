import requests
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
        cafes = []
    return float(data[0]['lat']), float(data[0]['lon'])

# Обычный запрос к апи OSM
def searchcodes(lat, lon, radius=1500, limit=10):
    query = f'''
    [out:json];
    node["amenity"="cafe"](around:{radius},{lat},{lon});
    out center;
    '''
    url = "https://overpass-api.de/api/interpreter"
    response = requests.post(url, data=query)
    data = response.json()
    
    cafes = []
    
    for element in data["elements"][:limit]:
        # Получения названия
        tags = element.get("tags", {})
        name = tags.get("name", "Без названия")
        # Координаты
        lat = element["lat"]
        lon = element["lon"]
        
        # Получения адреса
        street = tags.get("addr:street", "")
        house = tags.get("addr:housenumber", "")
        city = tags.get("addr:city", "")
        postcode = tags.get("addr:postcode", "")
        
        # Создание полного адреса
        parts = [city, street, house, postcode]
        address = ", ".join([p for p in parts if p]) 
        # Компановка в один список
        cafes.append({
        "name": name,
        "lat": lat,
        "lon": lon,
        "address": address if address else "Адрес не указан"
    })
    
    return cafes

city = input("Введите название города: ")

coords = citygeocodes(city)
if not coords:
    print("Город не найден, проверьте написание!")
else:
    lat, lon = coords
    cafes = searchcodes(lat, lon)

print("\nКафе поблизости:")
for c in cafes:
    print(f"- {c['name']} ({c['lat']}, {c['lon']}), {c['address']}")