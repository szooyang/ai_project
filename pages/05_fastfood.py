import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path   # ✅ 이 줄 추가!

@st.cache_data
def load_data():
    # 현재 파일: /mount/src/ai_project/pages/05_fastfood.py
    # base_dir:  /mount/src/ai_project
    base_dir = Path(__file__).resolve().parent.parent
    csv_path = base_dir / "fastfood.csv"   # ✅ fastfood.csv는 프로젝트 루트에 있다고 가정

    if not csv_path.exists():
        st.error(
            f"fastfood.csv 파일을 찾을 수 없습니다.\n"
            f"다음 위치에 fastfood.csv가 있는지 확인해주세요:\n\n{csv_path}"
        )
        st.stop()

    df = pd.read_csv(csv_path)
    return df
def add_health_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    전체 데이터 기준으로 각 영양소를 0~1 사이로 정규화해서
    'health_score' 컬럼을 추가합니다.
    - 나쁠수록 안 좋은 것(칼로리, 지방, 나트륨 등): 값이 낮을수록 점수↑
    - 좋을수록 좋은 것(식이섬유, 단백질): 값이 클수록 점수↑
    """
    df = df.copy()

    # 나쁠수록 건강에 안 좋은 항목들
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

    # 많을수록 좋은 항목들
    good_cols = [
        "Fiber\n(g)",
        "Protein\n(g)",
    ]

    # 1) 숫자로 강제 변환 (숫자가 아니면 NaN)
    for col in bad_cols + good_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    score_cols = []

    # 2) 나쁠수록 안 좋은 항목: 값이 작을수록 건강 점수↑
    for col in bad_cols:
        if col not in df.columns:
            continue

        col_data = df[col]

        # 전부 NaN이면 스킵
        if col_data.notna().sum() == 0:
            continue

        min_v = col_data.min(skipna=True)
        max_v = col_data.max(skipna=True)

        # 값이 하나뿐이거나 모두 같은 값이면 정규화 불가 → 스킵
        if pd.isna(min_v) or pd.isna(max_v) or min_v == max_v:
            continue

        norm = (col_data - min_v) / (max_v - min_v)   # 0~1
        score = 1 - norm                              # 값이 작을수록 점수↑

        score_col_name = f"_score_{col}"
        df[score_col_name] = score
        score_cols.append(score_col_name)

    # 3) 많을수록 좋은 항목: 값이 클수록 건강 점수↑
    for col in good_cols:
        if col not in df.columns:
            continue

        col_data = df[col]

        if col_data.notna().sum() == 0:
            continue

        min_v = col_data.min(skipna=True)
        max_v = col_data.max(skipna=True)

        if pd.isna(min_v) or pd.isna(max_v) or min_v == max_v:
            continue

        score = (col_data - min_v) / (max_v - min_v)  # 값이 클수록 점수↑

        score_col_name = f"_score_{col}"
        df[score_col_name] = score
        score_cols.append(score_col_name)

    # 4) 개별 스코어 평균 → health_score
    if score_cols:
        df["health_score"] = df[score_cols].mean(axis=1, skipna=True)
    else:
        df["health_score"] = np.nan

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

    if "health_score" not in company_df.columns or company_df["health_score"].isna().all():
        st.write("건강 점수를 계산할 수 있는 데이터가 부족합니다.")
        return

    top3 = (
        company_df.sort_values("health_score", ascending=False)
        .head(3)
        .reset_index(drop=True)
    )
    top3.insert(0, "순위", [1, 2, 3])

    show_cols = [
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
    show_cols = [c for c in show_cols if c in top3.columns]

    top3_display = top3[show_cols].copy()

    # 숫자 컬럼 포맷팅
    numeric_formats = {
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
    }

    for col, fmt in numeric_formats.items():
        if col in top3_display.columns:
            top3_display[col] = top3_display[col].map(
                lambda x: fmt.format(x) if pd.notna(x) else ""
            )

    st.write(
        "※ 건강 점수는 **칼로리·지방·나트륨·당분은 낮을수록**, "
        "**식이섬유·단백질은 높을수록** 좋다는 기준으로 계산한 상대적인 점수입니다. (0~1 사이)"
    )

    st.dataframe(top3_display, use_container_width=True)



if __name__ == "__main__":
    main()
