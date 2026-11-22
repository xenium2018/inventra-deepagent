"""Minimal Streamlit chat UI.  Run: streamlit run app.py"""
import uuid
import streamlit as st
from agent import ask

st.set_page_config(page_title="Inventra", page_icon="📦")
st.title("📦 Inventra")
st.caption("Inventory & finance assistant - powered by a Deep Agent with skills")

st.session_state.setdefault("thread", str(uuid.uuid4()))
st.session_state.setdefault("history", [])

for role, text in st.session_state.history:
    st.chat_message(role).markdown(text)

if prompt := st.chat_input("Ask about inventory, sales, finance, vendors or tickets..."):
    st.chat_message("user").markdown(prompt)
    with st.chat_message("assistant"), st.spinner("Thinking..."):
        answer = ask(prompt, st.session_state.thread)
        st.markdown(answer)
    st.session_state.history += [("user", prompt), ("assistant", answer)]
