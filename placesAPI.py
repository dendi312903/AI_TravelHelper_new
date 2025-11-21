import requests

# Москва, Красная площадь
lat = 55.7539
lon = 37.6208
radius = 500  # радиус в метрах

query = f"""
[out:json];
node
  ["amenity"="cafe"]
  (around:{radius},{lat},{lon});
out center;
"""

url = "https://overpass-api.de/api/interpreter"
response = requests.post(url, data=query)
data = response.json()

cafes = []

for element in data["elements"]:
    tags = element.get("tags", {})

    name = tags.get("name", "Без названия")
    lat = element["lat"]
    lon = element["lon"]

    # ---- Сборка адреса ----
    street = tags.get("addr:street", "")
    house = tags.get("addr:housenumber", "")
    city = tags.get("addr:city", "")
    postcode = tags.get("addr:postcode", "")

    # Формируем красивый адрес
    parts = [city, street, house, postcode]
    address = ", ".join([p for p in parts if p])  # убрать пустые строки

    cafes.append({
        "name": name,
        "lat": lat,
        "lon": lon,
        "address": address if address else "Адрес не указан"
    })

print("Найденные кафе:")
for c in cafes:
    print(f"- {c['name']} ({c['lat']}, {c['lon']}), {c['address']}")
