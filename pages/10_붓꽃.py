
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

# ==========================================
# 1. 페이지 설정
# ==========================================
st.set_page_config(
    page_title="붓꽃 AI 품종 예측",
    page_icon="🌸",
    layout="wide"
)

st.title("🌸 붓꽃 AI 품종 예측")
st.write(
    "꽃잎길이와 꽃잎너비를 입력하고 "
    "3가지 머신러닝 알고리즘의 예측 결과를 비교해 보세요."
)

st.divider()

# ==========================================
# 2. CSV 파일 불러오기
# ==========================================
current_folder = Path(__file__).resolve().parent

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
    st.error("iris.csv 파일을 찾을 수 없습니다.")
    st.stop()

try:
    df = pd.read_csv(file_path, encoding="cp949")
except UnicodeDecodeError:
    df = pd.read_csv(file_path, encoding="utf-8-sig")

required_columns = ["꽃잎길이", "꽃잎너비", "품종"]

if not all(col in df.columns for col in required_columns):
    st.error("CSV 파일의 열 이름을 확인해주세요.")
    st.stop()

df = df[required_columns].copy()

df["꽃잎길이"] = pd.to_numeric(
    df["꽃잎길이"], errors="coerce"
)
df["꽃잎너비"] = pd.to_numeric(
    df["꽃잎너비"], errors="coerce"
)

df = df.dropna()

# ==========================================
# 3. 학습 데이터 준비
# ==========================================
X = df[["꽃잎길이", "꽃잎너비"]]
y = df["품종"]

# KNN은 거리 계산이 중요하므로 표준화
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 알고리즘 1 : KNN
knn = KNeighborsClassifier(n_neighbors=5)
knn.fit(X_scaled, y)

# 알고리즘 2 : 의사결정나무
tree = DecisionTreeClassifier(
    max_depth=4,
    min_samples_leaf=2,
    random_state=42
)
tree.fit(X, y)

# 알고리즘 3 : 랜덤 포레스트
forest = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)
forest.fit(X, y)

models = {
    "KNN": knn,
    "의사결정나무": tree,
    "랜덤 포레스트": forest
}

# ==========================================
# 4. 사용자 입력
# ==========================================
st.subheader("1️⃣ 붓꽃 크기 입력하기")

length_min = float(df["꽃잎길이"].min())
length_max = float(df["꽃잎길이"].max())
width_min = float(df["꽃잎너비"].min())
width_max = float(df["꽃잎너비"].max())

st.info(
    f"꽃잎길이 입력 범위: {length_min} ~ {length_max} cm\n\n"
    f"꽃잎너비 입력 범위: {width_min} ~ {width_max} cm"
)

col1, col2 = st.columns(2)

with col1:
    petal_length = st.number_input(
        "🌷 꽃잎길이 (cm)",
        min_value=length_min,
        max_value=length_max,
        value=4.5,
        step=0.1
    )

with col2:
    petal_width = st.number_input(
        "🌷 꽃잎너비 (cm)",
        min_value=width_min,
        max_value=width_max,
        value=1.5,
        step=0.1
    )

input_data = pd.DataFrame(
    [[petal_length, petal_width]],
    columns=["꽃잎길이", "꽃잎너비"]
)

input_scaled = scaler.transform(input_data)

# ==========================================
# 5. 세 알고리즘으로 예측
# ==========================================
predictions = {
    "KNN": knn.predict(input_scaled)[0],
    "의사결정나무": tree.predict(input_data)[0],
    "랜덤 포레스트": forest.predict(input_data)[0]
}

st.divider()
st.subheader("2️⃣ 알고리즘별 예측 결과")

result_cols = st.columns(3)

for col, (name, prediction) in zip(
    result_cols, predictions.items()
):
    with col:
        st.metric(
            label=name,
            value=prediction
        )

# 예측 결과 일치 여부
if len(set(predictions.values())) == 1:
    st.success("🎉 세 알고리즘이 모두 같은 품종으로 예측했습니다!")
else:
    st.warning(
        "알고리즘에 따라 예측 결과가 다릅니다. "
        "아래 그래프에서 그 이유를 확인해 보세요."
    )

# ==========================================
# 6. 품종별 색상 설정
# ==========================================
classes = sorted(y.unique())

