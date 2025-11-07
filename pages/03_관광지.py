import streamlit as st
import folium
from streamlit_folium import st_folium

# 서울 관광지 Top 10 + 설명 + 지하철역 정보
tourist_spots = [
    {"name": "경복궁", "lat": 37.579617, "lon": 126.977041,
     "desc": "조선 시대의 대표 궁궐! 한국을 대표하는 역사 관광 명소입니다.",
     "subway": "경복궁역"},
    {"name": "명동 쇼핑거리", "lat": 37.563757, "lon": 126.985302,
     "desc": "쇼핑과 먹거리의 성지! 관광객 필수 코스 🎉",
     "subway": "명동역"},
    {"name": "남산타워(N Seoul Tower)", "lat": 37.551169, "lon": 126.988227,
     "desc": "서울 야경을 한눈에 볼 수 있는 랜드마크 🌃",
     "subway": "명동역 / 충무로역"},
    {"name": "동대문디자인플라자(DDP)", "lat": 37.566491, "lon": 127.009221,
     "desc": "자하 하디드 설계의 미래형 디자인 명소 + 야시장",
     "subway": "동대문역사문화공원역"},
    {"name": "북촌한옥마을", "lat": 37.582604, "lon": 126.983998,
     "desc": "한국 전통 한옥을 가까이에서 볼 수 있는 인기 관광지",
     "subway": "안국역"},
    {"name": "홍대거리", "lat": 37.556332, "lon": 126.922651,
     "desc": "젊음·예술의 거리! 버스킹·맛집·쇼핑 🎸",
     "subway": "홍대입구역"},
    {"name": "롯데월드", "lat": 37.511028, "lon": 127.098091,
     "desc": "서울 최대 테마파크! 실내+실외 모두 즐길 수 있어요 🎢",
     "subway": "잠실역"},
    {"name": "청계천", "lat": 37.570178, "lon": 126.988229,
     "desc": "도심 속 힐링 산책 코스 🚶‍♀️",
     "subway": "종각역 / 종로3가역"},
    {"name": "코엑스", "lat": 37.511634, "lon": 127.059537,
     "desc": "쇼핑·전시·아쿠아리움까지! 별마당 도서관도 유명 📚",
     "subway": "삼성역"},
    {"name": "한강공원", "lat": 37.520817, "lon": 126.939472,
     "desc": "서울 시민의 대표 힐링 스팟 🌊",
     "subway": "여의나루역"}
]

st.set_page_config(page_title="Seoul Attractions", layout="wide")
st.title("🌏 외국인들이 좋아하는 서울 관광지 Top 10")

# 지도 생성
m = folium.Map(location=[37.5665, 126.9780], zoom_start=12)

# 마커 추가
for s in tourist_spots:
    folium.Marker(
        location=[s["lat"], s["lon"]],
        popup=s["name"],
        tooltip=s["name"],
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(m)

# 지도 표시 (크기 1/2)
map_data = st_folium(m, width=600, height=330)

st.markdown("---")

# 선택된 정보 처리
selected_name = None

if map_data:
    # 팝업 클릭 감지
    if map_data.get("last_object_clicked") and \
       map_data["last_object_clicked"].get("popup"):
        selected_name = map_data["last_object_clicked"]["popup"]

if selected_name:
    spot = next((x for x in tourist_spots if x["name"] == selected_name), None)
    if spot:
        st.subheader(f"📍 {spot['name']}")
        st.write(f"⭐ {spot['desc']}")
        st.write(f"🚇 가장 가까운 지하철역: **{spot['subway']}**")
else:
    st.info("👆 지도의 관광지 마커를 클릭하면 아래에 상세 정보가 표시됩니다!")
