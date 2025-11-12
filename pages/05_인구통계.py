import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import io
import plotly.graph_objects as go

# -------------------------------
# Helpers
# -------------------------------
POSSIBLE_AGE = ["age", "연령", "나이", "AGE", "Age"]
POSSIBLE_POP = ["population", "pop", "인구", "인구수", "Population"]
POSSIBLE_DIST = ["district", "adm", "adm_name", "행정구", "행정동", "구", "시군구", "자치구", "지역", "District"]

def read_csv_smart(file_or_path):
    encodings = ["utf-8-sig", "cp949", "utf-8"]
    last_err = None
    for enc in encodings:
        try:
            if isinstance(file_or_path, (str, Path)):
                return pd.read_csv(file_or_path, encoding=enc)
            else:
                file_or_path.seek(0)
                data = file_or_path.read()
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
    # contain-based fallback
    for c in cols:
        cl = c.lower()
        if any(k in cl for k in ["age", "나이", "연령"]):
            return c
        if any(k in cl for k in ["pop", "인구"]):
            return c
        if any(k in cl for k in ["district", "행정", "자치", "시군구", "동", "구", "지역"]):
            return c
    return None

def ensure_numeric_age(s):
    try:
        return pd.to_numeric(s, errors="coerce")
    except Exception:
        pass
    # e.g., "0-4세", "10대", "20~24" -> 0, 10, 20
    return pd.to_numeric(s.astype(str).str.extract(r'(\d+)')[0], errors="coerce")

# -------------------------------
# App
# -------------------------------
st.set_page_config(page_title="인구 연령 분포 대시보드", layout="wide")

st.title("행정구별 연령-인구 꺾은선 그래프")
st.caption("가로축: 나이, 세로축: 인구수 · 회색 배경, X축 10살 간격 그리드, Y축 100명 간격 그리드")

with st.sidebar:
    st.header("데이터 입력")
    uploaded = st.file_uploader("CSV 업로드 (없으면 프로젝트의 population.csv 사용)", type=["csv"])
    path_fallback = "population.csv"

# 데이터 로드
if uploaded is not None:
    df = read_csv_smart(uploaded)
else:
    try:
        df = read_csv_smart(path_fallback)
    except Exception:
        st.error("데이터를 찾을 수 없습니다. CSV를 업로드 해주세요.")
        st.stop()

# 컬럼 매핑 (자동 추정 + 수동 보정)
age_col = guess_col(df.columns, POSSIBLE_AGE)
pop_col = guess_col(df.columns, POSSIBLE_POP)
dist_col = guess_col(df.columns, POSSIBLE_DIST)

with st.expander("🔧 컬럼 매핑 확인/수정"):
    age_col = st.selectbox("나이 열", options=list(df.columns), index=(list(df.columns).index(age_col) if age_col in df.columns else 0))
    pop_col = st.selectbox("인구수 열", options=list(df.columns), index=(list(df.columns).index(pop_col) if pop_col in df.columns else 0))
    dist_col = st.selectbox("행정구 열", options=list(df.columns), index=(list(df.columns).index(dist_col) if dist_col in df.columns else 0))

# 타입 정리
df = df.copy()
df["__AGE__"] = ensure_numeric_age(df[age_col])
df["__POP__"] = pd.to_numeric(df[pop_col], errors="coerce")
df["__DIST__"] = df[dist_col].astype(str)

# 유효 행만
df = df.dropna(subset=["__AGE__", "__POP__", "__DIST__"])

# 행정구 선택
districts = sorted(df["__DIST__"].unique().tolist())
selected = st.selectbox("행정구 선택", districts, index=0 if districts else None)

# 선택 데이터
dsel = df[df["__DIST__"] == selected].groupby("__AGE__", as_index=False)["__POP__"].sum()
dsel = dsel.sort_values("__AGE__")

# Plotly 그래프
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=dsel["__AGE__"],
        y=dsel["__POP__"],
        mode="lines+markers",
        name=selected
    )
)

# 회색 배경, 그리드 간격 설정 (X: 10살, Y: 100명)
x_min = np.nanmin(dsel["__AGE__"].values) if len(dsel) else 0
x_start = (int(np.floor(x_min/10))*10) if pd.notna(x_min) else 0

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
st.dataframe(dsel.rename(columns={"__AGE__": "나이", "__POP__": "인구수"}))

# (선택) 화면에서 코드 복사하기
with st.expander("📄 앱 코드 보기 / 복사"):
    st.code(Path(__file__).read_text(encoding="utf-8"), language="python")
