
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier

# ==========================================
# 1. 페이지 기본 설정
# ==========================================
st.set_page_config(
    page_title="붓꽃 품종 예측",
    page_icon="🌸",
    layout="wide"
)

st.title("🌸 붓꽃 품종 예측 AI")
st.write(
    "꽃잎의 길이와 너비를 입력하면 "
    "머신러닝이 붓꽃의 품종을 예측합니다."
)

st.divider()

# ==========================================
# 2. CSV 파일 불러오기
# ==========================================
current_folder = Path(__file__).resolve().parent

# pages 폴더와 상위 폴더 모두 검색
file_candidates = [
    current_folder / "iris.csv",
    current_folder.parent / "iris.csv"
]

file_path = None

for path in file_candidates:
    if path.exists():
        file_path = path
        break

if file_path is None:
    st.error(
        "iris.csv 파일을 찾을 수 없습니다. "
        "앱의 상위 폴더에 iris.csv를 넣어주세요."
    )
    st.stop()

# 한글 인코딩 처리
try:
    df = pd.read_csv(file_path, encoding="cp949")
except UnicodeDecodeError:
    df = pd.read_csv(file_path, encoding="utf-8-sig")

# 필요한 열 확인
required_columns = ["꽃잎길이", "꽃잎너비", "품종"]

if not all(col in df.columns for col in required_columns):
    st.error("CSV 파일의 열 이름을 확인해주세요.")
    st.stop()

# 분석에 필요한 데이터만 추출
df = df[required_columns].copy()

# 결측치 제거
df = df.dropna()

# ==========================================
# 3. 머신러닝 데이터 준비
# ==========================================

X = df[["꽃잎길이", "꽃잎너비"]]
y = df["품종"]

# 데이터 표준화
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# KNN 알고리즘 (가장 가까운 5개 데이터 비교)
model = KNeighborsClassifier(n_neighbors=5)
model.fit(X_scaled, y)

# 실제 데이터 범위
length_min = float(df["꽃잎길이"].min())
length_max = float(df["꽃잎길이"].max())

width_min = float(df["꽃잎너비"].min())
width_max = float(df["꽃잎너비"].max())

# ==========================================
# 4. 사용자 입력
# ==========================================

st.subheader("1️⃣ 붓꽃의 크기 입력하기")

st.info(
    f"꽃잎길이: {length_min:.1f} ~ {length_max:.1f} cm  |  "
    f"꽃잎너비: {width_min:.1f} ~ {width_max:.1f} cm"
)

col1, col2 = st.columns(2)

with col1:
    petal_length = st.number_input(
        "🌷 꽃잎길이 (cm)",
        min_value=length_min,
        max_value=length_max,
        value=4.5,
        step=0.1,
        format="%.1f"
    )

with col2:
    petal_width = st.number_input(
        "🌷 꽃잎너비 (cm)",
        min_value=width_min,
        max_value=width_max,
        value=1.5,
        step=0.1,
        format="%.1f"
    )

# ==========================================
# 5. 품종 예측
# ==========================================

input_data = pd.DataFrame(
    [[petal_length, petal_width]],
    columns=["꽃잎길이", "꽃잎너비"]
)

input_scaled = scaler.transform(input_data)

# 품종 예측
prediction = model.predict(input_scaled)[0]

# 가장 가까운 5개 데이터와 거리 계산
distances, indices = model.kneighbors(input_scaled)

nearest_data = df.iloc[indices[0]].copy()
nearest_data["거리"] = distances[0]

# 품종별 투표 수
vote_counts = nearest_data["품종"].value_counts()

# ==========================================
# 6. 예측 결과 출력
# ==========================================

st.divider()
st.subheader("2️⃣ AI 예측 결과")

st.success(f"🌸 예측된 붓꽃 품종: {prediction}")

result_col1, result_col2, result_col3 = st.columns(3)

result_col1.metric("예측 품종", prediction)
result_col2.metric("가장 가까운 데이터", "5개")
result_col3.metric(
    "다수결 투표",
    f"{vote_counts.iloc[0]} / 5"
)

# ==========================================
# 7. 데이터 시각화
# ==========================================

st.divider()
st.subheader("3️⃣ 그래프로 예측 위치 확인하기")

st.write(
    "기존 붓꽃 데이터는 품종별 색상으로 표시됩니다. "
    "별 모양은 사용자가 입력한 붓꽃입니다."
)

