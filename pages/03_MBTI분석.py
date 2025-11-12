# app.py
# ─────────────────────────────────────────────────────────
# Streamlit Cloud에서 동작하는 국가별 MBTI 분포 대시보드
# - 업로더로 CSV를 선택하거나, 리포에 포함된 파일(countriesMBTI_16types.csv)을 사용합니다.
# - 국가 선택 → 해당 국가의 MBTI 16유형 비율을 막대그래프로 시각화(1등은 빨간색, 나머지는 파란색 그라데이션)
# - Plotly 기반 인터랙티브 차트

import io
from typing import List

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.colors import sample_colorscale

st.set_page_config(page_title="국가별 MBTI 분포", page_icon="📊", layout="wide")

# ─────────────────────────────────────────────────────────
# 데이터 로더
# ─────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data(file_bytes: bytes | None = None) -> pd.DataFrame:
    """CSV를 DataFrame으로 로드한다.
    우선순위: 업로더 → 로컬 파일 → (옵션) 세션 환경의 경로
    """
    if file_bytes is not None:
        df = pd.read_csv(io.BytesIO(file_bytes))
    else:
        # 1) 리포/앱 루트에 파일이 포함된 경우
        try:
            df = pd.read_csv("countriesMBTI_16types.csv")
        except Exception:
            # 2) (선택) 현재 환경에 존재할 수 있는 경로 시도
            try:
                df = pd.read_csv("/mnt/data/countriesMBTI_16types.csv")
            except Exception as e:
                raise FileNotFoundError(
                    "CSV 파일을 찾을 수 없습니다. 상단 업로더로 파일을 올려주세요.") from e

    # 컬럼 정리
    if "Country" not in df.columns:
        raise ValueError("'Country' 컬럼이 필요합니다.")

    # 문자열 컬럼은 Country만 허용, 나머지는 수치형으로 시도
    mbti_cols = [c for c in df.columns if c != "Country"]
    for c in mbti_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # 결측치 처리: 비율 컬럼의 결측은 0으로 대체(보수적)
    df[mbti_cols] = df[mbti_cols].fillna(0)

    return df[["Country"] + mbti_cols]

# ─────────────────────────────────────────────────────────
# 색상 유틸: 1등 빨강 + 나머지 파란 그라데이션
# ─────────────────────────────────────────────────────────

def bar_colors_for_values(values: List[float], top_color: str = "red") -> List[str]:
    import numpy as np

    values = list(values)
    if not values:
        return []

    arr = np.array(values)
    top_idx = int(arr.argmax())

    # 나머지 막대에 사용할 그라데이션 색상 샘플(진하기를 조금 다양화)
    # Blues 스케일에서 0.25~0.9 사이 구간을 균등 분할해 사용
    n = len(values)
    # 최소 2개 이상일 때만 그라데이션 적용
    grad_positions = np.linspace(0.25, 0.9, max(n - 1, 1))
    grad_colors = sample_colorscale("Blues", grad_positions)

    colors = []
    grad_i = 0
    for i, _ in enumerate(values):
        if i == top_idx:
            colors.append(top_color)
        else:
            colors.append(grad_colors[grad_i])
            grad_i += 1
    return colors

# ─────────────────────────────────────────────────────────
# 사이드바: 데이터 업로더 & 옵션
# ─────────────────────────────────────────────────────────
st.sidebar.header("데이터 설정")
uploaded = st.sidebar.file_uploader("countriesMBTI_16types.csv 업로드", type=["csv"]) 

try:
    df = load_data(uploaded.read() if uploaded else None)
except Exception as e:
    st.error(str(e))
    st.stop()

mbti_cols = [c for c in df.columns if c != "Country"]

# 데이터 유효성(합계) 간단 점검 옵션
with st.sidebar.expander("데이터 점검", expanded=False):
    check = st.checkbox("국가별 합계(≈1) 경고 보기", value=True, help="16개 유형 합이 1에서 크게 벗어나면 경고합니다.")

