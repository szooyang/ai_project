
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error


# -----------------------------------------
# 1. 페이지 설정
# -----------------------------------------
st.set_page_config(
    page_title="월별 미래 기온 예측",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 인공지능 월별 미래 기온 예측")
st.write(
    "과거의 월별 평균기온 데이터를 학습하여 "
    "원하는 연도의 평균기온을 예측해 봅시다."
)

st.divider()


# -----------------------------------------
# 2. CSV 파일 불러오기
# -----------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

file_path = BASE_DIR / "temperature(3).csv"

if not file_path.exists():
    st.error(
        "temperature(3).csv 파일을 찾을 수 없습니다. "
        "프로젝트 최상위 폴더에 CSV 파일을 저장해 주세요."
    )
    st.stop()

try:
    try:
        df = pd.read_csv(file_path, encoding="cp949")
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding="utf-8-sig")

except Exception as e:
    st.error(f"CSV 파일을 읽을 수 없습니다: {e}")
    st.stop()


# -----------------------------------------
# 3. 필요한 데이터만 선택
# -----------------------------------------
date_column = "일시"
temp_column = "평균기온(℃)"

if date_column not in df.columns or temp_column not in df.columns:
    st.error("CSV 파일의 열 이름을 확인해 주세요.")
    st.stop()


# -----------------------------------------
# 4. 날짜 변환
# -----------------------------------------
# CSV의 날짜는 Oct-07 형태
# 첫 데이터는 1907년으로 처리
# 연도가 99에서 00으로 바뀌면 세기를 변경

def convert_dates(values):

    century = 1900
    previous_year = None
    result = []

    for value in values:

        try:
            month_text, year_text = str(value).strip().split("-")

            year_number = int(year_text)

            if previous_year is not None:

                if previous_year - year_number > 50:
                    century += 100

            year = century + year_number
            previous_year = year_number

            date = pd.to_datetime(
                f"{month_text} 1 {year}",
                format="%b %d %Y"
            )

            result.append(date)

        except Exception:
            result.append(pd.NaT)

    return pd.Series(result, index=values.index)


df["날짜"] = convert_dates(df[date_column])

df[temp_column] = pd.to_numeric(
    df[temp_column],
    errors="coerce"
)

df = df.dropna(
    subset=["날짜", temp_column]
)

df["연도"] = df["날짜"].dt.year
df["월"] = df["날짜"].dt.month

# 1907년부터 2025년까지 사용
df = df[
    (df["연도"] >= 1907) &
    (df["연도"] <= 2025)
].copy()

# 평균기온만 사용
df = df[
    ["연도", "월", temp_column]
]

if df.empty:
    st.error("1907~2025년 데이터가 없습니다.")
    st.stop()


# -----------------------------------------
# 5. 월 선택
# -----------------------------------------
st.subheader("① 분석할 월 선택")

selected_month = st.selectbox(
    "평균기온을 분석할 월을 선택하세요.",
    options=list(range(1, 13)),
    format_func=lambda x: f"{x}월"
)


# 선택한 월의 데이터
month_df = df[
    df["월"] == selected_month
].copy()

month_df = (
    month_df.groupby("연도", as_index=False)[temp_column]
    .mean()
    .sort_values("연도")
)

if len(month_df) < 10:
    st.error("선택한 월의 데이터가 부족합니다.")
    st.stop()


# -----------------------------------------
# 6. 과거 평균기온 그래프
# -----------------------------------------
st.divider()
st.subheader(f"② {selected_month}월의 연도별 평균기온 변화")

fig_history = go.Figure()

fig_history.add_trace(
    go.Scatter(
        x=month_df["연도"],
        y=month_df[temp_column],
        mode="lines+markers",
        name="실제 평균기온",
        line=dict(
            color="#2196F3",
            width=2
        ),
        marker=dict(size=4)
    )
)

fig_history.update_layout(
    title=f"1907~2025년 {selected_month}월 평균기온 변화",
    xaxis_title="연도",
    yaxis_title="평균기온(℃)",
    template="plotly_white",
    hovermode="x unified",
    height=450
)

st.plotly_chart(
    fig_history,
    use_container_width=True
)


# -----------------------------------------
# 7. 예측 연도 입력
# -----------------------------------------
st.divider()
st.subheader("③ 미래 기온 예측 연도 입력")

forecast_year = st.number_input(
    "평균기온을 예측할 연도를 입력하세요.",
    min_value=2026,
    max_value=2100,
    value=2030,
    step=1
)

st.write(
    f"선택한 조건: **{forecast_year}년 {selected_month}월 평균기온**"
)


# -----------------------------------------
# 8. 학습 데이터 준비
# -----------------------------------------
X = month_df[["연도"]]
y = month_df[temp_column]

# 1907~2025년 데이터를 학습
# 입력값은 연도, 정답은 해당 월의 평균기온


# -----------------------------------------
# 9. 세 가지 회귀 알고리즘
# -----------------------------------------
models = {
    "선형 회귀": LinearRegression(),

    "의사결정나무 회귀": DecisionTreeRegressor(
        max_depth=5,
        min_samples_leaf=5,
        random_state=42
    ),

    "랜덤 포레스트 회귀": RandomForestRegressor(
        n_estimators=200,
        max_depth=8,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1
    )
}


