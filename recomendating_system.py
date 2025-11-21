# Список пользователей
users = ["user_1", "user_2", "user_3"]

# Список городских мест
places = ["museum", "park", "cinema", "cafe", "library"]

# Данные о посещениях / лайках пользователей
interactions = {
    "user_1": ["museum", "park"],
    "user_2": ["cinema", "cafe"],
    "user_3": ["library"]
}


def recommend(user_id, top_n=3):
    # Пользовательские места
    user_places = set(interactions[user_id])

    # Все остальные места
    all_places = set(places)
    candidates = all_places - user_places

    print(f"\nРекомендации для {user_id}:")
    for place in list(candidates)[:top_n]:
        print(" •", place)

recommend("user_1")
recommend("user_2")
recommend("user_3")