# ─────────────────────────────────────────────────────────
# 메인 UI
# ─────────────────────────────────────────────────────────
st.title("📊 국가별 MBTI 분포 대시보드")
st.caption("국가를 선택하거나 MBTI 유형을 선택하여 인터랙티브 막대 그래프로 비교합니다.")

# 탭 구성
(tab_country, tab_type, tab_code) = st.tabs(["국가별", "유형별", "코드 보기"])

# ── [탭 1] 국가별: 단일 국가의 16유형 분포 ─────────────────────
with tab_country:
    # 국가 선택
    countries = df["Country"].sort_values().tolist()
    col1, col2 = st.columns([2, 1])
    with col1:
        country = st.selectbox("국가 선택", options=countries, index=0, key="country_select")
    with col2:
        sort_desc = st.toggle("비율순 정렬", value=True, key="sort_desc_country")

    # 선택된 국가의 데이터
    row = df[df["Country"] == country].iloc[0]
    values = row[mbti_cols].values.tolist()
    labels = mbti_cols.copy()

    # 정렬 옵션 적용
    if sort_desc:
        pairs = sorted(zip(labels, values), key=lambda x: x[1], reverse=True)
        labels, values = zip(*pairs)
        labels, values = list(labels), list(values)

    # 합계 점검
    total = float(sum(values))
    if "check" in locals() and check and not (0.95 <= total <= 1.05):
        st.warning(f"선택 국가의 MBTI 합계가 1과 다릅니다: 합계 = {total:.3f}")

    # 색상 지정(1등 빨강, 나머지는 파란 그라데이션 - 요청: 그라데이션 반대로)
    colors = bar_colors_for_values(values, top_color="red")
    # 그라데이션 뒤집기
    if len(colors) > 1:
        top_idx = colors.index("red")
        others = [c for i, c in enumerate(colors) if i != top_idx]
        others = list(reversed(others))
        colors = []
        cnt = 0
        for i in range(len(values)):
            if i == top_idx:
                colors.append("red")
            else:
                colors.append(others[cnt]); cnt += 1

    # Plotly 막대 그래프
    fig = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=values,
                marker=dict(color=colors),
                hovertemplate="<b>%{x}</b><br>비율: %{y:.2%}<extra></extra>",
                text=[f"{v*100:.1f}%" for v in values],
                textposition="outside",
            )
        ]
    )
    fig.update_layout(
        title=f"{country} — MBTI 유형 비율",
        xaxis_title="MBTI 유형",
        yaxis_title="비율",
        yaxis_tickformat=",.0%",
        template="plotly_white",
        margin=dict(t=60, r=20, b=60, l=60),
        height=560,
    )

    st.plotly_chart(fig, use_container_width=True)

    # 하단: 간단 표(접기)
    with st.expander("데이터 보기"):
        st.dataframe(pd.DataFrame({"Type": labels, "Ratio": values}))
        st.write(f"합계: **{total:.3f}**")

    st.caption("※ 1등 막대는 빨간색, 나머지는 파란색 계열 그라데이션(반전)으로 표시됩니다.")

