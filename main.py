import streamlit as st
st.title('나의 첫 웹 서비스 만들기!')
st.write('안녕하세요, 만나서 반갑습니다!')
name=st.text_input('이름을 입력해주세요!')
if st.button('인사말 생성'):
  st.write(name+'님! 반갑습니다!')
  st.balloons()
