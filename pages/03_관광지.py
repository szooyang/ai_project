import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic

# 관광지 데이터
tourist_spots = [
    {"name": "경복궁", "lat": 37.579617, "lon": 126.977041,
     "desc": "조선 시대의 대표 궁궐로 외국인들이 가장 많이 찾는 역사 명소!",
     "subway": "경복궁역"},
    {"name": "명동 쇼핑거리", "lat": 37.563757, "lon": 126.985302,
     "desc": "쇼핑과 길거리 음식의 천국! 관광객 필수 코스 🎉",
     "subway": "명동역"},
    {"name": "남산타워(N Seoul Tower)", "lat": 37.551169, "lon": 126.988227,
     "desc": "서울 전망을 한눈에! 야경 명소로 유명 🌃",
     "subway": "명동역 / 충무로역"},
    {"name": "동대문디자인플라자(DDP)", "lat": 37.566491, "lon": 127.009221,
     "desc": "자하 하디드가 설계한 미래형 건축물 + 야시장까지 즐길 수 있음",
     "subway": "동대문역사문화공원역"},
    {"name": "북촌한옥마을", "lat": 37.582604, "lon": 126.983998,
     "desc": "한옥 골목을 걸으며 한국 전통 문화를 느낄 수 있는 곳",
     "subway": "안국역"},
    {"name": "홍대거리", "lat": 37.556332, "lon": 126.922651,
     "desc": "젊음과 예술의 거리! 클럽, 맛집, 버스킹 🎸",
     "subway": "홍대입구역"},
    {"name": "롯데월드", "lat": 37.511028, "lon": 127.098091,
     "desc": "도심 속 대형 테마파크! 실내외 모두 즐길 수 있어요 🎢",
     "subway": "잠실역"},
    {"name": "청계천", "lat": 37.570178, "lon": 126.988229,
     "desc": "도심 속 휴식 공간! 산책하기 좋은 하천길 🚶🏻‍♂️",
     "subway": "종각역 / 종로3가역"},
    {"name": "코엑스", "lat": 37.511634, "lon": 127.059537,
     "desc": "아쿠아리움부터 별마당 도서관까지! 볼거리가 많아요 📚",
     "subway": "삼성역"},
    {"name": "한강공원", "lat": 37.520817, "lon": 126.939472,
     "desc": "서울 시민의 힐링 스팟 🌊 피크닉과 야경의 조화!",
     "subway": "여의나루역"}
]

st.set_page_config(page_title="Seoul Attractions", layout="wide")
st.title("🌏 외국인들이 좋아하는 서울 관광지 Top 10")

# 지도 생성
m = folium.Map(location=[37.5665, 126.9780], zoom_start=12)

# 마커 추가 + 팝업 유지(시각 정보용)
for spot in tourist_spots:
    folium.Marker(
        location=[spot["lat"], spot["lon"]],
        tooltip=spot["name"],
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(m)

# 지도 렌더링 (현 클릭 좌표 반환)
map_data = st_folium(m, width=600, height=400)

st.markdown("---")
st.subheader("📌 관광지 정보")

selected_spot = None

# 클릭 위치 데이터 처리
if map_data and map_data.get("last_clicked"):
    clicked_lat = map_data["last_clicked"]["lat"]
    clicked_lon = map_data["last_clicked"]["lng"]
    clicked_point = (clicked_lat, clicked_lon)

    # 가장 가까운 관광지 찾기
    min_distance = float("inf")

    for spot in tourist_spots:
        dist = geodesic(clicked_point, (spot["lat"], spot["lon"])).meters
        if dist < min_distance:
            min_distance = dist
            selected_spot = spot

# 관광지 정보 출력
if selected_spot:
    st.markdown(f"### 📍 {selected_spot['name']}")
    st.markdown(f"⭐ {selected_spot['desc']}")
    st.markdown(f"🚇 가까운 지하철역: **{selected_spot['subway']}**")
else:
    st.info("👆 지도를 클릭하면 가장 가까운 관광지 설명을 여기에 보여드릴게요!")
