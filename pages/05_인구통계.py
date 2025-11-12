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
POSSIBLE_DIST = ["district", "adm", "adm_name", "행정구", "행정동", "구", "시군구", "자치구", "지역", "District"]

def read_csv_smart(file_path_or_buf):
    encodings = ["utf-8-sig", "cp949", "utf-8"]
    last_err = None
    for enc in encodings:
        try:
            if isinstance(file_path_or_buf, (str, Path)):
                return pd.read_csv(file_path_or_buf, encoding=enc)
            else:
                # Buffer
                file_path_or_buf.seek(0)
                data = file_path_or_buf.read()
                buf = io.BytesIO(data)
                return pd.read_csv(buf, encoding=enc)
        except Exception as e:
            last_err = e
    raise last_err

def guess_col(cols, candidates):
    lower_map = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    # 부분 일치
    for c in cols:
        cl = c.lower()
        if any(k in cl for k in ["age", "나이", "연령"]):
            return c
    for c in cols:
        cl = c.lower()
        if any(k in cl for k in ["pop", "인구"]):
            return c
    for c in cols:
        cl = c.lower()
        if any(k in cl for k in ["district", "행정", "자치", "시군구", "동", "구", "지역"]):
            return c
    return None

def ensure_numeric_age(s: pd.Series) -> pd.Series:
    # 바로 숫자 변환 시도
    out = pd.to_numeric(s, errors="coerce")
    if out.notna().any():
        return out
    # 문자열에서 숫자 추출 (예: "0-4세", "10대", "20~24")
    return pd.to_numeric(s.astype(str).str.extract(r"(\d+)")[0], errors="coerce")

# ==============================
# 앱
# ==============================
st.set_page_config(page_title="행정구 인구구조", layout="wide")
st.title("행정구 인구구조")
st.caption("가로축: **나이**, 세로축: **인구수** · 회색 배경 · X축 10살 간격 · Y축 100명 간격")

# 데이터 로드 (업로더 없이, 프로젝트 루트의 population.csv 사용)
DATA_PATH = "population.csv"
if not Path(DATA_PATH).exists():
    st.error("population.csv 파일을 앱과 같은 폴더에 두어야 합니다.")
    st.stop()

try:
    df = read_csv_smart(DATA_PATH)
except Exception as e:
    st.error(f"CSV 읽기 실패: {e}")
    st.stop()

# 컬럼 자동 추정
age_col  = guess_col(df.columns, POSSIBLE_AGE)
pop_col  = guess_col(df.columns, POSSIBLE_POP)
dist_col = guess_col(df.columns, POSSIBLE_DIST)

missing_cols = [name for name, val in [("나이", age_col), ("인구수", pop_col), ("행정구", dist_col)] if val is None]
if missing_cols:
    st.error(
        "열 자동 인식에 실패했습니다. CSV에 다음 의미의 열이 필요합니다: "
        f"{', '.join(missing_cols)}. (예: 나이/연령/age, 인구/population, 행정구/district)"
    )
    st.stop()

# 정제
df = df.copy()
df["__AGE__"]  = ensure_numeric_age(df[age_col])
df["__POP__"]  = pd.to_numeric(df[pop_col], errors="coerce")
df["__DIST__"] = df[dist_col].astype(str)

df = df.dropna(subset=["__AGE__", "__POP__", "__DIST__"])

# 행정구 선택(유일한 인터랙션)
districts = sorted(df["__DIST__"].unique().tolist())
if not districts:
    st.error("행정구 값이 없습니다.")
    st.stop()

selected = st.selectbox("행정구 선택", districts, index=0)

# 선택된 행정구의 인구구조 (나이별 합계)
dsel = (
    df[df["__DIST__"] == selected]
      .groupby("__AGE__", as_index=False)["__POP__"]
      .sum()
      .sort_values("__AGE__")
)

# 그래프
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=dsel["__AGE__"],
        y=dsel["__POP__"],
        mode="lines+markers",
        name=selected
    )
)

# 축/스타일: 회색 배경, X: 10살 단위, Y: 100명 단위
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

# (선택) 표 미리보기
st.subheader("데이터 미리보기")
st.dataframe(
    dsel.rename(columns={"__AGE__": "나이", "__POP__": "인구수"}),
    use_container_width=True
)
