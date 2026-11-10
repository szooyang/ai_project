
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


# -----------------------------------
# 1. 페이지 기본 설정
# -----------------------------------
st.set_page_config(
    page_title="미래 기온 예측",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 인공지능으로 미래 기온 예측하기")
st.markdown("""
과거 기온 데이터를 학습하여 미래의 평균기온을 예측해 봅시다.

세 가지 회귀 알고리즘이 어떤 차이를 보이는지 그래프로 비교할 수 있습니다.
""")

st.divider()


# -----------------------------------
# 2. CSV 파일 불러오기
# -----------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

file_candidates = [
    BASE_DIR / "temperature(3).csv",
    BASE_DIR / "temperature.csv",
    BASE_DIR / "temperature"
]

file_path = next(
    (p for p in file_candidates if p.exists()),
    None
)

if file_path is None:
    st.error(
        "CSV 파일을 찾을 수 없습니다. "
        "프로젝트 최상위 폴더에 temperature(3).csv "
        "파일이 있는지 확인해 주세요."
    )
    st.stop()


# 한글 CSV 인코딩 처리
try:
    df = pd.read_csv(file_path, encoding="cp949")
except UnicodeDecodeError:
    try:
        df = pd.read_csv(file_path, encoding="utf-8-sig")
    except Exception as e:
        st.error(f"CSV 파일 읽기 오류: {e}")
        st.stop()


# -----------------------------------
# 3. 데이터 전처리
# -----------------------------------
date_column = "일시"
target_column = "평균기온(℃)"

if date_column not in df.columns or target_column not in df.columns:
    st.error(
        "CSV 파일에 '일시' 또는 '평균기온(℃)' "
        "열이 있는지 확인해 주세요."
    )
    st.stop()


# 2자리 연도를 실제 연도로 변환
def convert_date(value):
    try:
        value = str(value).strip()

        month_text, year_text = value.split("-")

        year = int(year_text)

        if year < 100:
            if year <= 26:
                year += 2000
            else:
                year += 1900

        return pd.to_datetime(
            f"{month_text} 1 {year}",
            format="%b %d %Y"
        )

    except Exception:
        return pd.NaT


df["날짜"] = df[date_column].apply(convert_date)

df[target_column] = pd.to_numeric(
    df[target_column],
    errors="coerce"
)

df = df.dropna(
    subset=["날짜", target_column]
)

# 같은 월에 데이터가 중복되면 평균값으로 통합
df = (
    df.groupby("날짜", as_index=False)[target_column]
    .mean()
    .sort_values("날짜")
    .reset_index(drop=True)
)

if len(df) < 36:
    st.error("기계학습을 위해 최소 36개월 이상의 데이터가 필요합니다.")
    st.stop()


# -----------------------------------
# 4. 기계학습에 사용할 특성 만들기
# -----------------------------------
# 시간의 흐름을 숫자로 변환
start_date = df["날짜"].min()

def make_features(dates):
    dates = pd.Series(pd.to_datetime(dates))

    month_index = (
        (dates.dt.year - start_date.year) * 12
        + dates.dt.month - start_date.month
    )

    month_angle = 2 * np.pi * (dates.dt.month - 1) / 12

    return pd.DataFrame({
        "경과월": month_index.values,
        "월별_사인": np.sin(month_angle),
        "월별_코사인": np.cos(month_angle)
    })


X = make_features(df["날짜"])
y = df[target_column].values


# -----------------------------------
# 5. 학습용 데이터와 평가용 데이터 분리
# -----------------------------------
# 시간 순서를 유지하여 마지막 20%를 평가용으로 사용
split_index = int(len(df) * 0.8)

X_train = X.iloc[:split_index]
X_test = X.iloc[split_index:]

y_train = y[:split_index]
y_test = y[split_index:]


# -----------------------------------
# 6. 세 가지 회귀 알고리즘 설정
# -----------------------------------
models = {
    "선형 회귀": LinearRegression(),

    "의사결정나무 회귀": DecisionTreeRegressor(
        max_depth=5,
        min_samples_leaf=6,
        random_state=42
    ),

    "랜덤 포레스트 회귀": RandomForestRegressor(
        n_estimators=200,
        max_depth=8,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1
    )
}


# -----------------------------------
# 7. 알고리즘별 학습 및 성능 평가
# -----------------------------------
results = {}

for name, model in models.items():

    # 학습용 데이터로 학습
    model.fit(X_train, y_train)

    # 평가용 데이터 예측
    test_prediction = model.predict(X_test)

    mae = mean_absolute_error(
        y_test,
        test_prediction
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_test,
            test_prediction
        )
    )

    results[name] = {
        "MAE": mae,
        "RMSE": rmse
    }

    # 전체 데이터로 다시 학습
    # 미래 기온 예측에 사용
    model.fit(X, y)


