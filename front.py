# fronttest.py - исправленная версия

import streamlit as st
import requests
import json

# ========== КОНФИГУРАЦИЯ СТРАНИЦЫ ==========
st.set_page_config(
    page_title="TravelHelper - Городской помощник",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== СТИЛИ ==========
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .stButton > button {
        background: linear-gradient(45deg, #4CAF50, #8BC34A);
        color: white;
        font-weight: bold;
        border-radius: 10px;
        border: none;
        padding: 12px 24px;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    
    .place-card {
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid #4CAF50;
    }
    
    .place-title {
        color: #333;
        font-size: 1.3em;
        font-weight: bold;
        margin-bottom: 10px;
    }
    
    .place-info {
        color: #666;
        font-size: 0.9em;
        margin: 5px 0;
    }
    
    .place-score {
        background: linear-gradient(45deg, #FF9800, #FF5722);
        color: white;
        padding: 5px 10px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    
    h1 {
        color: white;
        text-align: center;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    h2, h3 {
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ========== КОНФИГУРАЦИЯ ==========
API_URL = "http://localhost:8000"

# Типы мест
PLACE_TYPES = {
    "🍔 Кафе": "cafe",
    "🍽️ Ресторан": "restaurant",
    "🍻 Бар": "bar",
    "🎭 Театр": "theatre",
    "🎬 Кинотеатр": "cinema",
    "🏛️ Музей": "museum",
    "🏞️ Парк": "park",
    "🛍️ Торговый центр": "mall",
    "⚽ Спортзал": "sports_centre",
    "🏥 Больница": "hospital",
    "💊 Аптека": "pharmacy",
    "🏦 Банк": "bank",
    "🏨 Отель": "hotel",
    "🎡 Достопримечательность": "attraction",
    "🏰 Памятник": "monument"
}

# Города
CITIES = ["Москва", "Санкт-Петербург", "Казань", "Екатеринбург", "Новосибирск", 
          "Сочи", "Владивосток", "Калининград", "Нижний Новгород", "Самара"]

# ========== ФУНКЦИИ ==========
def search_places(city, place_type, radius, limit):
    """Отправляет запрос к backend API"""
    try:
        response = requests.post(
            f"{API_URL}/api/search_places",
            json={
                "city_name": city,
                "amenity": place_type,
                "radius": radius,
                "limit": limit,
                "username": "dendi31"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Ошибка сервера: {response.status_code}")
            return None
            
    except requests.exceptions.ConnectionError:
        st.error("Не могу подключиться к серверу. Запустите backend командой: python back.py")
        return None
    except Exception as e:
        st.error(f"Ошибка: {e}")
        return None

def display_place(place):
    """Отображает карточку места"""
    st.markdown(f"""
    <div class="place-card">
        <div class="place-title">{place['name']}</div>
        <div class="place-info">📍 {place['address']}</div>
        <div class="place-info">📏 Расстояние: {place.get('distance', '?')} м</div>
        <div class="place-info">🏷️ Тип: {place['type']}</div>
        
        {f"<div class='place-info'>🌐 Сайт: <a href='{place['website']}' target='_blank'>{place['website']}</a></div>" if place.get('website') else ""}
        {f"<div class='place-info'>📞 Телефон: {place['phone']}</div>" if place.get('phone') else ""}
        {f"<div class='place-info'>⏰ Часы работы: {place['opening_hours']}</div>" if place.get('opening_hours') else ""}
        
        <div style='margin-top: 10px;'>
            <span class="place-score">Рекомендация: {place.get('score', 0) * 100:.0f}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ========== ЗАГОЛОВОК ==========
st.title("🏙️ Городской помощник с персональными рекомендациями")
st.markdown("---")

# ========== САЙДБАР ==========
with st.sidebar:
    st.header("🔍 Поиск мест")
    
    # Выбор города
    city = st.selectbox(
        "Выберите город:",
        CITIES,
        index=0
    )
    
    # Выбор типа места
    place_type_display = st.selectbox(
        "Выберите тип места:",
        list(PLACE_TYPES.keys()),
        index=0
    )
    
    place_type = PLACE_TYPES[place_type_display]
    
    # Настройки поиска
    st.subheader("⚙️ Настройки")
    
    radius = st.slider(
        "Радиус поиска (метры):",
        min_value=500,
        max_value=5000,
        value=1500,
        step=100
    )
    
    limit = st.slider(
        "Количество результатов:",
        min_value=1,
        max_value=20,
        value=10,
        step=1
    )
    
    # Кнопка поиска
    if st.button("🔍 Начать поиск", use_container_width=True):
        with st.spinner("Ищем лучшие места для вас..."):
            result = search_places(city, place_type, radius, limit)
            
            if result:
                st.session_state.search_result = result
                st.session_state.show_results = True
                st.rerun()
    
    # Информация о пользователе
    st.markdown("---")
    st.subheader("👤 Ваш профиль")
    st.info("""
    **Имя:** Денис  
    **Любит:** кафе, парки, кино  
    **Не любит:** шумные бары, больницы
    
    *Рекомендации подбираются специально для вас!*
    """)

# ========== ОСНОВНОЙ КОНТЕНТ ==========
if 'show_results' not in st.session_state:
    st.session_state.show_results = False

if not st.session_state.show_results:
    # Приветственный экран
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🎯 Как это работает?")
        st.info("""
        1. Выберите город в меню слева
        2. Выберите тип места (кафе, парк и т.д.)
        3. Настройте параметры поиска
        4. Нажмите "Начать поиск"
        5. Получите персональные рекомендации!
        """)
    
    with col2:
        st.markdown("### 📊 Наша статистика")
        st.success(f"""
        🏙️ **Городов:** {len(CITIES)}
        🏷️ **Типов мест:** {len(PLACE_TYPES)}
        ⭐ **Персонализация:** Да
        ⚡ **Скорость:** Высокая
        """)
    
    with col3:
        st.markdown("### 💡 Советы")
        st.warning("""
        • Парки отлично подходят для прогулок
        • Музеи работают до 18:00
        • В ресторанах лучше бронировать столики
        • Проверяйте часы работы на сайте
        """)
    
    st.markdown("---")
    
    # Примеры запросов
    st.markdown("### 🚀 Попробуйте быстрый поиск:")
    
    quick_col1, quick_col2, quick_col3 = st.columns(3)
    
    with quick_col1:
        if st.button("Кафе в Москве", use_container_width=True):
            st.session_state.quick_search = ("Москва", "cafe")
            st.rerun()
    
    with quick_col2:
        if st.button("Парки в СПб", use_container_width=True):
            st.session_state.quick_search = ("Санкт-Петербург", "park")
            st.rerun()
    
    with quick_col3:
        if st.button("Музеи в Казани", use_container_width=True):
            st.session_state.quick_search = ("Казань", "museum")
            st.rerun()

else:
    # Показать результаты поиска
    result = st.session_state.get('search_result', {})
    
    if result and 'places' in result:
        st.header(f"🎯 Результаты поиска в {result.get('city', 'городе')}")
        
        st.info(f"""
        **Найдено мест:** {result.get('found', 0)}  
        **Тип мест:** {result.get('amenity', 'неизвестно')}  
        **Для пользователя:** {result.get('user', 'Гость')}
        """)
        
        # Сортировка
        st.subheader("Сортировка:")
        sort_by = st.radio(
            "Сортировать по:",
            ["Рекомендациям", "Расстоянию", "Названию"],
            horizontal=True
        )
        
        places = result['places']
        
        if sort_by == "Рекомендациям":
            places.sort(key=lambda x: x.get('score', 0), reverse=True)
        elif sort_by == "Расстоянию":
            places.sort(key=lambda x: x.get('distance', 99999))
        else:
            places.sort(key=lambda x: x.get('name', ''))
        
        # Отображение мест
        st.markdown(f"### 🏆 Топ-{len(places)} мест для вас:")
        
        for i, place in enumerate(places, 1):
            # Цветовая рамка в зависимости от рейтинга
            score = place.get('score', 0)
            if score > 0.7:
                border_color = "#4CAF50"  # Зелёный
            elif score > 0.4:
                border_color = "#FF9800"  # Оранжевый
            else:
                border_color = "#F44336"  # Красный
            
            st.html(f"""
            <div style="border-left: 5px solid {border_color}; padding-left: 15px; margin: 20px 0;">
                <h3>{i}. {place['name']}</h3>
                <p><strong>📍 Адрес:</strong> {place.get('address', 'Не указан')}</p>
                <p><strong>📏 Расстояние от центра:</strong> {place.get('distance', '?')} метров</p>
                
                {f"<p><strong>🌐 Сайт:</strong> <a href='{place['website']}' target='_blank'>{place['website']}</a></p>" if place.get('website') else ""}
                {f"<p><strong>📞 Телефон:</strong> {place['phone']}</p>" if place.get('phone') else ""}
                {f"<p><strong>⏰ Часы работы:</strong> {place['opening_hours']}</p>" if place.get('opening_hours') else ""}
                
                <div style="background: linear-gradient(90deg, {'#4CAF50' if score > 0.7 else '#FF9800' if score > 0.4 else '#F44336'}, #2196F3); 
                            color: white; padding: 5px 10px; border-radius: 5px; display: inline-block; margin-top: 10px;">
                    <strong>Рекомендация:</strong> {score * 100:.1f}%
                </div>
            </div>
            """)
            
            # Кнопки действий
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"🗺️ Карта #{i}", key=f"map_{i}"):
                    st.write(f"Открываем карту для: {place['name']}")
            with col2:
                if st.button(f"📝 Заметка #{i}", key=f"note_{i}"):
                    st.write(f"Добавляем в заметки: {place['name']}")
            with col3:
                if st.button(f"❤️ Нравится #{i}", key=f"like_{i}"):
                    st.success(f"Добавлено в избранное: {place['name']}")
            
            st.markdown("---")
        
        # Кнопка нового поиска
        if st.button("🔄 Новый поиск", use_container_width=True):
            st.session_state.show_results = False
            st.rerun()
    
    else:
        st.warning("Места не найдены. Попробуйте изменить параметры поиска.")
        
        if st.button("Вернуться к поиску"):
            st.session_state.show_results = False
            st.rerun()

# ========== ФУТЕР ==========
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: white;">
    <p><strong>🏙️ Городской помощник</strong> | Школьный проект 10 класс</p>
    <p>Использует OpenStreetMap | FastAPI backend | Streamlit frontend</p>
    <p>© 2024 Разработано для проекта "Персональные рекомендации в городе"</p>
</div>
""", unsafe_allow_html=True)