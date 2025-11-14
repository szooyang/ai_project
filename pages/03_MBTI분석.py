import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np


@st.cache_data
def load_data():
    # CSV 파일은 streamlit_app.py와 같은 폴더에 두고 이름을 맞춰주세요.
    df = pd.read_csv("countriesMBTI_16types.csv")
    return df


def make_colors(n_bars: int):
    """
    막대 색상 리스트 생성
    - 1등: 빨간색
    - 2등 이후: 진한 파란색 → 연한 파란색 그라데이션
    """
    # Plotly의 파란색 계열 팔레트 (진↔연)
    blue_scale = px.colors.sequential.Blues_r  # 진한 파랑 → 연파랑

    if n_bars <= 1:
        return ["red"]

    # 필요한 개수만큼 인덱스를 골고루 뽑아서 그라데이션 느낌 내기
    idx = np.linspace(0, len(blue_scale) - 1, n_bars - 1).astype(int)
    blue_colors = [blue_scale[i] for i in idx]

    # 1등은 빨간색, 나머지는 파란색 계열
    return ["red"] + blue_colors


def main():
    st.set_page_config(
        page_title="국가별 MBTI 분포",
        page_icon="🌍",
        layout="centered",
    )

    st.title("🌍 국가별 MBTI 유형 분포 대시보드")
    st.write("각 국가를 선택하면 그 국가의 **MBTI 16유형 비율**을 막대그래프로 보여줍니다.")

    df = load_data()

    # 국가 선택
    countries = sorted(df["Country"].unique())
    selected_country = st.selectbox("국가를 선택하세요", countries)

    # 선택한 국가 데이터 추출
    row = df[df["Country"] == selected_country].iloc[0]

    mbti_cols = [c for c in df.columns if c != "Country"]
    data = pd.DataFrame({
        "MBTI": mbti_cols,
        "Ratio": [row[c] for c in mbti_cols]
    })

    # 내림차순 정렬 (1등 찾기 위함)
    data = data.sort_values("Ratio", ascending=False).reset_index(drop=True)

    # 색상 리스트 생성
    colors = make_colors(len(data))

    # 비율을 퍼센트로 보기 좋게 표시할 컬럼 추가
    data["Ratio_pct"] = data["Ratio"] * 100

    # Plotly 막대그래프
    fig = px.bar(
        data,
        x="MBTI",
        y="Ratio",
        text=data["Ratio_pct"].map(lambda x: f"{x:.1f}%"),
    )

    fig.update_traces(
        marker_color=colors,
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>비율: %{y:.3f} (약 %{customdata:.1f}%)<extra></extra>",
        customdata=data["Ratio_pct"],
    )

    fig.update_layout(
        xaxis_title="MBTI 유형",
        yaxis_title="비율",
        yaxis_tickformat=".0%",
        uniformtext_minsize=8,
        uniformtext_mode="hide",
        margin=dict(t=60, l=40, r=40, b=40),
    )

    st.subheader(f"🇺🇳 {selected_country}의 MBTI 유형 분포")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.caption("1등 막대는 **빨간색**, 나머지는 **진한 파랑 → 연한 파랑** 그라데이션입니다.")


if __name__ == "__main__":
    main()
