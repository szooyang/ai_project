# 파일 위치 예시: pages/05_dessert_top_cafe.py

import streamlit as st
import pandas as pd
from pathlib import Path
import folium
from streamlit_folium import st_folium

# 지오코딩을 위한 geopy (카페/지하철 위치 좌표 얻기)
from geopy.geocoders import Nominatim


@st.cache_data
def load_data():
    """상위 폴더에 있는 CSV 파일 불러오기"""
    root_dir = Path(__file__).resolve().parent.parent
    cafe_path = root_dir / "CAFE.csv"
    dessert_path = root_dir / "DESSERT.csv"

    cafe_df = pd.read_csv(cafe_path, encoding="utf-8-sig")
    dessert_df = pd.read_csv(dessert_path, encoding="utf-8-sig")

    # 날짜 컬럼 datetime 변환
    dessert_df["날짜"] = pd.to_datetime(dessert_df["날짜"])
    return cafe_df, dessert_df


@st.cache_data
def geocode(address: str):
    """주소를 위/경도로 변환 (Nominatim 사용, 세션 내 캐시)"""
    geolocator = Nominatim(user_agent="dessert_top_cafe_app")
    try:
        location = geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude
    except Exception:
        pass
    return None, None


def get_recent_top_desserts(dessert_df, months: int = 3, top_n: int = 3):
    """최근 N개월 기준 인기 TOP 디저트 선정 (평균값 기준)"""
    max_date = dessert_df["날짜"].max()
    start_date = max_date - pd.DateOffset(months=months)
    recent = dessert_df[dessert_df["날짜"] >= start_date]

    # 날짜 컬럼 제외하고 평균 계산
    mean_values = recent.drop(columns=["날짜"]).mean().sort_values(ascending=False)
    top = mean_values.head(top_n)
    return top, start_date, max_date


def build_cafe_info_dict():
    """
    카페별 '가까운 지하철역' 정보 딕셔너리
    (웹에서 미리 조사해서 하드코딩한 정보)
    """
    return {
        "띵베이크샵": {
            "subway_name": "제기동역",
            "subway_line": "1호선",
        },
        "올더어글리쿠키&트레몽": {
            "subway_name": "합정역",
            "subway_line": "2·6호선",
        },
        "사이드테이블": {
            "subway_name": "홍대입구역",
            "subway_line": "2·경의중앙·공항철도",
        },
        "크림시크": {
            "subway_name": "명동역",
            "subway_line": "4호선",
        },
        "펠트커피 청계천점": {
            "subway_name": "광화문역",
            "subway_line": "5호선",
        },
        "라에비뉴 성수": {
            "subway_name": "성수역",
            "subway_line": "2호선",
        },
        "브론시스": {
            "subway_name": "홍대입구역",
            "subway_line": "2·경의중앙·공항철도",
        },
        "슈밤": {
            "subway_name": "서울숲역",
            "subway_line": "수인분당선",
        },
        "작당모의": {
            "subway_name": "홍대입구역",
            "subway_line": "2·경의중앙·공항철도",
        },
        "센트럴사이트 연남점": {
            "subway_name": "홍대입구역",
            "subway_line": "2·경의중앙·공항철도",
        },
    }


