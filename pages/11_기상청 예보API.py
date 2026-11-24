import math
from datetime import datetime, timedelta, timezone
from urllib.parse import unquote

import pandas as pd
import requests
import streamlit as st

# ---------------------------------------------------------
# 1. 페이지 기본 설정 및 API 키 로드
# ---------------------------------------------------------
st.set_page_config(page_title="전국 단기예보 날씨 앱", page_icon="🌤️", layout="wide")

st.title("🌤️ 대한민국 전국 시·군·구·동 단기예보")
st.caption("기상청 단기예보 API 기반 (오늘 ~ 모레 시간대별 예보)")

if "kma_api" not in st.secrets:
    st.error("Streamlit Secrets에 'kma_api' 키가 설정되지 않았습니다.")
    st.stop()

# Encoding 키와 Decoding 키 모두 호환되도록 디코딩 처리
API_KEY = unquote(st.secrets["kma_api"]).strip()


# ---------------------------------------------------------
# 2. 위·경도 -> 기상청 격자 좌표(nx, ny) 변환 함수 (기상청 공식 알고리즘)
# ---------------------------------------------------------
def latlon_to_grid(lat: float, lon: float) -> tuple[int, int]:
    RE = 6371.00877  # 지구 반경(km)
    GRID = 5.0       # 격자 간격(km)
    SLAT1 = 30.0     # 투영 위도1(degree)
    SLAT2 = 60.0     # 투영 위도2(degree)
    OLON = 126.0     # 기준점 경도(degree)
    OLAT = 38.0      # 기준점 위도(degree)
    XO = 43          # 기준점 X좌표(GRID)
    YO = 136         # 기준점 Y좌표(GRID)

    DEGRAD = math.pi / 180.0
    re = RE / GRID
    slat1 = SLAT1 * DEGRAD
    slat2 = SLAT2 * DEGRAD
    olon = OLON * DEGRAD
    olat = OLAT * DEGRAD

    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = math.pow(sf, sn) * math.cos(slat1) / sn
    ro = math.tan(math.pi * 0.25 + olat * 0.5)
    ro = re * sf / math.pow(ro, sn)

    ra = math.tan(math.pi * 0.25 + lat * DEGRAD * 0.5)
    ra = re * sf / math.pow(ra, sn)
    theta = lon * DEGRAD - olon
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn

    nx = math.floor(ra * math.sin(theta) + XO + 0.5)
    ny = math.floor(ro - ra * math.cos(theta) + YO + 0.5)
    return nx, ny


# ---------------------------------------------------------
# 3. 시/군/구/동 주소 검색 -> 좌표 반환 함수
# ---------------------------------------------------------
@st.cache_data(ttl=86400)
def search_location(query: str):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "json",
        "countrycodes": "kr",
        "limit": 5,
        "accept-language": "ko",
    }
    headers = {"User-Agent": "StreamlitKMAWeatherApp/1.0"}
    res = requests.get(url, params=params, headers=headers, timeout=10)
    res.raise_for_status()
    return res.json()


# ---------------------------------------------------------
# 4. 기상청 단기예보 발표 시각(base_date, base_time) 계산 (한국시간 기준)
# ---------------------------------------------------------
def get_kma_base_datetime() -> tuple[str, str]:
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)

    # 단기예보 발표 시각 (1일 8회, 각 시각 +15분 이후 API 제공 안정화)
    base_hours = [2, 5, 8, 11, 14, 17, 20, 23]
    selected_hour = None

    for h in reversed(base_hours):
        candidate = now.replace(hour=h, minute=15, second=0, microsecond=0)
        if now >= candidate:
            selected_hour = h
            break

    if selected_hour is None:
        # 새벽 02:15 이전인 경우 전날 23:00 발표 데이터 사용
        yesterday = now - timedelta(days=1)
        return yesterday.strftime("%Y%m%d"), "2300"

    return now.strftime("%Y%m%d"), f"{selected_hour:02d}00"


