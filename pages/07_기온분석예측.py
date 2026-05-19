import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ---------------------------
# 페이지 설정
# ---------------------------
st.set_page_config(
    page_title="서울 기온 분석",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 날짜별 기온 분석")

# ---------------------------
# 데이터 불러오기
# ---------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("seoul.csv", encoding="cp949")

    # 컬럼 이름 변경
    df.columns = ["date", "station", "avg_temp", "min_temp", "max_temp"]

    # 날짜 정리
    df["date"] = df["date"].astype(str).str.strip()
    df = df[df["date"].str.contains(r"\d{4}-\d{2}-\d{2}", na=False)]

    # datetime 변환
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    # 연/월/일 추출
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["day"] = df["date"].dt.day

    return df


df = load_data()

# ---------------------------
# 사용자 입력
# ---------------------------
st.sidebar.header("📅 날짜 선택")

month = st.sidebar.selectbox(
    "월 선택",
    list(range(1, 13)),
    index=0
)

day = st.sidebar.selectbox(
    "일 선택",
    list(range(1, 32)),
    index=0
)

# ---------------------------
# 데이터 필터링
# ---------------------------
filtered = df[
    (df["month"] == month) &
    (df["day"] == day)
].copy()

filtered = filtered.sort_values("year")

# ---------------------------
# 데이터 없는 경우 처리
# ---------------------------
if filtered.empty:
    st.warning("해당 날짜의 데이터가 없습니다.")
    st.stop()

# ---------------------------
# 그래프 생성
# ---------------------------
fig = go.Figure()

# 최고기온
fig.add_trace(
    go.Scatter(
        x=filtered["year"],
        y=filtered["max_temp"],
        mode="lines+markers",
        name="최고기온",
        line=dict(
            color="hotpink",
            width=3
        ),
        marker=dict(size=6)
    )
)

# 최저기온
fig.add_trace(
    go.Scatter(
        x=filtered["year"],
        y=filtered["min_temp"],
        mode="lines+markers",
        name="최저기온",
        line=dict(
            color="#A7D8FF",
            width=3
        ),
        marker=dict(size=6)
    )
)

# ---------------------------
# 레이아웃 설정
# ---------------------------
fig.update_layout(
    title=f"{month}월 {day}일 날짜별 기온 분석",
    xaxis_title="연도",
    yaxis_title="온도(℃)",
    hovermode="x unified",
    template="plotly_white",
    height=650,
    legend=dict(
        title="범례"
    )
)

# ---------------------------
# 출력
# ---------------------------
st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# 추가 정보
# ---------------------------
st.subheader("📌 선택 날짜 통계")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "역대 최고기온",
        f"{filtered['max_temp'].max():.1f}℃"
    )

with col2:
    st.metric(
        "역대 최저기온",
        f"{filtered['min_temp'].min():.1f}℃"
    )

# 데이터 표시
with st.expander("데이터 보기"):
    st.dataframe(
        filtered[["year", "min_temp", "max_temp"]]
        .rename(columns={
            "year": "연도",
            "min_temp": "최저기온",
            "max_temp": "최고기온"
        }),
        use_container_width=True
    )