color_map = {
    classes[0]: "#FF6384",
    classes[1]: "#36A2EB",
    classes[2]: "#2ECC71"
}

class_to_num = {
    name: i for i, name in enumerate(classes)
}

# ==========================================
# 7. 예측 영역을 그리는 함수
# ==========================================
def make_prediction_graph(model, name, scaled=False):

    # 꽃잎길이와 꽃잎너비의 예측 영역 생성
    x_values = np.linspace(length_min, length_max, 150)
    y_values = np.linspace(width_min, width_max, 150)

    xx, yy = np.meshgrid(x_values, y_values)

    grid_data = pd.DataFrame({
        "꽃잎길이": xx.ravel(),
        "꽃잎너비": yy.ravel()
    })

    if scaled:
        grid_input = scaler.transform(grid_data)
    else:
        grid_input = grid_data

    grid_predictions = model.predict(grid_input)

    zz = np.array([
        class_to_num[value]
        for value in grid_predictions
    ]).reshape(xx.shape)

    # 품종별 예측 영역 색상
    colorscale = [
        [0.0, color_map[classes[0]]],
        [0.3333, color_map[classes[0]]],
        [0.3334, color_map[classes[1]]],
        [0.6666, color_map[classes[1]]],
        [0.6667, color_map[classes[2]]],
        [1.0, color_map[classes[2]]]
    ]

    fig = go.Figure()

    # AI가 예측한 품종별 영역
    fig.add_trace(
        go.Contour(
            x=x_values,
            y=y_values,
            z=zz,
            colorscale=colorscale,
            zmin=-0.5,
            zmax=2.5,
            contours=dict(
                start=-0.5,
                end=2.5,
                size=1,
                coloring="fill",
                showlines=True
            ),
            opacity=0.22,
            showscale=False,
            hoverinfo="skip",
            name="예측 영역"
        )
    )

    # 기존 붓꽃 데이터 표시
    for species in classes:
        species_data = df[df["품종"] == species]

        fig.add_trace(
            go.Scatter(
                x=species_data["꽃잎길이"],
                y=species_data["꽃잎너비"],
                mode="markers",
                name=species,
                marker=dict(
                    size=7,
                    color=color_map[species],
                    line=dict(color="white", width=0.5)
                )
            )
        )

    # 사용자가 입력한 값 표시
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
            text=["입력값"],
            textposition="top center",
            name="사용자 입력"
        )
    )

    fig.update_layout(
        title=f"{name} 예측 영역",
        xaxis_title="꽃잎길이 (cm)",
        yaxis_title="꽃잎너비 (cm)",
        height=500,
        legend_title="범례",
        hovermode="closest"
    )

    return fig

# ==========================================
# 8. 알고리즘별 시각화
# ==========================================
st.divider()
st.subheader("3️⃣ 알고리즘별 예측 영역 비교")

st.write(
    "배경색은 각 알고리즘이 해당 위치를 어떤 품종으로 "
    "분류하는지 나타냅니다. 빨간 별은 사용자가 입력한 위치입니다."
)

tabs = st.tabs([
    "① KNN",
    "② 의사결정나무",
    "③ 랜덤 포레스트"
])

with tabs[0]:
    st.markdown("### KNN - 주변 이웃의 의견")
    st.write(
        "입력값 주변의 가장 가까운 5개 데이터를 찾아 "
        "가장 많이 등장하는 품종으로 예측합니다."
    )

    fig = make_prediction_graph(
        knn, "KNN", scaled=True
    )
    st.plotly_chart(fig, use_container_width=True)

    # 가까운 5개 데이터 확인
    distances, indices = knn.kneighbors(input_scaled)
    nearest = df.iloc[indices[0]].copy()
    nearest["거리"] = distances[0]

    st.markdown("**가장 가까운 데이터 5개**")

    st.dataframe(
        nearest.round(3),
        use_container_width=True,
        hide_index=True
    )

    votes = nearest["품종"].value_counts()

    st.markdown("**품종별 투표 결과**")
    st.bar_chart(
        votes.reindex(classes, fill_value=0)
    )

