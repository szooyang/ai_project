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
st.caption("국가를 선택하면 16개 MBTI 유형 비율을 인터랙티브 막대 그래프로 보여줍니다.")

# 국가 선택
countries = df["Country"].sort_values().tolist()
col1, col2 = st.columns([2, 1])
with col1:
    country = st.selectbox("국가 선택", options=countries, index=0)
with col2:
    sort_desc = st.toggle("비율순 정렬", value=True)

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

# 색상 지정(1등 빨강, 나머지는 파란 그라데이션)
colors = bar_colors_for_values(values, top_color="red")

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

st.caption("※ 1등 막대는 빨간색, 나머지는 파란색 계열 그라데이션으로 표시됩니다. 업로더로 다른 CSV도 사용할 수 있습니다.")