# ── [탭 2] 유형별: 특정 MBTI 유형의 상위 국가 비교 ─────────────────
with tab_type:
    colA, colB = st.columns([2,1])
    with colA:
        sel_type = st.selectbox("MBTI 유형 선택", options=mbti_cols, index=mbti_cols.index("INFJ") if "INFJ" in mbti_cols else 0, key="type_select")
    with colB:
        top_n = st.number_input("표시할 상위 국가 수", min_value=5, max_value=20, value=10, step=1, key="topn_input")

    # 선택 유형 기준 상위 국가 정렬
    tmp = df[["Country", sel_type]].sort_values(by=sel_type, ascending=False).reset_index(drop=True)
    top_df = tmp.head(int(top_n)).copy()

    # South Korea(여러 표기 허용) 포함 보장
    def find_korea_row(source_df: pd.DataFrame, col_country: str = "Country"):
        # 허용 표기 후보
        candidates = [
            "South Korea", "Korea, South", "Republic of Korea", "대한민국", "Korea (South)",
        ]
        # 우선 정확 일치(대소문자 무시)
        for cand in candidates:
            m = source_df[source_df[col_country].str.lower() == cand.lower()]
            if len(m):
                return m.iloc[0]
        # 부분 일치(대한/코리아/남한 등)
        keys = ["south korea", "korea, south", "republic of korea", "대한민국", "korea"]
        m = source_df[source_df[col_country].str.lower().str.contains("|".join(keys), na=False)]
        if len(m):
            return m.iloc[0]
        return None

    kr_row = find_korea_row(tmp)
    kr_included = False
    if kr_row is not None:
        kr_name = kr_row["Country"]
        if (top_df["Country"].str.lower() == kr_name.lower()).any():
            kr_included = True
        else:
            # 상위 목록 뒤에 추가(요청사항: 포함되지 않으면 마지막에 추가)
            top_df = pd.concat([top_df, kr_row.to_frame().T], ignore_index=True)

    # 시각화 데이터
    x_labels = top_df["Country"].tolist()
    y_vals = top_df[sel_type].tolist()

    # 색상: 기본 파란 그라데이션 + 한국은 빨간색
    colors2 = bar_colors_for_values(y_vals, top_color="red")
    # 한국 막대만 빨강으로 강제
    for i, name in enumerate(x_labels):
        if kr_row is not None and str(name).lower() == str(kr_row["Country"]).lower():
            colors2[i] = "red"
        elif colors2[i] == "red":
            # 1등이 한국이 아닐 경우, 자동 빨강을 블루톤으로 보정
            colors2[i] = sample_colorscale("Blues", [0.6])[0]

    fig2 = go.Figure(
        data=[
            go.Bar(
                x=x_labels,
                y=y_vals,
                marker=dict(color=colors2),
                hovertemplate="<b>%{x}</b><br>비율: %{y:.2%}<extra></extra>",
                text=[f"{v*100:.1f}%" for v in y_vals],
                textposition="outside",
            )
        ]
    )
    fig2.update_layout(
        title=f"{sel_type} 비율 상위 국가",
        xaxis_title="국가",
        yaxis_title="비율",
        yaxis_tickformat=",.0%",
        template="plotly_white",
        margin=dict(t=60, r=20, b=60, l=60),
        height=560,
    )

    st.plotly_chart(fig2, use_container_width=True)

    # 표 & 안내
    with st.expander("데이터 보기"):
        st.dataframe(top_df.rename(columns={sel_type: "Ratio"}))
        if kr_row is None:
            st.info("데이터에 South Korea(대한민국) 표기가 존재하지 않아 추가하지 못했습니다.")
        elif not kr_included:
            st.caption("요청에 따라 South Korea를 목록 마지막에 추가했습니다.")

    st.caption("※ 상위 N개 국가는 선택한 유형 비율 기준으로 내림차순입니다. South Korea가 상위권에 없으면 목록 끝에 추가되며, 한국 막대는 항상 빨간색으로 표시됩니다.")

# ── [탭 3] 코드 보기: app.py & requirements.txt ─────────────────────
with tab_code:
    st.subheader("📄 앱 코드 보기 (복사/다운로드 가능)")
    from pathlib import Path
    try:
        code_text = Path(__file__).read_text(encoding="utf-8")
    except Exception:
        # 일부 환경에서는 __file__ 접근이 제한될 수 있어 백업 경로를 시도
        try:
            code_text = Path("app.py").read_text(encoding="utf-8")
        except Exception:
            code_text = "현재 실행 환경에서 소스 코드를 읽어올 수 없습니다. 리포지토리의 app.py를 확인해주세요."

    st.code(code_text, language="python")
    st.download_button("app.py 다운로드", data=code_text, file_name="app.py", mime="text/x-python")

    st.divider()
    st.subheader("📦 requirements.txt")
    req_text = """streamlit>=1.39.0
pandas>=2.2.2
plotly>=5.24.1
"""
    st.code(req_text, language="text")
    st.download_button("requirements.txt 다운로드", data=req_text, file_name="requirements.txt", mime="text/plain")


