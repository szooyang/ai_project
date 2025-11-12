import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import io
import plotly.graph_objects as go

# ==============================
# 유틸
# ==============================
POSSIBLE_AGE = ["age", "연령", "나이", "AGE", "Age"]
POSSIBLE_POP = ["population", "pop", "인구", "인구수", "Population"]
POSSIBLE_DIST = [
    "district", "adm", "adm_name", "행정구", "행정동", "구",
    "시군구", "자치구", "지역", "District", "행정구역"  # ✅ 행정구역 포함
]

def read_csv_smart(file_path_or_buf):
    encodings = ["utf-8-sig", "cp949", "utf-8"]
    for enc in encodings:
        try:
            if isinstance(file_path_or_buf, (str, Path)):
                return pd.read_csv(file_path_or_buf, encoding=enc)
            else:
                file_path_or_buf.seek(0)
                data = file_path_or_buf.read()
                buf = io.BytesIO(data)
                return pd.read_csv(buf, encoding=enc)
        except Exception:
            continue
    st.error("CSV 인코딩을 인식할 수 없습니다.")
    st.stop()

def guess_col(cols, candidates):
    lower_map = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    for c in cols:
        cl = c.lower()
        if any(k in cl for k in ["age", "나이", "연령"]):
            return c
        if any(k in cl for k in ["pop", "인구"]):
            return c
        if any(k in cl for k in ["district", "행정", "자치", "시군구", "동", "구", "지역", "행정구역"]):
            return c
    return None

def ensure_numeric_age(s: pd.Series) -> pd.Series:
    out = pd.to_numeric(s, errors="coerce")
    if out.notna().any():
        return out
    return pd.to_numeric(s.astype(str).str.extract(r"(\d+)")[0], errors="coerce")

# ==============================
# 앱
# ==============================
st.set_page_config(page_title="행정구역 인구구조", layout="wide")
st.title("행정구역 인구구조")
st.caption("가로축: **나이**, 세로축: **인구수** · 회색 배경 · X축 10살 간격 · Y축 100명 간격")

# population.csv 읽기
DATA_PATH = "population.csv"
if not Path(DATA_PATH).exists():
    st.error("population.csv 파일을 app.py와 같은 폴더에 두어야 합니다.")
    st.stop()

df = read_csv_smart(DATA_PATH)

# 컬럼 자동 추정
age_col  = guess_col(df.columns, POSSIBLE_AGE)
pop_col  = guess_col(df.columns, POSSIBLE_POP)
dist_col = guess_col(df.columns, POSSIBLE_DIST)

missing_cols = [name for name, val in [("나이", age_col), ("인구수", pop_col), ("행정구역", dist_col)] if val is None]
if missing_cols:
    st.error(
        "열 자동 인식에 실패했습니다. CSV에 다음 의미의 열이 필요합니다: "
        f"{', '.join(missing_cols)} (예: 나이/연령/age, 인구/population, 행정구역/district)"
    )
    st.stop()

# 데이터 정리
df = df.copy()
df["__AGE__"]  = ensure_numeric_age(df[age_col])
df["__POP__"]  = pd.to_numeric(df[pop_col], errors="coerce")
df["__DIST__"] = df[dist_col].astype(str).str.strip()
df = df.dropna(subset=["__AGE__", "__POP__"])

# ✅ 행정구역 리스트 만들기
districts = sorted([d for d in df["__DIST__"].unique() if isinstance(d, str) and d.strip() != ""])
if len(districts) == 0:
    st.warning("⚠️ CSV 파일의 ‘행정구역’ 열에 값이 비어 있습니다. 샘플 데이터를 확인하세요.")
    st.stop()

# ✅ 사용자 선택 가능
selected = st.selectbox("행정구역 선택", districts, index=0)

# 선택된 행정구역의 인구구조
dsel = (
    df[df["__DIST__"] == selected]
      .groupby("__AGE__", as_index=False)["__POP__"]
      .sum()
      .sort_values("__AGE__")
)

# ==============================
# 그래프
# ==============================
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=dsel["__AGE__"],
        y=dsel["__POP__"],
        mode="lines+markers",
        name=selected
    )
)

x_min = np.nanmin(dsel["__AGE__"].values) if len(dsel) else 0
x_start = int(np.floor(x_min / 10)) * 10 if np.isfinite(x_min) else 0

fig.update_layout(
    paper_bgcolor="#f0f0f0",
    plot_bgcolor="#f0f0f0",
    margin=dict(l=40, r=20, t=40, b=40),
    height=520
)
fig.update_xaxes(
    title_text="나이",
    showgrid=True,
    gridcolor="#d0d0d0",
    dtick=10,
    tick0=x_start,
    zeroline=False
)
fig.update_yaxes(
    title_text="인구수",
    showgrid=True,
    gridcolor="#d0d0d0",
    dtick=100,
    zeroline=False
)

st.plotly_chart(fig, use_container_width=True)

# 데이터 미리보기
st.subheader("데이터 미리보기")
st.dataframe(dsel.rename(columns={"__AGE__": "나이", "__POP__": "인구수"}), use_container_width=True)
