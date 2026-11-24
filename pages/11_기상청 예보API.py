import pandas as pd
import requests
import streamlit as st

# ---------------------------------------------------------
# 1. 페이지 기본 설정 및 API 키 로드
# ---------------------------------------------------------
st.set_page_config(page_title="기상청 API허브 단기예보", page_icon="🌤️", layout="wide")

st.title("🌤️ 대한민국 전국 시·군 단기예보")
st.caption("기상청 API허브(apihub.kma.go.kr) 단기예보 기반")

if "kma_api" not in st.secrets:
    st.error("Streamlit Secrets에 'kma_api' 키가 설정되지 않았습니다.")
    st.stop()

AUTH_KEY = st.secrets["kma_api"].strip()


# ---------------------------------------------------------
# 2. 전국 예보 구역코드 목록 불러오기 (fct_shrt_reg.php)
# ---------------------------------------------------------
@st.cache_data(ttl=86400)
def fetch_region_codes(auth_key: str) -> dict[str, str]:
    url = "https://apihub.kma.go.kr/api/typ01/url/fct_shrt_reg.php"
    params = {"tmfc": "0", "authKey": auth_key}
    res = requests.get(url, params=params, timeout=15)
    res.raise_for_status()

    # 기상청 API허브 typ01 응답은 EUC-KR 또는 UTF-8 인코딩 사용
    res.encoding = res.apparent_encoding

    regions = {}
    for line in res.text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 4)
        if len(parts) >= 5:
            reg_id, _, _, reg_sp, reg_name = parts
            # 'C'는 시/군 단위 육상 예보 구역 코드
            if reg_sp == "C":
                regions[f"{reg_name} ({reg_id})"] = reg_id

    return regions


# ---------------------------------------------------------
# 3. 선택한 지역의 단기예보 불러오기 (fct_afs_dl.php)
# ---------------------------------------------------------
@st.cache_data(ttl=1800)
def fetch_land_forecast(reg_id: str, auth_key: str) -> pd.DataFrame:
    url = "https://apihub.kma.go.kr/api/typ01/url/fct_afs_dl.php"
    params = {
        "reg": reg_id,
        "disp": "0",
        "authKey": auth_key,
    }
    res = requests.get(url, params=params, timeout=15)
    res.raise_for_status()
    res.encoding = res.apparent_encoding

    rows = []
    for line in res.text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # 공백 기준으로 최대 17개 컬럼 분리 (마지막 WF 날씨 문장 보존)
        parts = line.split(None, 16)
        if len(parts) >= 17:
            rows.append(parts)

    if not rows:
        raise RuntimeError(f"예보 데이터가 비어 있습니다. 서버 응답: {res.text[:200]}")

    cols = [
        "REG_ID", "TM_FC", "TM_EF", "MOD", "NE", "STN", "C",
        "MAN_ID", "MAN_FC", "W1", "T", "W2", "TA", "ST", "SKY", "PREP", "WF"
    ]
    df = pd.DataFrame(rows, columns=cols)

    # 가장 최근 발표시각(TM_FC) 데이터만 필터링
    latest_tm_fc = df["TM_FC"].max()
    df = df[df["TM_FC"] == latest_tm_fc].copy()

    # 코드값 한글 변환
    sky_map = {
        "DB01": "☀️ 맑음",
        "DB02": "🌤️ 구름조금",
        "DB03": "⛅ 구름많음",
        "DB04": "☁️ 흐림",
    }
    prep_map = {
        "0": "없음",
        "1": "🌧️ 비",
        "2": "🌨️ 비/눈",
        "3": "❄️ 눈",
        "4": "🌦️ 소나기",
    }

    df["하늘상태"] = df["SKY"].map(sky_map).fillna(df["SKY"])
    df["강수형태"] = df["PREP"].map(prep_map).fillna("없음")

    # 발효시각(TM_EF: YYYYMMDDHHMM) -> 날짜 및 오전/오후 구분
    dt_ef = pd.to_datetime(df["TM_EF"], format="%Y%m%d%H%M")
    df["날짜"] = dt_ef.dt.strftime("%Y-%m-%d (%a)")
    df["구분"] = dt_ef.dt.hour.map(lambda h: "🌅 오전 (00시~)" if h < 12 else "🌇 오후 (12시~)")

    # 기온(-99는 결측/지나간 시간) 및 강수확률 정리
    df["예상기온(℃)"] = pd.to_numeric(df["TA"], errors="coerce").apply(
        lambda x: f"{int(x)} ℃" if pd.notna(x) and x > -50 else "-"
    )
    df["강수확률(%)"] = pd.to_numeric(df["ST"], errors="coerce").fillna(0).astype(int)
    df["날씨요약"] = df["WF"].str.strip('"')
    df["발표시각"] = pd.to_datetime(latest_tm_fc, format="%Y%m%d%H%M").strftime("%Y-%m-%d %H:%M")

    result_cols = ["날짜", "구분", "예상기온(℃)", "하늘상태", "강수형태", "강수확률(%)", "날씨요약", "발표시각"]
    return df[result_cols].reset_index(drop=True)


# ---------------------------------------------------------
# 4. 화면 UI 구성
# ---------------------------------------------------------
try:
    with st.spinner("전국 시·군 구역 목록을 불러오는 중입니다..."):
        region_map = fetch_region_codes(AUTH_KEY)

    if not region_map:
        st.error("구역 코드를 불러오지 못했습니다. Secrets의 'kma_api' 값을 확인해 주세요.")
        st.stop()

    region_names = sorted(region_map.keys())
    default_idx = next((i for i, name in enumerate(region_names) if name.startswith("서울")), 0)

    selected_region = st.selectbox(
        "지역을 선택하거나 직접 타이핑해 검색하세요 (예: 서울, 수원, 부산, 제주):",
        options=region_names,
        index=default_idx,
    )
    selected_reg_id = region_map[selected_region]

    with st.spinner(f"{selected_region}의 단기예보를 조회하는 중입니다..."):
        df_forecast = fetch_land_forecast(selected_reg_id, AUTH_KEY)

    st.info(f"📍 선택 지역: **{selected_region}** | 기상청 발표시각: `{df_forecast['발표시각'].iloc[0]}`")

    # (A) 상단 요약 카드
    st.subheader("📌 가장 가까운 예보 요약")
    first_row = df_forecast.iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("시점", f"{first_row['날짜'][5:]} {first_row['구분'][:2]}")
    c2.metric("예상 기온", first_row["예상기온(℃)"])
    c3.metric("날씨 요약", first_row["날씨요약"])
    c4.metric("강수 확률", f"{first_row['강수확률(%)']} %")

    st.divider()

    # (B) 오늘 ~ 모레 시간대별 표
    st.subheader("📋 오늘 ~ 모레 단기예보 표")
    display_df = df_forecast.drop(columns=["발표시각"])
    st.dataframe(display_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
