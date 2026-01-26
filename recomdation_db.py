import sqlite3
from math import sqrt

# Подключение к базе и создание таблицы
conn = sqlite3.connect("vectors.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS similarities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    similarity REAL
)
""")
conn.commit()


# Косинусное сходство
def cosine_simularity(vec1, vec2):
    product = sum(a * b for a, b in zip(vec1, vec2))

    lengh1 = sqrt(sum(x * x for x in vec1))
    lengh2 = sqrt(sum(x * x for x in vec2))

    if lengh1 == 0 or lengh2 == 0:
        return 0

    return product / (lengh1 * lengh2)


# Исходные данные 
user = [2, 2, 2]
cinema = [2, 1, 0]
stadium = [0, 0, 1]


sim_stadium = cosine_simularity(user, stadium)
sim_cinema = cosine_simularity(user, cinema)

print("Сходство пользователя и стадиона:", sim_stadium)
print("Сходство пользователя и кино:", sim_cinema)

# Сохранение результатов в базу 
cur.execute("INSERT INTO similarities (name, similarity) VALUES (?, ?)",
            ("stadium", sim_stadium))
cur.execute("INSERT INTO similarities (name, similarity) VALUES (?, ?)",
            ("cinema", sim_cinema))
conn.commit()

# Вывод содержимого таблицы
print("\nИстория значений в базе:")
cur.execute("SELECT name, similarity FROM similarities")
for row in cur.fetchall():
    print(row)

conn.close()