# -----------------------------------
# 8. 미래 예측 기간 선택
# -----------------------------------
st.subheader("🔮 미래 기온 예측 설정")

forecast_months = st.slider(
    "앞으로 몇 개월의 기온을 예측할까요?",
    min_value=3,
    max_value=36,
    value=12,
    step=3
)

last_date = df["날짜"].max()

future_dates = pd.date_range(
    start=last_date + pd.offsets.MonthBegin(1),
    periods=forecast_months,
    freq="MS"
)

# 과거와 미래를 연결한 날짜
all_dates = pd.concat([
    df["날짜"],
    pd.Series(future_dates)
], ignore_index=True)

all_features = make_features(all_dates)

future_features = make_features(future_dates)


# -----------------------------------
# 9. 과거 학습 결과와 미래 예측
# -----------------------------------
predictions = {}

for name, model in models.items():

    predictions[name] = model.predict(
        all_features
    )

future_predictions = {}

for name, model in models.items():

    future_predictions[name] = model.predict(
        future_features
    )


# -----------------------------------
# 10. 그래프 그리기
# -----------------------------------
st.divider()

st.subheader("📈 알고리즘별 미래 기온 예측 결과")

st.caption(
    "최근 5년간의 실제 평균기온과 세 가지 알고리즘의 "
    "학습 결과 및 미래 예측을 비교합니다."
)

fig = go.Figure()

# 최근 5년 데이터만 표시
recent_start = last_date - pd.DateOffset(years=5)

recent_df = df[df["날짜"] >= recent_start]

# 실제 기온
fig.add_trace(
    go.Scatter(
        x=recent_df["날짜"],
        y=recent_df[target_column],
        mode="lines+markers",
        name="실제 평균기온",
        line=dict(color="black", width=2),
        marker=dict(size=5)
    )
)


# 알고리즘별 색상
colors = {
    "선형 회귀": "#E91E63",
    "의사결정나무 회귀": "#2196F3",
    "랜덤 포레스트 회귀": "#FF9800"
}

all_dates = pd.to_datetime(all_dates)

for name in models:

    # 최근 5년 + 미래 예측
    selected = all_dates >= recent_start

    fig.add_trace(
        go.Scatter(
            x=all_dates[selected],
            y=predictions[name][selected],
            mode="lines",
            name=name,
            line=dict(
                color=colors[name],
                width=2.5
            )
        )
    )


# 미래 예측 시작 지점 표시
fig.add_vline(
    x=last_date.timestamp() * 1000,
    line_dash="dash",
    line_color="gray",
    annotation_text="미래 예측 시작"
)

