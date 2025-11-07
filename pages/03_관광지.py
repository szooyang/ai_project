import streamlit as st
import folium
from streamlit_folium import st_folium

# 서울 관광지 Top 10 데이터
tourist_spots = [
    {"name": "경복궁", "lat": 37.579617, "lon": 126.977041},
    {"name": "명동 쇼핑거리", "lat": 37.563757, "lon": 126.985302},
    {"name": "남산타워(N Seoul Tower)", "lat": 37.551169, "lon": 126.988227},
    {"name": "동대문디자인플라자(DDP)", "lat": 37.566491, "lon": 127.009221},
    {"name": "북촌한옥마을", "lat": 37.582604, "lon": 126.983998},
    {"name": "홍대거리", "lat": 37.556332, "lon": 126.922651},
    {"name": "롯데월드", "lat": 37.511028, "lon": 127.098091},
    {"name": "청계천", "lat": 37.570178, "lon": 126.988229},
    {"name": "코엑스", "lat": 37.511634, "lon": 127.059537},
    {"name": "한강공원", "lat": 37.520817, "lon": 126.939472}
]

st.set_page_config(page_title="Seoul Top 10 Attractions", layout="wide")
st.title("🌏 외국인들이 좋아하는 서울 관광지 Top 10")

# 지도 생성 (중앙 좌표는 서울 중심)
m = folium.Map(location=[37.5665, 126.9780], zoom_start=12)

# 마커 추가
for spot in tourist_spots:
    folium.Marker(
        location=[spot["lat"], spot["lon"]],
        popup=spot["name"],
        tooltip=spot["name"]
    ).add_to(m)

# Streamlit에 Folium 지도 표시
st_folium(m, width=900, height=600)
