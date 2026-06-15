import streamlit as st
import pandas as pd
import json
import random
import time
from pathlib import Path

# -----------------------
# 페이지 설정
# -----------------------
st.set_page_config(
    page_title="AI 타로 리딩",
    page_icon="🔮",
    layout="wide"
)

# -----------------------
# 경로
# -----------------------
BASE_DIR = Path(__file__).resolve().parent.parent

csv_path = BASE_DIR / "tarot_card_meanings.csv"
json_path = BASE_DIR / "tarot-images.json"
image_dir = BASE_DIR / "images"

# -----------------------
# 데이터 로드
# -----------------------
@st.cache_data
def load_data():
    df = pd.read_csv(csv_path)

    with open(json_path, encoding="utf-8") as f:
        tarot_json = json.load(f)

    return df, tarot_json

df, tarot_json = load_data()

# -----------------------
# 이미지 매핑
# -----------------------
image_map = {}

for card in tarot_json["cards"]:
    image_map[card["name"]] = card["img"]

# -----------------------
# 카드 정보 매핑
# -----------------------
card_info = {}

for card in tarot_json["cards"]:
    card_info[card["name"]] = card

# -----------------------
# CSV 정보 매핑
# -----------------------
csv_info = {}

for _, row in df.iterrows():
    csv_info[str(row["card_name"]).strip()] = row

# -----------------------
# 제목
# -----------------------
st.title("🔮 AI 타로 리딩")

st.markdown(
"""
당신의 질문에 대해 카드를 통해 조언을 받아보세요.

카드는 미래를 예언하지 않으며,
현재 상황을 돌아보는 참고용입니다.
"""
)

# -----------------------
# 질문 유형
# -----------------------
reading_type = st.selectbox(
    "질문 유형",
    ["일반", "연애", "진로"]
)

# -----------------------
# 질문 입력
# -----------------------
question = st.text_area(
    "무엇이 궁금한가요?",
    placeholder="예) 올해 진로는 어떻게 될까요?"
)

# -----------------------
# 스프레드
# -----------------------
spread = st.radio(
    "스프레드 선택",
    ["1장 리딩", "3장 리딩"],
    horizontal=True
)

# -----------------------
# 카드 셔플
# -----------------------
if st.button("🃏 카드 셔플"):

    if not question.strip():
        st.warning("질문을 입력해주세요.")
        st.stop()

    with st.spinner("카드를 섞는 중..."):
        time.sleep(2)

    cards = list(image_map.keys())

    if spread == "1장 리딩":
        selected_cards = random.sample(cards, 1)
        positions = ["현재"]
    else:
        selected_cards = random.sample(cards, 3)
        positions = ["과거", "현재", "미래"]

    st.divider()

    cols = st.columns(len(selected_cards))

    summary = []

    for i, card_name in enumerate(selected_cards):

        orientation = random.choice(["정방향", "역방향"])

        image_file = image_map.get(card_name)

        csv_card = csv_info.get(card_name)

        with cols[i]:

            st.subheader(positions[i])

            image_path = image_dir / image_file

            if image_path.exists():
                st.image(str(image_path))

            st.markdown(f"### {card_name}")
            st.write(orientation)

            # -----------------------
            # 의미 선택
            # -----------------------
            if csv_card is not None:

                if reading_type == "연애":

                    meaning = str(csv_card["love_meaning"])

                elif reading_type == "진로":

                    meaning = str(csv_card["career_meaning"])

                else:

                    if orientation == "정방향":
                        meaning = str(csv_card["upright_meaning"])
                    else:
                        meaning = str(csv_card["reversed_meaning"])

            else:

                meaning = "해석 정보가 없습니다."

            st.info(meaning)

            summary.append(
                f"{positions[i]}의 {card_name}({orientation}) 카드는 '{meaning}'을 의미합니다."
            )

    st.divider()

    # -----------------------
    # 종합 리딩
    # -----------------------
    st.header("✨ 종합 리딩")

    if spread == "1장 리딩":

        reading = f"""
현재 상황에 대한 조언 카드가 나타났습니다.

{summary[0]}

이 카드는 현재의 상황을 되돌아보고
앞으로의 방향을 고민해보라는 메시지를 담고 있습니다.
"""

    else:

        reading = f"""
질문 : {question}

{summary[0]}

{summary[1]}

{summary[2]}

세 장의 카드를 종합하면 현재 상황을 이해하고,
앞으로의 선택에 신중함과 자신감을 함께 가져야 함을 의미합니다.
"""

    st.success(reading)

    # -----------------------
    # 키워드
    # -----------------------
    st.header("🔑 카드 키워드")

    keyword_set = []

    for card_name in selected_cards:

        card = card_info.get(card_name, {})

        if "keywords" in card:
            keyword_set.extend(card["keywords"][:4])

    keyword_set = list(dict.fromkeys(keyword_set))

    if len(keyword_set) > 0:
        st.write(" · ".join(keyword_set))

    # -----------------------
    # 생각해볼 질문
    # -----------------------
    st.header("💭 스스로에게 던져볼 질문")

    for card_name in selected_cards:

        card = card_info.get(card_name, {})

        if "Questions to Ask" in card:

            q_list = card["Questions to Ask"]

            if len(q_list) > 0:
                st.markdown(
                    f"- {random.choice(q_list)}"
                )

    st.divider()

    st.caption(
        "본 결과는 오락 및 자기성찰 목적으로만 활용하세요."
    )