# 기존 데이터 산점도
fig = px.scatter(
    df,
    x="꽃잎길이",
    y="꽃잎너비",
    color="품종",
    hover_data=["품종"],
    color_discrete_sequence=[
        "#FF6384", "#36A2EB", "#4BC0C0"
    ],
    labels={
        "꽃잎길이": "꽃잎길이 (cm)",
        "꽃잎너비": "꽃잎너비 (cm)"
    },
    title="붓꽃 품종별 꽃잎 크기 분포"
)

# 가장 가까운 5개 데이터까지 선으로 연결
for i in range(len(nearest_data)):
    neighbor = nearest_data.iloc[i]

    fig.add_trace(
        go.Scatter(
            x=[petal_length, neighbor["꽃잎길이"]],
            y=[petal_width, neighbor["꽃잎너비"]],
            mode="lines",
            line=dict(
                color="gray",
                width=1.5,
                dash="dot"
            ),
            showlegend=False,
            hoverinfo="skip"
        )
    )

# 가장 가까운 5개 데이터 표시
fig.add_trace(
    go.Scatter(
        x=nearest_data["꽃잎길이"],
        y=nearest_data["꽃잎너비"],
        mode="markers",
        marker=dict(
            symbol="diamond",
            size=13,
            color="gold",
            line=dict(color="black", width=1)
        ),
        name="가까운 데이터 5개",
        text=nearest_data["품종"],
        hovertemplate=(
            "품종: %{text}<br>"
            "꽃잎길이: %{x}<br>"
            "꽃잎너비: %{y}"
            "<extra></extra>"
        )
    )
)

# 사용자 입력 위치 (별 모양)
fig.add_trace(
    go.Scatter(
        x=[petal_length],
        y=[petal_width],
        mode="markers+text",
        marker=dict(
            symbol="star",
            size=25,
            color="red",
            line=dict(color="black", width=1)
        ),
        text=["사용자 입력"],
        textposition="top center",
        name="사용자 입력값"
    )
)

fig.update_layout(
    height=600,
    xaxis_title="꽃잎길이 (cm)",
    yaxis_title="꽃잎너비 (cm)",
    legend_title="범례",
    hovermode="closest"
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 8. 예측 근거 분석
# ==========================================

st.divider()
st.subheader("4️⃣ AI가 이렇게 예측한 이유")

st.write(
    "AI는 입력한 값과 가장 가까운 기존 데이터 5개를 "
    "찾아서 품종을 결정했습니다."
)

# 품종별 투표 결과
st.markdown("**① 가까운 데이터 5개의 품종별 투표 결과**")

vote_df = (
    vote_counts
    .reindex(model.classes_, fill_value=0)
    .rename("투표 수")
)

st.bar_chart(vote_df)

# 가장 가까운 데이터 상세 정보
st.markdown("**② 가장 가까운 데이터 5개 확인하기**")

display_df = nearest_data[
    ["꽃잎길이", "꽃잎너비", "품종", "거리"]
].copy()

display_df["거리"] = display_df["거리"].round(3)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)

# ==========================================
# 9. 최종 예측 근거 설명
# ==========================================

st.markdown("**③ AI의 판단 근거**")

st.write(
    f"입력한 꽃잎길이는 {petal_length:.1f}cm, "
    f"꽃잎너비는 {petal_width:.1f}cm입니다."
)

st.write(
    f"가장 가까운 데이터 5개 중 "
    f"{prediction} 품종이 "
    f"{int(vote_counts.get(prediction, 0))}개 발견되었습니다."
)

st.success(
    f"따라서 KNN 알고리즘은 다수결 원리에 따라 "
    f"{prediction}으로 예측했습니다."
)

st.caption(
    "※ 거리는 표준화된 두 측정값을 이용한 유클리드 거리입니다. "
    "투표 수는 모델의 확률이나 예측 정확도를 의미하지 않습니다."
)

# ==========================================
# 10. 데이터 정보
# ==========================================

with st.expander("📊 학습 데이터 정보 확인하기"):
    st.write(f"전체 학습 데이터: {len(df)}개")
    st.write("사용한 입력 변수: 꽃잎길이, 꽃잎너비")
    st.write("분류 알고리즘: KNN")
    st.write("최근접 이웃 수: 5개")
    st.write("데이터 표준화: StandardScaler")
    st.write("품종별 데이터 개수")
    st.write(df["품종"].value_counts())
