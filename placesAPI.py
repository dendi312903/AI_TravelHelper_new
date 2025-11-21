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
    name = element["tags"].get("name", "Без названия")
    lat = element["lat"]
    lon = element["lon"]

    cafes.append({
        "name": name,
        "lat": lat,
        "lon": lon
    })

print("Найденные кафе:")
for c in cafes:
    print(f"- {c['name']} ({c['lat']}, {c['lon']})")