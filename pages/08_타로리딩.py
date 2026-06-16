import streamlit as st
import pandas as pd
import json, random, time
from pathlib import Path

st.set_page_config(page_title="AI 타로 리딩", page_icon="🔮", layout="wide")

BASE_DIR = Path(__file__).resolve().parent.parent
csv_path = BASE_DIR / "tarot_card_meanings.csv"
json_path = BASE_DIR / "tarot-images.json"
image_dir = BASE_DIR / "images"

CARD_BACK = image_dir / "card_back.jpg"
CARD_BACK_CHOICE = image_dir / "card_back_choice.jpg"

@st.cache_data
def load_data():
    df = pd.read_csv(csv_path)
    with open(json_path, encoding="utf-8") as f:
        tarot_json = json.load(f)
    return df, tarot_json

df, tarot_json = load_data()

image_map = {}
card_info = {}
for card in tarot_json["cards"]:
    image_map[card["name"]] = card["img"]
    card_info[card["name"]] = card

csv_info = {}
for _, row in df.iterrows():
    csv_info[str(row["card_name"]).strip()] = row

if "deck_cards" not in st.session_state:
    st.session_state.deck_cards = None

if "chosen_cards" not in st.session_state:
    st.session_state.chosen_cards = []

st.title("🔮 AI 타로 리딩")

reading_type = st.selectbox("질문 유형", ["일반", "연애", "진로"])

question = st.text_area(
    "무엇이 궁금한가요?",
    placeholder="예) 올해 진로는 어떻게 될까요?"
)

if st.button("🃏 카드 셔플 시작"):

    if not question.strip():
        st.warning("질문을 입력해주세요.")
        st.stop()

    with st.spinner("카드를 섞는 중..."):
        time.sleep(2)

    st.session_state.deck_cards = random.sample(
        list(image_map.keys()), 21
    )

    st.session_state.chosen_cards = []
    st.rerun()

if st.session_state.deck_cards:

    st.divider()
    st.subheader(
        f"카드를 선택하세요 ({len(st.session_state.chosen_cards)}/3)"
    )

    for row in range(3):

        cols = st.columns(7)

        for col in range(7):

            idx = row * 7 + col
            card_name = st.session_state.deck_cards[idx]

            with cols[col]:

                selected = card_name in st.session_state.chosen_cards

                img = CARD_BACK_CHOICE if selected else CARD_BACK

                if img.exists():
                    st.image(str(img), use_container_width=True)

                if not selected and len(st.session_state.chosen_cards) < 3:

                    if st.button("선택", key=f"c{idx}"):
                        st.session_state.chosen_cards.append(card_name)
                        st.rerun()

    if len(st.session_state.chosen_cards) == 3:

        st.divider()
        st.header("✨ 선택된 카드")

        positions = ["과거", "현재", "미래"]
        cols = st.columns(3)
        summary = []

        for i, card_name in enumerate(st.session_state.chosen_cards):

            orientation = random.choice(["정방향", "역방향"])

            csv_card = csv_info.get(card_name)

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

            with cols[i]:

                st.subheader(positions[i])

                image_file = image_map.get(card_name)
                image_path = image_dir / image_file

                if image_path.exists():
                    st.image(str(image_path), use_container_width=True)

                name_ko = card.get(
                    "name_ko",
                    card_name
                )

                st.markdown(
                    f"**{name_ko} ({card_name})**"
                )
                st.write(orientation)
                st.info(meaning)

            summary.append(f"{positions[i]} : {meaning}")

        st.divider()
        st.header("🔮 종합 리딩")

        st.success(f"""
질문 : {question}

{summary[0]}

{summary[1]}

{summary[2]}

세 장의 카드는 현재의 흐름과 앞으로의 가능성을 보여줍니다.
""")

        st.header("🔑 카드 키워드")

        keywords = []

        for card_name in st.session_state.chosen_cards:

            card = card_info.get(card_name, {})

            if "keywords_ko" in card:

                keywords.extend(
                card["keywords_ko"][:4]
            )

            elif "keywords" in card:

                keywords.extend(
                card["keywords"][:4]
            )

        keywords = list(dict.fromkeys(keywords))

        if keywords:
            st.write(" · ".join(keywords))

st.header("💭 스스로에게 던져볼 질문")

for card_name in st.session_state.chosen_cards:

    card = card_info.get(card_name, {})

    if "questions_ko" in card:

        q = card["questions_ko"]

        if q:
            st.markdown(
                f"- {random.choice(q)}"
            )

    elif "Questions to Ask" in card:

        q = card["Questions to Ask"]

        if q:
            st.markdown(
                f"- {random.choice(q)}"
            )

        st.caption("본 결과는 오락 및 자기성찰 목적으로만 활용하세요.")
