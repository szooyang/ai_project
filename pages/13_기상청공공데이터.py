from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="공공데이터포털 단기예보", page_icon="🌤️", layout="wide")
st.title("🌤️ 대한민국 주요 도시 단기예보")
st.caption("공공데이터포털(data.go.kr) 단기예보 조회서비스 기반")

if "kma_data_api" not in st.secrets:
    st.error("Streamlit Secrets에 'kma_data_api' 키가 설정되지 않았습니다.")
    st.stop()

# Decoding 키를 넣는 것을 권장합니다 (requests params 사용 시 자동 인코딩)
SERVICE_KEY = st.secrets["kma_data_api"].strip()

# 주요 지역 기상청 격자 좌표 (nx, ny) - 필요에 따라 추가 가능
GRID_MAP = {
    "서울특별시": (60, 127),
    "부산광역시": (98, 76),
    "대구광역시": (89, 90),
    "인천광역시": (55, 124),
    "광주광역시": (58, 74),
    "대전광역시": (67, 100),
    "울산광역시": (102, 84),
    "세종특별자치시": (66, 103),
    "수원시": (60, 121),
    "춘천시": (73, 134),
    "청주시": (69, 106),
    "전주시": (63, 89),
    "포항시": (102, 94),
    "창원시": (91, 77),
    "제주시": (52, 38),
}

# 단기예보 발표시각(HHMM) 목록: 02:00 ~ 23:00 (3시간 간격)
BASE_TIMES = ["2300", "2000", "1700", "1400", "1100", "0800", "0500", "0200"]


def get_latest_base_datetime() -> tuple[str, str]:
    """API 제공 지연(보통 발표 후 약 10~15분)을 감안해 가장 최근 유효한 base_date, base_time 반환"""
    now = datetime.now(ZoneInfo("Asia/Seoul")) - timedelta(minutes=15)
    today_str = now.strftime("%Y%m%d")
    curr_hm = now.strftime("%H%M")

    for bt in BASE_TIMES:
        if curr_hm >= bt:
            return today_str, bt

    # 02:00 이전이면 전날 2300 발표분 사용
    yesterday_str = (now - timedelta(days=1)).strftime("%Y%m%d")
    return yesterday_str, "2300"


@st.cache_data(ttl=1800)
def fetch_vilage_forecast(nx: int, ny: int, base_date: str, base_time: str, service_key: str) -> pd.DataFrame:
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    params = {
        "serviceKey": service_key,
        "pageNo": "1",
        "numOfRows": "1000",
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": str(nx),
        "ny": str(ny),
    }

    res = requests.get(url, params=params, timeout=15)
    res.raise_for_status()

    data = res.json()
    header = data.get("response", {}).get("header", {})
    result_code = header.get("resultCode")
    if result_code != "00":
        raise RuntimeError(f"API 오류 [{result_code}]: {header.get('resultMsg')}")

    items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
    if not items:
        raise RuntimeError("예보 데이터가 비어 있습니다.")

    raw_df = pd.DataFrame(items)

    # 예보시각(fcstDate + fcstTime) 기준으로 항목(TMP, SKY, PTY, POP)을 가로로 펼치기
    needed = raw_df[raw_df["category"].isin(["TMP", "SKY", "PTY", "POP"])].copy()
    pivoted = needed.pivot_table(
        index=["fcstDate", "fcstTime"],
        columns="category",
        values="fcstValue",
        aggfunc="first",
    ).reset_index()

    sky_map = {
        "1": "☀️ 맑음",
        "3": "⛅ 구름많음",
        "4": "☁️ 흐림",
    }
    pty_map = {
        "0": "없음",
        "1": "🌧️ 비",
        "2": "🌨️ 비/눈",
        "3": "❄️ 눈",
        "4": "🌦️ 소나기",
    }

    dt_fcst = pd.to_datetime(pivoted["fcstDate"] + pivoted["fcstTime"], format="%Y%m%d%H%M")
    pivoted["예보시각"] = dt_fcst.dt.strftime("%Y-%m-%d %H:%M")
    pivoted["예상기온(℃)"] = pd.to_numeric(pivoted.get("TMP"), errors="coerce").apply(
        lambda x: f"{x:.0f} ℃" if pd.notna(x) else "-"
    )
    pivoted["하늘상태"] = pivoted.get("SKY", pd.Series(dtype=str)).map(sky_map).fillna("-")
    pivoted["강수형태"] = pivoted.get("PTY", pd.Series(dtype=str)).map(pty_map).fillna("없음")
    pivoted["강수확률(%)"] = pd.to_numeric(pivoted.get("POP"), errors="coerce").fillna(0).astype(int)

    pivoted = pivoted.sort_values("예보시각").reset_index(drop=True)
    return pivoted[["예보시각", "예상기온(℃)", "하늘상태", "강수형태", "강수확률(%)"]]


try:
    selected_city = st.selectbox("지역을 선택하세요:", options=list(GRID_MAP.keys()), index=0)
    nx, ny = GRID_MAP[selected_city]
    base_date, base_time = get_latest_base_datetime()

    with st.spinner(f"{selected_city} 단기예보를 조회하는 중입니다..."):
        df_forecast = fetch_vilage_forecast(nx, ny, base_date, base_time, SERVICE_KEY)

    st.info(f"📍 선택 지역: **{selected_city}** (격자 {nx}, {ny}) | 발표시각: `{base_date} {base_time[:2]}:{base_time[2:]}`")

    first_row = df_forecast.iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("가장 가까운 예보시각", first_row["예보시각"][5:])
    c2.metric("예상 기온", first_row["예상기온(℃)"])
    c3.metric("하늘 / 강수", f"{first_row['하늘상태']} / {first_row['강수형태']}")
    c4.metric("강수 확률", f"{first_row['강수확률(%)']} %")

    st.divider()
    st.subheader("📋 시간대별 단기예보 표")
    st.dataframe(df_forecast, use_container_width=True, hide_index=True)

except Exception as e:
    safe_msg = str(e).replace(SERVICE_KEY, "***")
    st.error(f"오류가 발생했습니다: {safe_msg}")