with tabs[1]:
    st.markdown("### Decision Tree - 조건에 따른 판단")
    st.write(
        "꽃잎길이와 꽃잎너비를 기준으로 여러 조건을 "
        "통과하면서 품종을 결정합니다."
    )

    fig = make_prediction_graph(
        tree, "의사결정나무"
    )
    st.plotly_chart(fig, use_container_width=True)

    # 의사결정나무가 사용한 조건 표시
    st.markdown("**AI가 판단한 조건 확인하기**")

    from scipy.sparse import issparse

    decision_path = tree.decision_path(input_data)
    node_indices = decision_path.indices

    tree_rules = []

    for node_id in node_indices:
        if tree.tree_.children_left[node_id] == tree.tree_.children_right[node_id]:
            continue

        feature_index = tree.tree_.feature[node_id]
        threshold = tree.tree_.threshold[node_id]
        feature_name = X.columns[feature_index]
        input_value = input_data.iloc[0, feature_index]

        if input_value <= threshold:
            condition = "<="
        else:
            condition = ">"

        tree_rules.append(
            f"{feature_name} {condition} {threshold:.2f} "
            f"(입력값: {input_value:.2f})"
        )

    for i, rule in enumerate(tree_rules, 1):
        st.write(f"{i}. {rule}")

    if not tree_rules:
        st.write("추가 분기 없이 품종을 결정했습니다.")

with tabs[2]:
    st.markdown("### Random Forest - 여러 나무의 의견")
    st.write(
        "100개의 의사결정나무가 각각 품종을 예측하고 "
        "가장 많은 표를 받은 품종을 최종 선택합니다."
    )

    fig = make_prediction_graph(
        forest, "랜덤 포레스트"
    )
    st.plotly_chart(fig, use_container_width=True)

    # 개별 나무의 예측 결과
    tree_votes = [
        estimator.predict(input_data)[0]
        for estimator in forest.estimators_
    ]

    forest_votes = pd.Series(tree_votes).value_counts()

    st.markdown("**100개 의사결정나무의 투표 결과**")

    st.bar_chart(
        forest_votes.reindex(classes, fill_value=0)
    )

    st.write(
        f"총 100개 나무 중 "
        f"{forest_votes.get(predictions['랜덤 포레스트'], 0)}개가 "
        f"{predictions['랜덤 포레스트']}으로 예측했습니다."
    )

# ==========================================
# 9. 알고리즘 비교
# ==========================================
st.divider()
st.subheader("4️⃣ 세 알고리즘의 예측 비교")

comparison = pd.DataFrame({
    "알고리즘": list(predictions.keys()),
    "예측 품종": list(predictions.values())
})

st.dataframe(
    comparison,
    use_container_width=True,
    hide_index=True
)

# ==========================================
# 10. 알고리즘 설명
# ==========================================
st.divider()
st.subheader("5️⃣ 알고리즘은 어떻게 다를까요?")

with st.expander("① KNN - 가까운 친구 5명에게 물어보기"):
    st.write(
        "새로운 붓꽃과 가장 비슷한 붓꽃 5개를 찾습니다. "
        "주변 5개 중 가장 많이 등장한 품종을 선택합니다."
    )
    st.write(
        "비유: 새로운 학생이 전학 왔을 때 주변 친구 5명의 "
        "특징을 살펴보고 가장 비슷한 유형을 판단하는 것과 같습니다."
    )

with st.expander("② 의사결정나무 - 질문에 답하며 판단하기"):
    st.write(
        "꽃잎길이가 얼마보다 큰지, 꽃잎너비가 얼마보다 작은지 "
        "등의 조건을 차례대로 확인합니다."
    )
    st.write(
        "비유: 스무고개처럼 질문에 답하면서 "
        "정답을 찾아가는 방식입니다."
    )

with st.expander("③ 랜덤 포레스트 - 여러 전문가에게 물어보기"):
    st.write(
        "여러 개의 의사결정나무가 각각 예측한 뒤 "
        "가장 많은 표를 받은 품종을 선택합니다."
    )
    st.write(
        "비유: 한 명의 의견만 듣는 것이 아니라 "
        "100명의 전문가에게 물어보고 다수의 의견을 따르는 방식입니다."
    )

st.caption(
    "※ 이번 실습은 전체 데이터 150개를 학습에 사용한 예측 시연입니다. "
    "그래프의 배경색은 모델의 분류 영역이며, "
    "실제 성능 비교를 위해서는 별도의 학습·평가 데이터 분리가 필요합니다."
)
