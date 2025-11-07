import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="국가별 MBTI 통계", layout="wide")

# 데이터 불러오기
@st.cache_data
def load_data():
    df = pd.read_csv("countriesMBTI_16types.csv")  # 업로드한 CSV 사용
    return df

data = load_data()

st.title("🌍 국가별 MBTI 비율 시각화")

# 국가 선택
countries = data['Country'].unique()
selected_country = st.selectbox("국가를 선택하세요:", countries)

# 선택된 국가 데이터 필터링
country_df = data[data['Country'] == selected_country].iloc[0]
mbti_cols = data.columns[1:]  # Country 제외

mbti_data = pd.DataFrame({
    "MBTI": mbti_cols,
    "Percent": [country_df[col] for col in mbti_cols]
})

# 높은 순으로 정렬
mbti_data = mbti_data.sort_values("Percent", ascending=False)

# 색상 설정 (1등=빨간색, 나머지=그라데이션)
colors = ["red"] + [
    f"rgba({255 - i*8}, {100 + i*10}, {100 + i*10}, 0.9)"
    for i in range(1, len(mbti_data))
]

fig = px.bar(
    mbti_data,
    x="MBTI",
    y="Percent",
    title=f"{selected_country} MBTI 비율",
    text="Percent"
)

fig.update_traces(marker_color=colors, texttemplate='%{text:.2f}%')
fig.update_layout(yaxis_title="비율 (%)")

st.plotly_chart(fig, use_container_width=True)