# ---------------------------------------------------------
# 5. 기상청 단기예보 API 호출 및 데이터 정리 함수
# ---------------------------------------------------------
@st.cache_data(ttl=1800)  # 30분 캐싱으로 불필요한 호출 방지
def fetch_short_term_forecast(nx: int, ny: int, base_date: str, base_time: str) -> pd.DataFrame:
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    params = {
        "serviceKey": API_KEY,
        "pageNo": "1",
        "numOfRows": "1000",  # 오늘~모레 전체 시간대 데이터 충분히 수신
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny,
    }
    res = requests.get(url, params=params, timeout=15)
    res.raise_for_status()

    try:
        data = res.json()
    except Exception:
        raise RuntimeError(f"기상청 서버 응답 오류 (XML 반환됨): {res.text[:300]}")

    header = data.get("response", {}).get("header", {})
    if header.get("resultCode") != "00":
        raise RuntimeError(f"API 오류 [{header.get('resultCode')}]: {header.get('resultMsg')}")

    items = data["response"]["body"]["items"]["item"]
    df_raw = pd.DataFrame(items)

    # 필요한 카테고리만 필터링 후 피벗 테이블로 변환
    target_cats = ["TMP", "SKY", "PTY", "POP", "REH", "WSD"]
    df_filtered = df_raw[df_raw["category"].isin(target_cats)]
    df_pivot = df_filtered.pivot(
        index=["fcstDate", "fcstTime"], columns="category", values="fcstValue"
    ).reset_index()

    # 코드값 -> 한글 라벨 매핑
    sky_map = {"1": "☀️ 맑음", "3": "⛅ 구름많음", "4": "☁️ 흐림"}
    pty_map = {
        "0": "없음",
        "1": "🌧️ 비",
        "2": "🌨️ 비/눈",
        "3": "❄️ 눈",
        "4": "🌦️ 소나기",
    }

    df_pivot["하늘상태"] = df_pivot["SKY"].map(sky_map).fillna("-")
    df_pivot["강수형태"] = df_pivot["PTY"].map(pty_map).fillna("없음")

    # 날짜 및 시간 포맷 정리
    df_pivot["날짜"] = pd.to_datetime(df_pivot["fcstDate"], format="%Y%m%d").dt.strftime("%Y-%m-%d (%a)")
    df_pivot["시간"] = df_pivot["fcstTime"].str[:2] + ":00"
    df_pivot["일시"] = pd.to_datetime(
        df_pivot["fcstDate"] + df_pivot["fcstTime"], format="%Y%m%d%H%M"
    )

    # 숫자형 변환
    df_pivot["기온(℃)"] = pd.to_numeric(df_pivot["TMP"], errors="coerce")
    df_pivot["강수확률(%)"] = pd.to_numeric(df_pivot["POP"], errors="coerce")
    df_pivot["습도(%)"] = pd.to_numeric(df_pivot["REH"], errors="coerce")
    df_pivot["풍속(m/s)"] = pd.to_numeric(df_pivot["WSD"], errors="coerce")

    result_cols = ["일시", "날짜", "시간", "기온(℃)", "하늘상태", "강수형태", "강수확률(%)", "습도(%)", "풍속(m/s)"]
    return df_pivot[result_cols].sort_values("일시").reset_index(drop=True)


# ---------------------------------------------------------
# 6. 사용자 입력 UI 및 결과 출력
# ---------------------------------------------------------
col_input, col_btn = st.columns([4, 1])
with col_input:
    region_query = st.text_input(
        "조회할 지역을 입력하세요 (예: 서울 강남구 역삼동, 부산 해운대구 우동, 수원시 영통구)",
        value="서울특별시 중구 명동",
    )
with col_btn:
    st.write("")
    st.write("")
    search_clicked = st.button("날씨 조회", type="primary", use_container_width=True)

if region_query:
    try:
        locations = search_location(region_query)
        if not locations:
            st.warning("입력하신 지역을 찾을 수 없습니다. '시/군/구/동' 단위로 다시 입력해 주세요. (예: 경기 성남시 분당구 정자동)")
            st.stop()

        # 검색 결과가 여러 개일 경우 선택할 수 있도록 드롭다운 제공
        location_options = {loc["display_name"]: loc for loc in locations}
        selected_name = st.selectbox("검색된 지역 선택 (가장 정확한 위치를 고르세요):", list(location_options.keys()))
        selected_loc = location_options[selected_name]

        lat = float(selected_loc["lat"])
        lon = float(selected_loc["lon"])
        nx, ny = latlon_to_grid(lat, lon)
        base_date, base_time = get_kma_base_datetime()

        st.info(f"📍 선택 위치: **{selected_name}** | 기상청 격자좌표: `(nx={nx}, ny={ny})` | 발표시각: `{base_date} {base_time[:2]}:00`")

        with st.spinner("기상청에서 오늘~모레 단기예보 데이터를 불러오는 중입니다..."):
            df_weather = fetch_short_term_forecast(nx, ny, base_date, base_time)

        # (A) 상단 요약 카드 (가장 가까운 예보 시간 기준)
        st.subheader("📌 가장 가까운 시간대 요약")
        latest = df_weather.iloc[0]
        weather_status = latest["강수형태"] if latest["강수형태"] != "없음" else latest["하늘상태"]

        m1, m2, m3, m4 = st.columns(4)
        m1.metric(label=f"예상 기온 ({latest['시간']} 기준)", value=f"{latest['기온(℃)']} ℃")
        m2.metric(label="하늘 / 강수", value=weather_status)
        m3.metric(label="강수확률", value=f"{int(latest['강수확률(%)'])} %")
        m4.metric(label="습도 / 풍속", value=f"{int(latest['습도(%)'])}% / {latest['풍속(m/s)']}m/s")

        st.divider()

        # (B) 기온 변화 추이 그래프
        st.subheader("📈 오늘 ~ 모레 기온 변화 추이")
        chart_df = df_weather.set_index("일시")[["기온(℃)"]]
        st.line_chart(chart_df, height=280)

        st.divider()

        # (C) 시간대별 상세 예보 표 (날짜별 필터 제공)
        st.subheader("📋 오늘 ~ 모레 시간대별 상세 예보 표")
        available_dates = ["전체 보기"] + df_weather["날짜"].unique().tolist()
        selected_date = st.radio("날짜 필터:", available_dates, horizontal=True)

        display_df = df_weather.drop(columns=["일시"])
        if selected_date != "전체 보기":
            display_df = display_df[display_df["날짜"] == selected_date]

        st.dataframe(display_df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