# -----------------------------------------
# 10. 알고리즘 학습 및 예측
# -----------------------------------------
results = {}

for name, model in models.items():

    model.fit(X, y)

    prediction = model.predict(
        pd.DataFrame({"연도": [forecast_year]})
    )[0]

    results[name] = prediction


# -----------------------------------------
# 11. 예측값 출력
# -----------------------------------------
st.divider()
st.subheader(
    f"④ {forecast_year}년 {selected_month}월 평균기온 예측 결과"
)

cols = st.columns(3)

colors = {
    "선형 회귀": "#E91E63",
    "의사결정나무 회귀": "#2196F3",
    "랜덤 포레스트 회귀": "#FF9800"
}

for col, (name, value) in zip(cols, results.items()):

    with col:

        st.metric(
            label=name,
            value=f"{value:.2f} ℃"
        )


# -----------------------------------------
# 12. 예측 결과 비교 그래프
# -----------------------------------------
st.divider()
st.subheader("⑤ 세 가지 알고리즘의 예측 과정 비교")

# 1907~2025년 모델 학습 결과를 그래프로 표시
# 미래 연도까지 각 모델의 예측선을 연장

future_X = pd.DataFrame({
    "연도": np.arange(1907, int(forecast_year) + 1)
})

fig = go.Figure()

# 실제 평균기온
fig.add_trace(
    go.Scatter(
        x=month_df["연도"],
        y=month_df[temp_column],
        mode="markers",
        name="실제 평균기온",
        marker=dict(
            color="black",
            size=5
        )
    )
)


# 알고리즘별 학습 결과 및 미래 예측
for name, model in models.items():

    predicted_values = model.predict(future_X)

    fig.add_trace(
        go.Scatter(
            x=future_X["연도"],
            y=predicted_values,
            mode="lines",
            name=name,
            line=dict(
                color=colors[name],
                width=2.5
            )
        )
    )


# 미래 예측 연도 표시
fig.add_vline(
    x=forecast_year,
    line_dash="dash",
    line_color="gray",
    annotation_text="예측 연도"
)

fig.update_layout(
    title=f"{selected_month}월 평균기온 회귀 알고리즘 비교",
    xaxis_title="연도",
    yaxis_title="평균기온(℃)",
    template="plotly_white",
    hovermode="x unified",
    legend_title="범례",
    height=550
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# -----------------------------------------
# 13. 알고리즘별 작동 원리
# -----------------------------------------
st.divider()
st.subheader("⑥ 회귀 알고리즘별 작동 원리")

with st.expander("① 선형 회귀"):

    st.markdown("""
    **어떻게 작동할까요?**

    - 과거 연도와 평균기온의 관계를 학습합니다.
    - 데이터 전체의 경향을 가장 잘 나타내는 직선을 찾습니다.
    - 학습한 직선을 미래 연도까지 연장하여 예측합니다.

    **그래프 특징**

    - 직선 형태로 예측합니다.
    - 전체적인 기온 상승 또는 하락 경향을 파악하기 쉽습니다.
    - 복잡한 기온 변화를 표현하는 데 한계가 있습니다.
    """)

with st.expander("② 의사결정나무 회귀"):

    st.markdown("""
    **어떻게 작동할까요?**

    - 연도를 기준으로 데이터를 여러 구간으로 나눕니다.
    - 각 구간에 속한 평균기온의 평균값을 학습합니다.
    - 새로운 연도가 어느 구간에 속하는지 판단하여 예측합니다.

    **그래프 특징**

    - 계단 모양으로 나타납니다.
    - 구간에 따라 예측값이 달라집니다.
    - 학습한 범위를 벗어난 미래에는 마지막 구간의 예측값이 유지됩니다.
    """)

with st.expander("③ 랜덤 포레스트 회귀"):

    st.markdown("""
    **어떻게 작동할까요?**

    - 여러 개의 의사결정나무를 만듭니다.
    - 각 나무가 서로 다른 학습 자료와 조건으로 예측합니다.
    - 여러 나무의 예측값을 평균하여 최종 예측값을 만듭니다.

    **그래프 특징**

    - 여러 의사결정나무의 결과를 종합합니다.
    - 하나의 나무에 비해 예측이 안정적일 수 있습니다.
    - 학습 범위를 벗어난 미래에는 마지막 구간의 예측값을 중심으로 나타납니다.
    """)


# -----------------------------------------
# 14. 수업 정리
# -----------------------------------------
st.divider()
st.subheader("💡 오늘의 학습 정리")

st.markdown("""
- 같은 기온 데이터라도 알고리즘에 따라 예측 결과가 달라집니다.
- 선형 회귀는 전체적인 경향을 직선으로 학습합니다.
- 의사결정나무는 데이터를 여러 구간으로 나누어 학습합니다.
- 랜덤 포레스트는 여러 의사결정나무의 예측을 종합합니다.
- 예측값은 실제 미래의 기온과 다를 수 있습니다.
""")

st.warning(
    "이 앱은 기계학습의 원리를 이해하기 위한 교육용 프로그램입니다. "
    "미래 기온을 실제로 맞히는 기상예보 프로그램은 아닙니다."
)