def make_map(cafe_rows, cafe_info_dict):
    """
    선택한 디저트에 해당하는 카페 2곳과
    각각 근처 지하철역을 folium 지도에 표시
    """
    markers = []

    # 카페 마커 좌표 수집
    for _, row in cafe_rows.iterrows():
        for cafe_col, addr_col in [("카페1", "위치1"), ("카페2", "위치2")]:
            cafe_name = row[cafe_col]
            address = row[addr_col]

            if pd.isna(cafe_name) or pd.isna(address):
                continue

            lat, lon = geocode(str(address))
            if lat is None:
                continue

            markers.append(
                {
                    "type": "cafe",
                    "name": cafe_name,
                    "address": address,
                    "lat": lat,
                    "lon": lon,
                }
            )

            # 지하철역 정보 있으면 같이 처리
            info = cafe_info_dict.get(cafe_name)
            if info:
                subway_query = f"서울 {info['subway_name']}"
                slat, slon = geocode(subway_query)
                if slat is not None:
                    markers.append(
                        {
                            "type": "subway",
                            "name": f"{info['subway_name']} ({info['subway_line']})",
                            "lat": slat,
                            "lon": slon,
                        }
                    )

    if not markers:
        st.info("지오코딩에 실패해서 지도를 표시할 수 없습니다. 주소/네트워크를 확인해주세요.")
        return

    # 지도 중심 = 마커들의 평균 위치
    center_lat = sum(m["lat"] for m in markers) / len(markers)
    center_lon = sum(m["lon"] for m in markers) / len(markers)

    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

    for mkr in markers:
        if mkr["type"] == "cafe":
            popup = f"{mkr['name']}<br>{mkr['address']}"
            folium.Marker(
                [mkr["lat"], mkr["lon"]],
                popup=popup,
                tooltip=mkr["name"],
                icon=folium.Icon(icon="coffee", prefix="fa"),
            ).add_to(m)
        else:  # subway
            popup = mkr["name"]
            folium.Marker(
                [mkr["lat"], mkr["lon"]],
                popup=popup,
                tooltip=mkr["name"],
                icon=folium.Icon(icon="train", prefix="fa", color="green"),
            ).add_to(m)

    st_folium(m, width=800, height=500)


def main():
    st.title("최근 3개월 인기 디저트 TOP & 카페 추천 지도")

    cafe_df, dessert_df = load_data()
    cafe_info_dict = build_cafe_info_dict()

    # 최근 3개월 TOP 디저트 계산
    top_mean, start_date, max_date = get_recent_top_desserts(dessert_df, months=3, top_n=3)

    st.subheader("최근 3개월 기준 인기 디저트 TOP")
    st.caption(f"기간: {start_date.date()} ~ {max_date.date()} 기준 (평균값)")

    # 표로 간단히 보여주기
    st.dataframe(
        top_mean.reset_index().rename(columns={"index": "디저트", 0: "최근 3개월 평균"}),
        hide_index=True,
    )

    # 디저트 선택
    dessert_choice = st.selectbox(
        "카페 추천을 보고 싶은 디저트를 선택하세요.",
        options=top_mean.index.tolist(),
    )

    # 선택한 디저트에 해당하는 카페 정보 추출
    selected_cafe_rows = cafe_df[cafe_df["디저트"] == dessert_choice]

    if selected_cafe_rows.empty:
        st.warning("해당 디저트에 대한 카페 정보가 CAFE.csv에 없습니다.")
        return

    st.markdown("---")
    st.subheader(f"✅ '{dessert_choice}' 대표 카페 추천")

    row = selected_cafe_rows.iloc[0]
    col1, col2 = st.columns(2)

    cafe1 = row["카페1"]
    cafe2 = row["카페2"]
    addr1 = row["위치1"]
    addr2 = row["위치2"]

    info1 = cafe_info_dict.get(cafe1, {})
    info2 = cafe_info_dict.get(cafe2, {})

    with col1:
        st.markdown(f"**1. {cafe1}**")
        st.write(addr1)
        if info1:
            st.write(f"가까운 지하철역: **{info1['subway_name']} ({info1['subway_line']})**")

    with col2:
        st.markdown(f"**2. {cafe2}**")
        st.write(addr2)
        if info2:
            st.write(f"가까운 지하철역: **{info2['subway_name']} ({info2['subway_line']})**")

    st.markdown("---")
    st.subheader("🗺 지도에서 카페 & 지하철역 보기")

    st.caption("※ 지오코딩은 외부 서비스(Nominatim)를 사용하므로 최초 로딩 시 시간이 조금 걸릴 수 있습니다.")

    make_map(selected_cafe_rows, cafe_info_dict)


if __name__ == "__main__":
    main()
