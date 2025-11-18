import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# -----------------------------
# 데이터 불러오기 함수 (캐시)
# -----------------------------
@st.cache_data
def load_data():
    # pages 폴더 기준으로 한 단계 위(루트 폴더)에 있는 subway.csv 읽기
    base_dir = Path(__file__).resolve().parent.parent
    csv_path = base_dir / "subway.csv"

    df = pd.read_csv(csv_path, encoding="cp949")

    # 날짜 컬럼 처리
    df["사용일자"] = pd.to_datetime(df["사용일자"].astype(str), format="%Y%m%d")
    # 총 이용객수 (승차 + 하차)
    df["총이용객수"] = df["승차총승객수"] + df["하차총승객수"]
    return df


def make_bar_chart(df_ranked, selected_date, selected_line):
    # 색상: 1등은 빨간색, 나머지는 파란색 그라데이션
    n = len(df_ranked)
    colors = []

    for i in range(n):
        if i == 0:
            # 1등
            colors.append("red")
        else:
            # 나머지: 파란색 계열 그라데이션
            # i가 커질수록 점점 연해지도록 설정
            t = i / (n - 1) if n > 1 else 1  # 0 ~ 1 사이
            r = 0
            g = int(70 + t * 120)   # 70 ~ 190
            b = 255
            colors.append(f"rgba({r},{g},{b},1.0)")

    fig = go.Figure(
        data=[
            go.Bar(
                x=df_ranked["역명"],
                y=df_ranked["총이용객수"],
                marker=dict(color=colors),
                hovertemplate="역명: %{x}<br>총 이용객수: %{y:,}명<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        title=f"{selected_date.strftime('%Y-%m-%d')} {selected_line} 역별 총 이용객수 순위",
        xaxis_title="역명",
        yaxis_title="총이용객수(명)",
        xaxis_tickangle=-45,
        hovermode="x",
        margin=dict(l=40, r=40, t=60, b=100),
    )

    return fig


def main():
    st.set_page_config(
        page_title="지하철 승하차 분석",
        layout="wide",
    )

    st.title("🚇 서울 지하철 승하차 분석 (2025년 10월)")
    st.markdown(
        """
        2025년 10월 한 달 동안의 지하철 승차·하차 데이터를 기반으로  
        **특정 날짜와 호선을 선택하면 역별 총 이용객수를 순위별로 시각화**합니다.
        """
    )

    # 데이터 불러오기
    df = load_data()

    # -----------------------------
    # 사이드바: 날짜 & 호선 선택
    # -----------------------------
    st.sidebar.header("🔧 필터 설정")

    min_date = df["사용일자"].min()
    max_date = df["사용일자"].max()

    selected_date = st.sidebar.date_input(
        "날짜 선택 (2025년 10월 중 하루)",
        value=min_date,
        min_value=min_date,
        max_value=max_date,
    )

    line_options = sorted(df["노선명"].unique())
    selected_line = st.sidebar.selectbox("호선 선택", line_options)

    # -----------------------------
    # 데이터 필터링
    # -----------------------------
    mask = (df["사용일자"] == pd.to_datetime(selected_date)) & (
        df["노선명"] == selected_line
    )
    df_filtered = df[mask].copy()

    if df_filtered.empty:
        st.warning("선택한 날짜와 호선에 해당하는 데이터가 없습니다.")
        return

    # 역별 총 이용객수 집계 & 정렬
    df_ranked = (
        df_filtered.groupby("역명", as_index=False)["총이용객수"]
        .sum()
        .sort_values("총이용객수", ascending=False)
    )

    # -----------------------------
    # 그래프 그리기
    # -----------------------------
    st.subheader(
        f"📊 {selected_date.strftime('%Y-%m-%d')} {selected_line} 역별 총 이용객수 순위"
    )

    fig = make_bar_chart(df_ranked, pd.to_datetime(selected_date), selected_line)
    st.plotly_chart(fig, use_container_width=True)

    # -----------------------------
    # 데이터 테이블 (옵션)
    # -----------------------------
    with st.expander("🔍 역별 총 이용객수 데이터 보기"):
        st.dataframe(
            df_ranked.reset_index(drop=True).rename(
                columns={"총이용객수": "총이용객수(명)"}
            )
        )


if __name__ == "__main__":
    main()
