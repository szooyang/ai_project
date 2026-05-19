import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
import numpy as np

# -----------------------------------
# 페이지 설정
# -----------------------------------
st.set_page_config(
    page_title="서울 기온 분석",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 날짜별 기온 분석")

# -----------------------------------
# 데이터 불러오기
# -----------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("seoul.csv", encoding="cp949")

    # 컬럼명 변경
    df.columns = [
        "date",
        "station",
        "avg_temp",
        "min_temp",
        "max_temp"
    ]

    # 날짜 정리
    df["date"] = df["date"].astype(str).str.strip()

    df = df[
        df["date"].str.contains(
            r"\d{4}-\d{2}-\d{2}",
            na=False
        )
    ]

    # datetime 변환
    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    df = df.dropna(subset=["date"])

    # 숫자 변환
    df["min_temp"] = pd.to_numeric(
        df["min_temp"],
        errors="coerce"
    )

    df["max_temp"] = pd.to_numeric(
        df["max_temp"],
        errors="coerce"
    )

    # 결측 제거
    df = df.dropna(
        subset=["min_temp", "max_temp"]
    )

    # 연/월/일 추출
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["day"] = df["date"].dt.day

    return df


df = load_data()

# -----------------------------------
# 사용자 선택
# -----------------------------------
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

# -----------------------------------
# 데이터 필터링
# -----------------------------------
filtered = df[
    (df["month"] == month) &
    (df["day"] == day)
].copy()

filtered = filtered.sort_values("year")

# -----------------------------------
# 데이터 없는 경우
# -----------------------------------
if filtered.empty:
    st.warning("해당 날짜 데이터가 없습니다.")
    st.stop()

# -----------------------------------
# 그래프 생성
# -----------------------------------
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

# 레이아웃
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

st.plotly_chart(
    fig,
    use_container_width=True
)

# -----------------------------------
# 통계
# -----------------------------------
st.subheader("📊 날짜 통계")

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

# -----------------------------------
# 미래 기온 예측
# -----------------------------------
st.subheader("🔮 미래 기온 예측")

predict_year = st.slider(
    "예측할 연도 선택",
    2020,
    2100,
    2035
)

# 학습 데이터
X = filtered["year"].values.reshape(-1, 1)

y_max = filtered["max_temp"].values
y_min = filtered["min_temp"].values

# 모델 생성
model_max = LinearRegression()
model_min = LinearRegression()

# 학습
model_max.fit(X, y_max)
model_min.fit(X, y_min)

# 예측
future = np.array([[predict_year]])

pred_max = model_max.predict(future)[0]
pred_min = model_min.predict(future)[0]

# 결과 출력
col3, col4 = st.columns(2)

with col3:
    st.metric(
        f"{predict_year}년 예상 최고기온",
        f"{pred_max:.1f}℃"
    )

with col4:
    st.metric(
        f"{predict_year}년 예상 최저기온",
        f"{pred_min:.1f}℃"
    )

# -----------------------------------
# 예측 그래프 추가
# -----------------------------------
fig2 = go.Figure()

# 기존 최고기온
fig2.add_trace(
    go.Scatter(
        x=filtered["year"],
        y=filtered["max_temp"],
        mode="lines",
        name="실제 최고기온",
        line=dict(
            color="hotpink",
            width=3
        )
    )
)

# 기존 최저기온
fig2.add_trace(
    go.Scatter(
        x=filtered["year"],
        y=filtered["min_temp"],
        mode="lines",
        name="실제 최저기온",
        line=dict(
            color="#A7D8FF",
            width=3
        )
    )
)

# 예측 최고기온
fig2.add_trace(
    go.Scatter(
        x=[predict_year],
        y=[pred_max],
        mode="markers",
        name="예측 최고기온",
        marker=dict(
            color="red",
            size=14
        )
    )
)

# 예측 최저기온
fig2.add_trace(
    go.Scatter(
        x=[predict_year],
        y=[pred_min],
        mode="markers",
        name="예측 최저기온",
        marker=dict(
            color="blue",
            size=14
        )
    )
)

fig2.update_layout(
    title="미래 기온 예측",
    xaxis_title="연도",
    yaxis_title="온도(℃)",
    template="plotly_white",
    height=650
)

st.plotly_chart(
    fig2,
    use_container_width=True
)

# -----------------------------------
# 데이터 보기
# -----------------------------------
with st.expander("📄 데이터 보기"):
    st.dataframe(
        filtered[
            ["year", "min_temp", "max_temp"]
        ].rename(
            columns={
                "year": "연도",
                "min_temp": "최저기온",
                "max_temp": "최고기온"
            }
        ),
        use_container_width=True
    )
