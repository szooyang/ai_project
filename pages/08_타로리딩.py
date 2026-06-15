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
# 카드 이미지 매핑
# -----------------------
image_map = {}

for card in tarot_json["cards"]:
    image_map[card["name"]] = card["img"]

# -----------------------
# 카드 상세정보 매핑
# -----------------------
card_info = {}

for card in tarot_json["cards"]:
    card_info[card["name"]] = card

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
# 질문
# -----------------------
question = st.text_area(
    "무엇이 궁금한가요?",
    placeholder="예) 올해 진로는 어떻게 될까요?"
)

# -----------------------
# 스프레드 선택
# -----------------------
spread = st.radio(
    "스프레드 선택",
    ["1장 리딩", "3장 리딩"],
    horizontal=True
)

# -----------------------
# 셔플
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

        card_data = card_info.get(card_name, {})

        image_file = image_map.get(card_name)

        with cols[i]:

            st.subheader(positions[i])

            image_path = image_dir / image_file

            if image_path.exists():
                st.image(image_path)

            st.markdown(f"### {card_name}")
            st.write(orientation)

            # 의미 선택
            if orientation == "정방향":

                if "meanings" in card_data:
                    meanings = card_data["meanings"].get("light", [])
                    meaning = random.choice(meanings)

                else:
                    meaning = "새로운 가능성을 의미합니다."

            else:

                if "meanings" in card_data:
                    meanings = card_data["meanings"].get("shadow", [])
                    meaning = random.choice(meanings)

                else:
                    meaning = "주의가 필요한 상황입니다."

            st.info(meaning)

            summary.append(
                f"{positions[i]}의 {card_name}({orientation}) 카드는 '{meaning}'을 의미합니다."
            )

    st.divider()

    # -----------------------
    # 종합 리딩
    # -----------------------
    st.header("✨ 종합 리딩")

    reading = ""

    if spread == "1장 리딩":

        reading += f"""
현재 상황에 대한 조언 카드가 나타났습니다.

{summary[0]}

이 카드는 지금의 상황을 객관적으로 바라보고,
카드가 전달하는 메시지를 참고하라는 의미를 담고 있습니다.
"""

    else:

        reading += f"""
질문: {question}

과거에는 현재 상황의 원인이 되는 사건이나 경험이 있었음을 보여줍니다.

{summary[0]}

현재는 지금 가장 중요한 에너지를 나타냅니다.

{summary[1]}

미래는 현재의 흐름이 이어질 경우 예상되는 방향성을 의미합니다.

{summary[2]}

세 장의 카드를 종합하면,
현재의 경험을 통해 성장하고 변화하는 과정에 있으며,
자신의 선택과 행동에 따라 더 좋은 방향으로 나아갈 수 있음을 시사합니다.
"""

    st.success(reading)

    # -----------------------
    # 키워드
    # -----------------------
    st.header("🔑 핵심 키워드")

    keyword_set = []

    for card_name in selected_cards:

        card = card_info.get(card_name, {})

        if "keywords" in card:
            keyword_set.extend(card["keywords"][:4])

    keyword_set = list(dict.fromkeys(keyword_set))

    st.write(" · ".join(keyword_set[:12]))

    # -----------------------
    # 생각해볼 질문
    # -----------------------
    st.header("💭 스스로에게 던져볼 질문")

    for card_name in selected_cards:

        card = card_info.get(card_name, {})

        if "Questions to Ask" in card:

            question_list = card["Questions to Ask"]

            if len(question_list) > 0:
                st.markdown(
                    f"- {random.choice(question_list)}"
                )

    st.divider()

    st.caption(
        "본 결과는 오락 및 자기성찰 목적으로만 활용하세요."
    )
