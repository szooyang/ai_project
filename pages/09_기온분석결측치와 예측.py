
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor


# =========================================
# 1. 페이지 설정
# =========================================
st.set_page_config(
    page_title="미래 기온 예측",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 인공지능 미래 기온 예측")
st.write(
    "결측치 처리 방법과 기계학습 알고리즘에 따라 "
    "미래 기온 예측 결과가 어떻게 달라지는지 알아봅시다."
)

st.divider()


# =========================================
# 2. CSV 파일 불러오기
# =========================================
BASE_DIR = Path(__file__).resolve().parent.parent

file_path = BASE_DIR / "temperature.csv"

if not file_path.exists():
    st.error(
        "temperature.csv 파일을 찾을 수 없습니다. "
        "GitHub 최상위 폴더에 CSV 파일이 있는지 확인하세요."
    )
    st.stop()

try:
    try:
        df = pd.read_csv(file_path, encoding="cp949")
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding="utf-8-sig")

except Exception as e:
    st.error(f"CSV 파일 읽기 오류: {e}")
    st.stop()


# =========================================
# 3. 필요한 열만 사용
# =========================================
date_column = "일시"
temp_column = "평균기온(℃)"

if date_column not in df.columns or temp_column not in df.columns:
    st.error(
        "CSV 파일에 '일시' 또는 '평균기온(℃)' 열이 없습니다."
    )
    st.stop()


# =========================================
# 4. 날짜 변환
# =========================================
# Oct-07 형식의 날짜를 1907년부터 순서대로 변환

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

df = df.dropna(subset=["날짜"])

df["연도"] = df["날짜"].dt.year
df["월"] = df["날짜"].dt.month

# 1907~2025년 데이터만 사용
df = df[
    (df["연도"] >= 1907) &
    (df["연도"] <= 2025)
].copy()

# 평균기온만 사용
df = df[["연도", "월", temp_column]]

# 같은 연도와 월에 여러 데이터가 있다면 평균 처리
df = (
    df.groupby(["연도", "월"], as_index=False)[temp_column]
    .mean()
)


# =========================================
# 5. 사용자 입력
# =========================================
st.subheader("① 예측 조건 설정")

col1, col2 = st.columns(2)

with col1:
    selected_month = st.selectbox(
        "분석할 월을 선택하세요.",
        options=list(range(1, 13)),
        format_func=lambda x: f"{x}월"
    )

with col2:
    forecast_year = st.number_input(
        "예측할 연도를 입력하세요.",
        min_value=2026,
        max_value=2100,
        value=2030,
        step=1
    )

st.caption(
    f"선택한 예측 대상: {forecast_year}년 {selected_month}월 평균기온"
)


# =========================================
# 6. 선택한 월의 데이터 추출
# =========================================
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


# 연도별 자료 구성
# 실제 관측값이 없는 연도도 결측치로 표시
first_year = int(month_df["연도"].min())

year_index = pd.Index(
    range(first_year, 2026),
    name="연도"
)

temperature_series = (
    month_df.set_index("연도")[temp_column]
    .reindex(year_index)
)

missing_count = int(temperature_series.isna().sum())

st.divider()

st.subheader("② 결측치 현황")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("분석 대상 월", f"{selected_month}월")

with col2:
    st.metric("전체 연도 수", f"{len(temperature_series)}년")

with col3:
    st.metric("결측치 개수", f"{missing_count}개")


# =========================================
# 7. 결측치 처리 방법 선택
# =========================================
st.divider()
st.subheader("③ 결측치 처리 방법 선택")

missing_method = st.selectbox(
    "어떤 방법으로 결측치를 처리할까요?",
    options=[
        "제거",
        "중앙값 대체",
        "선형보간법"
    ]
)

method_description = {
    "제거": "평균기온이 없는 연도의 데이터를 학습에서 제외합니다.",
    "중앙값 대체": "선택한 월의 평균기온 중앙값으로 결측치를 채웁니다.",
    "선형보간법": "앞뒤 연도의 평균기온을 이용하여 결측치를 추정합니다."
}

st.info(method_description[missing_method])


# =========================================
# 8. 알고리즘 선택
# =========================================
st.divider()
st.subheader("④ 기계학습 알고리즘 선택")

