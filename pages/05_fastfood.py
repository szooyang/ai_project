import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 데이터 불러오기 함수 (캐시 적용)
@st.cache_data
def load_data():
    df = pd.read_csv("../fastfood.csv")
    return df

def add_health_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    전체 데이터 기준으로 각 영양소를 0~1 사이로 정규화해서
    'health_score' 컬럼을 추가합니다.
    - 나쁠수록 안 좋은 것(칼로리, 지방, 나트륨 등): 낮을수록 점수↑
    - 좋을수록 좋은 것(식이섬유, 단백질): 높을수록 점수↑
    """
    df = df.copy()

    # 실제 컬럼명 (줄바꿈 포함) 주의!
    bad_cols = [
        "Calories",
        "Total Fat\n(g)",
        "Saturated Fat\n(g)",
        "Trans Fat\n(g)",
        "Cholesterol\n(mg)",
        "Sodium \n(mg)",
        "Carbs\n(g)",
        "Sugars\n(g)",
    ]
    good_cols = [
        "Fiber\n(g)",
        "Protein\n(g)",
    ]

    # 숫자형으로 변환
    for col in bad_cols + good_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    score_cols = []

    # 나쁠수록 안 좋은 항목: 값이 작을수록 건강 점수↑
    for col in bad_cols:
        if col not in df.columns:
            continue
        col_data = df[col]
        min_v = col_data.min()
        max_v = col_data.max()
        if pd.isna(min_v) or pd.isna(max_v) or min_v == max_v:
            continue
        norm = (col_data - min_v) / (max_v - min_v)  # 0(최소) ~ 1(최대)
        score = 1 - norm  # 값이 작을수록 점수↑
        score_col_name = f"_score_{col}"
        df[score_col_name] = score
        score_cols.append(score_col_name)

    # 많을수록 좋은 항목: 값이 클수록 건강 점수↑
    for col in good_cols:
        if col not in df.columns:
            continue
        col_data = df[col]
        min_v = col_data.min()
        max_v = col_data.max()
        if pd.isna(min_v) or pd.isna(max_v) or min_v == max_v:
            continue
        score = (col_data - min_v) / (max_v - min_v)  # 값이 클수록 점수↑
        score_col_name = f"_score_{col}"
        df[score_col_name] = score
        score_cols.append(score_col_name)

    # 개별 점수 평균 = 종합 건강 점수
    if score_cols:
        df["health_score"] = df[score_cols].mean(axis=1, skipna=True)
    else:
        df["health_score"] = np.nan

    return df


def main():
    st.set_page_config(
        page_title="패스트푸드 영양 분석",
        layout="wide",
    )

    st.title("🍟 패스트푸드 영양 분석 대시보드")
    st.write(
        """
        - 회사를 선택하면 해당 회사 메뉴의 **칼로리 막대그래프**를 볼 수 있어요.  
        - 그래프 아래에는 나트륨·지방·칼로리·당·식이섬유·단백질 등을 모두 고려해  
          **가장 건강한 메뉴 Top3**를 1, 2, 3위로 보여줍니다.
        """
    )

    df = load_data()
    df = add_health_score(df)

    # 회사 선택
    companies = sorted(df["Company"].dropna().unique())
    selected_company = st.selectbox("📌 회사를 선택하세요", companies)

    # 선택한 회사 데이터 필터링
    company_df = df[df["Company"] == selected_company].copy()

    if company_df.empty:
        st.warning("선택한 회사에 해당하는 메뉴가 없습니다.")
        return

    # ---- 1) 칼로리 막대그래프 ----
    st.subheader(f"📊 {selected_company} 메뉴별 칼로리")

    # 메뉴 이름이 길 수 있으므로 정렬 후 그리기
    company_df_sorted = company_df.sort_values("Calories", ascending=False)

    fig = px.bar(
        company_df_sorted,
        x="Item",
        y="Calories",
        labels={"Item": "메뉴", "Calories": "칼로리 (kcal)"},
        title=f"{selected_company} 메뉴별 칼로리",
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        margin=dict(l=10, r=10, t=50, b=150),
    )

    st.plotly_chart(fig, use_container_width=True)

    # ---- 2) 가장 건강한 메뉴 Top3 ----
    s