fig.update_layout(
    title="회귀 알고리즘별 미래 평균기온 예측",
    xaxis_title="날짜",
    yaxis_title="평균기온(℃)",
    hovermode="x unified",
    legend_title="범례",
    template="plotly_white",
    height=600
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# -----------------------------------
# 11. 미래 예측값 표로 확인
# -----------------------------------
st.subheader("📋 미래 기온 예측값")

forecast_table = pd.DataFrame({
    "날짜": future_dates.strftime("%Y-%m"),
    "선형 회귀": future_predictions["선형 회귀"],
    "의사결정나무 회귀": future_predictions["의사결정나무 회귀"],
    "랜덤 포레스트 회귀": future_predictions["랜덤 포레스트 회귀"]
})

forecast_table = forecast_table.round(1)

st.dataframe(
    forecast_table,
    use_container_width=True,
    hide_index=True
)


# -----------------------------------
# 12. 알고리즘별 성능 비교
# -----------------------------------
st.divider()

st.subheader("📊 알고리즘별 예측 정확도 비교")

st.caption(
    "과거 데이터의 마지막 20%를 평가용으로 남겨 두고 "
    "예측값과 실제 기온의 차이를 계산했습니다."
)

metric_cols = st.columns(3)

for col, (name, score) in zip(
    metric_cols,
    results.items()
):

    with col:
        st.metric(
            label=name,
            value=f"MAE {score['MAE']:.2f}℃",
            delta=f"RMSE {score['RMSE']:.2f}℃",
            delta_color="off"
        )


st.info(
    "MAE와 RMSE는 예측값과 실제값의 차이를 나타냅니다. "
    "일반적으로 값이 작을수록 예측 오차가 작습니다."
)


# -----------------------------------
# 13. 알고리즘별 작동 원리 설명
# -----------------------------------
st.divider()

st.subheader("🧠 세 가지 회귀 알고리즘 알아보기")

with st.expander("① 선형 회귀 (Linear Regression)", expanded=True):

    st.markdown("""
    **작동 원리**

    - 입력된 데이터의 전체적인 관계를 수식으로 학습합니다.
    - 시간의 흐름과 계절적 특징을 함께 반영합니다.
    - 학습한 관계를 이용하여 미래의 기온을 계산합니다.

    **그래프 특징**

    - 전체적인 추세가 부드럽게 나타납니다.
    - 계절적 특징을 반영하므로 완만한 반복 형태가 나타날 수 있습니다.

    **생각해 보기**

    - 데이터가 일정한 경향을 보인다면 선형 회귀가 유리할까요?
    """)


with st.expander("② 의사결정나무 회귀 (Decision Tree)"):

    st.markdown("""
    **작동 원리**

    - 데이터를 여러 조건에 따라 나눕니다.
    - 비슷한 특성을 가진 데이터끼리 그룹을 만듭니다.
    - 각 그룹에 속한 데이터의 평균값을 예측값으로 사용합니다.

    **그래프 특징**

    - 예측값이 구간별로 일정하게 나타나는 계단 모양이 특징입니다.
    - 학습 데이터의 범위를 벗어난 미래에서는 새로운 추세를 만들어 내기 어렵습니다.

    **생각해 보기**

    - 왜 그래프가 부드러운 곡선이 아니라 계단 모양으로 나타날까요?
    """)


with st.expander("③ 랜덤 포레스트 회귀 (Random Forest)"):

    st.markdown("""
    **작동 원리**

    - 여러 개의 의사결정나무를 만듭니다.
    - 각각의 나무가 독립적으로 예측합니다.
    - 여러 나무의 예측값을 평균하여 최종 결과를 만듭니다.

    **그래프 특징**

    - 여러 나무의 결과를 종합하기 때문에 하나의 나무보다 예측이 안정적일 수 있습니다.
    - 여러 나무의 평균이므로 계단 모양이 완화될 수 있습니다.
    - 학습 범위를 벗어난 미래의 장기적인 상승·하락 추세를 스스로 외삽하지는 못합니다.

    **생각해 보기**

    - 하나의 나무보다 여러 나무의 의견을 모으면 어떤 장점이 있을까요?
    """)


# -----------------------------------
# 14. 수업 마무리
# -----------------------------------
st.divider()

st.subheader("💡 오늘의 학습 정리")

st.markdown("""
1. 같은 기온 데이터를 사용해도 알고리즘에 따라 예측 결과가 달라집니다.
2. 선형 회귀는 전체적인 관계를 수식으로 학습합니다.
3. 의사결정나무는 조건에 따라 데이터를 구간별로 나눕니다.
4. 랜덤 포레스트는 여러 의사결정나무의 결과를 종합합니다.
5. 예측 오차가 작다고 해서 모든 미래 상황에서 정확한 것은 아닙니다.
""")

st.warning(
    "주의: 이 앱은 기계학습 알고리즘의 작동 원리를 배우기 위한 "
    "교육용 예측 실습입니다. 실제 기상예보가 아니며, "
    "장기 기온은 기후 변화와 다양한 환경 요인의 영향을 받습니다."
)