algorithm_name = st.selectbox(
    "어떤 회귀 알고리즘을 사용할까요?",
    options=[
        "선형 회귀",
        "의사결정나무 회귀",
        "랜덤 포레스트 회귀"
    ]
)


# =========================================
# 9. 결측치 처리 함수
# =========================================
def handle_missing(series, method):

    result = series.copy()

    if method == "제거":

        result = result.dropna()

    elif method == "중앙값 대체":

        median_value = result.median()

        result = result.fillna(median_value)

    elif method == "선형보간법":

        result = result.interpolate(
            method="linear",
            limit_direction="both"
        )

        # 양 끝에 결측치가 있을 경우 중앙값으로 보완
        result = result.fillna(result.median())

    return result


# =========================================
# 10. 회귀 알고리즘 생성 함수
# =========================================
def create_model(name):

    if name == "선형 회귀":

        return LinearRegression()

    elif name == "의사결정나무 회귀":

        return DecisionTreeRegressor(
            max_depth=5,
            min_samples_leaf=5,
            random_state=42
        )

    elif name == "랜덤 포레스트 회귀":

        return RandomForestRegressor(
            n_estimators=200,
            max_depth=8,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1
        )


# =========================================
# 11. 세 가지 결측치 처리 방법 비교
# =========================================
st.divider()
st.subheader("⑤ 결측치 처리 방법에 따른 예측 결과 비교")

methods = [
    "제거",
    "중앙값 대체",
    "선형보간법"
]

method_colors = {
    "제거": "#E91E63",
    "중앙값 대체": "#2196F3",
    "선형보간법": "#FF9800"
}

comparison_results = {}
comparison_models = {}
processed_data = {}

for method in methods:

    # 결측치 처리
    clean_series = handle_missing(
        temperature_series,
        method
    )

    processed_data[method] = clean_series

    # 학습 데이터 준비
    X_train = pd.DataFrame({
        "연도": clean_series.index.astype(int)
    })

    y_train = clean_series.values.astype(float)

    # 알고리즘 생성
    model = create_model(algorithm_name)

    # 학습
    model.fit(X_train, y_train)

    # 예측 연도까지 그래프용 데이터 생성
    graph_years = np.arange(
        first_year,
        int(forecast_year) + 1
    )

    X_graph = pd.DataFrame({
        "연도": graph_years
    })

    # 예측
    graph_predictions = model.predict(X_graph)

    # 미래 예측값
    future_prediction = model.predict(
        pd.DataFrame({
            "연도": [int(forecast_year)]
        })
    )[0]

    comparison_results[method] = {
        "예측값": future_prediction,
        "학습자료수": len(clean_series),
        "그래프연도": graph_years,
        "그래프예측": graph_predictions
    }

    comparison_models[method] = model


# =========================================
# 12. 선택한 결측치 처리 결과 표시
# =========================================
selected_result = comparison_results[missing_method]

st.markdown(
    f"**선택한 결측치 처리 방법: {missing_method}**"
)

st.markdown(
    f"**선택한 알고리즘: {algorithm_name}**"
)

st.metric(
    label=f"{forecast_year}년 {selected_month}월 예측 평균기온",
    value=f"{selected_result['예측값']:.2f} ℃"
)


# =========================================
# 13. 결측치 처리 방법별 예측 그래프
# =========================================
fig = go.Figure()

# 실제 관측 기온
fig.add_trace(
    go.Scatter(
        x=temperature_series.index,
        y=temperature_series.values,
        mode="markers",
        name="실제 평균기온",
        marker=dict(
            color="black",
            size=5
        )
    )
)

# 결측치 처리 방법별 예측선
for method in methods:

    result = comparison_results[method]

    is_selected = (method == missing_method)

    fig.add_trace(
        go.Scatter(
            x=result["그래프연도"],
            y=result["그래프예측"],
            mode="lines",
            name=f"{method} 예측",
            line=dict(
                color=method_colors[method],
                width=4 if is_selected else 2,
                dash="solid" if is_selected else "dash"
            ),
            opacity=1.0 if is_selected else 0.65
        )
    )


