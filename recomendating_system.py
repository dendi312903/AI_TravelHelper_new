from math import sqrt
# Кино, искусство, спорт
user = [2, 1, 1]   
cinema = [2, 1, 0] 
stadium = [0, 0, 1]     

def cosine_simularity(vec1, vec2):
    # Скалярное произведение
    product = sum(a * b for a, b in zip(vec1, vec2))
    # Длина первого вектора vec1
    lenghvec1 = 0
    for i in range(len(vec1)):
        lenghvec1 += vec1[i] * vec1[i]
    lengh1 = sqrt(lenghvec1)
    
    # Длина второго вектора vec2
    lenghvec2 = 0
    for i in range(len(vec2)):
        lenghvec2 += vec2[i] * vec2[i]
    lengh2 = sqrt(lenghvec2)
    
    if lengh1 == 0 or lengh2 == 0:
        return 0
    # Формула косинусного сходства (A * B) / (|A*A| * |B*B|)
    return product / (lengh1 * lengh2)

print("Сходства пользователя и стадиона:", cosine_simularity(user, stadium))
print("Сходства пользователя и кино:", cosine_simularity(user, cinema))
