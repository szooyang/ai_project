import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 데이터 불러오기 (pages 폴더 기준 → CSV는 상위 폴더)
@st.cache_data
def load_data():
#    df = pd.read_csv("../fastfood.csv", encoding="utf-8")


    base_dir = Path(__file__).resolve().parent.parent
    csv_path = base_dir / "fastfood.csv"

    df = pd.read_csv(csv_path, encoding="cp949")
    return df



def add_health_score(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

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

    for col in bad_cols + good_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="ignore")

    score_cols = []

    # 나쁠수록 건강점수 낮음 → 작을수록 좋은 항목
    for col in bad_cols:
        if col not in df.columns:
            continue
        col_data = df[col]
        min_v, max_v = col_data.min(), col_data.max()
        if pd.isna(min_v) or pd.isna(max_v) or min_v == max_v:
            continue

        norm = (col_data - min_v) / (max_v - min_v)
        df[f"_score_{col}"] = 1 - norm
        score_cols.append(f"_score_{col}")

    # 많을수록 건강점수 높은 항목
    for col in good_cols:
        if col not in df.columns:
            continue
        col_data = df[col]
        min_v, max_v = col_data.min(), col_data.max()
        if pd.isna(min_v) or pd.isna(max_v) or min_v == max_v:
            continue

        df[f"_score_{col}"] = (col_data - min_v) / (max_v - min_v)
        score_cols.append(f"_score_{col}")

    if score_cols:
        df["health_score"] = df[score_cols].mean(axis=1)

    return df


def main():
    st.title("🍟 패스트푸드 영양 분석")

    df = load_data()
    df = add_health_score(df)

    companies = sorted(df["Company"].dropna().unique())
    selected_company = st.selectbox("📌 회사를 선택하세요", companies)

    company_df = df[df["Company"] == selected_company]

    if company_df.empty:
        st.warning("해당 회사의 메뉴가 없습니다.")
        return

    # ▣ 칼로리 그래프
    st.subheader(f"📊 {selected_company} 메뉴별 칼로리")

    fig = px.bar(
        company_df.sort_values("Calories", ascending=False),
        x="Item",
        y="Calories",
        title=f"{selected_company} 메뉴 칼로리",
        labels={"Item": "메뉴", "Calories": "칼로리(kcal)"},
    )
    fig.update_layout(xaxis_tickangle=-45, height=600)

    st.plotly_chart(fig, use_container_width=True)

    # ▣ 건강 점수 Top3 메뉴
    st.subheader(f"🥗 {selected_company} 건강한 메뉴 TOP 3")

    top3 = (
        company_df.sort_values("health_score", ascending=False)
        .head(3)
        .reset_index(drop=True)
    )

    top3.insert(0, "순위", [1, 2, 3])

    st.dataframe(
        top3[
            [
                "순위",
                "Item",
                "Calories",
                "Total Fat\n(g)",
                "Saturated Fat\n(g)",
                "Trans Fat\n(g)",
                "Cholesterol\n(mg)",
                "Sodium \n(mg)",
                "Carbs\n(g)",
                "Fiber\n(g)",
                "Sugars\n(g)",
                "Protein\n(g)",
                "health_score",
            ]
        ].style.format(
            {
                "Calories": "{:.0f}",
                "Total Fat\n(g)": "{:.1f}",
                "Saturated Fat\n(g)": "{:.1f}",
                "Trans Fat\n(g)": "{:.1f}",
                "Cholesterol\n(mg)": "{:.0f}",
                "Sodium \n(mg)": "{:.0f}",
                "Carbs\n(g)": "{:.1f}",
                "Fiber\n(g)": "{:.1f}",
                "Sugars\n(g)": "{:.1f}",
                "Protein\n(g)": "{:.1f}",
                "health_score": "{:.3f}",
            },
            errors="ignore",
        )
    )


if __name__ == "__main__":
    main()