# 미래 예측 연도 표시
fig.add_vline(
    x=int(forecast_year),
    line_dash="dot",
    line_color="gray",
    annotation_text="예측 연도"
)

fig.update_layout(
    title=(
        f"{selected_month}월 평균기온 - "
        f"{algorithm_name} / 결측치 처리 방법 비교"
    ),
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


# =========================================
# 14. 결측치 처리별 예측값 비교표
# =========================================
st.subheader("⑥ 결측치 처리 방법별 예측값 비교")

result_table = pd.DataFrame({
    "결측치 처리 방법": methods,
    "학습 데이터 수": [
        comparison_results[m]["학습자료수"]
        for m in methods
    ],
    "예측 평균기온(℃)": [
        round(comparison_results[m]["예측값"], 2)
        for m in methods
    ]
})

st.dataframe(
    result_table,
    use_container_width=True,
    hide_index=True
)


# =========================================
# 15. 결측치 처리 방법별 설명
# =========================================
st.divider()
st.subheader("⑦ 결측치 처리 방법 알아보기")

with st.expander("1. 제거"):

    st.markdown("""
    평균기온이 비어 있는 데이터를 삭제합니다.

    - 장점: 실제 관측된 데이터만 사용합니다.
    - 단점: 학습 데이터의 양이 줄어듭니다.
    """)

with st.expander("2. 중앙값 대체"):

    st.markdown("""
    선택한 월의 평균기온 중앙값으로 빈칸을 채웁니다.

    - 장점: 간단하고 이상값의 영향을 비교적 적게 받습니다.
    - 단점: 여러 빈칸이 같은 값으로 채워집니다.
    """)

with st.expander("3. 선형보간법"):

    st.markdown("""
    앞뒤 연도의 기온을 이용하여 중간에 비어 있는 값을 추정합니다.

    - 장점: 주변 데이터의 변화 경향을 반영할 수 있습니다.
    - 단점: 실제 기온 변화가 직선 형태가 아닐 수 있습니다.
    """)


# =========================================
# 16. 알고리즘별 작동 원리
# =========================================
st.divider()
st.subheader("⑧ 회귀 알고리즘 알아보기")

with st.expander("1. 선형 회귀"):

    st.markdown("""
    과거 연도와 평균기온의 관계를 직선으로 학습합니다.

    - 전체적인 상승 또는 하락 경향을 파악합니다.
    - 미래 연도까지 직선을 연장하여 예측합니다.
    """)

with st.expander("2. 의사결정나무 회귀"):

    st.markdown("""
    연도에 따라 데이터를 여러 구간으로 나눕니다.

    - 각 구간의 평균기온을 학습합니다.
    - 새로운 연도가 어느 구간에 속하는지 판단합니다.
    - 그래프가 계단 모양으로 나타납니다.
    """)

with st.expander("3. 랜덤 포레스트 회귀"):

    st.markdown("""
    여러 개의 의사결정나무를 만들어 결과를 종합합니다.

    - 여러 나무가 각각 기온을 예측합니다.
    - 예측값들의 평균을 최종 결과로 사용합니다.
    - 하나의 나무에 의존하는 것보다 안정적일 수 있습니다.
    """)


# =========================================
# 17. 마무리
# =========================================
st.divider()

st.subheader("💡 오늘의 학습 정리")

st.markdown("""
1. 결측치를 처리하는 방법에는 여러 가지가 있습니다.
2. 같은 데이터라도 결측치 처리 방법에 따라 학습 데이터가 달라집니다.
3. 같은 학습 데이터라도 회귀 알고리즘에 따라 예측값이 달라집니다.
4. 예측값이 다르다고 해서 반드시 어느 한쪽이 정답인 것은 아닙니다.
5. 실제 미래 기온은 다양한 기상 및 환경 요인의 영향을 받습니다.
""")

st.warning(
    "이 프로그램은 기계학습 원리를 배우기 위한 교육용 프로그램입니다. "
    "연도만을 입력 특성으로 사용하므로 실제 기상예보의 정확도를 "
    "보장하지 않습니다. 특히 의사결정나무와 랜덤 포레스트는 "
    "학습 범위를 벗어난 미래 연도에서 마지막 구간의 예측값을 "
    "유지하는 특성이 있습니다."
)
