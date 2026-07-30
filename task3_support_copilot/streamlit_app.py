"""Streamlit chat UI for the Support Copilot (bonus)."""
import os
import uuid

import requests
import streamlit as st

API = os.getenv("API_URL", "http://localhost:8003")

st.set_page_config(page_title="Support Copilot", page_icon="💬")
st.title("💬 Customer Support Copilot")

if "session_id" not in st.session_state:
    st.session_state.session_id = f"ui-{uuid.uuid4().hex[:8]}"
if "messages" not in st.session_state:
    st.session_state.messages = []

st.caption(f"Session: `{st.session_state.session_id}` · answers grounded in the FAQ; low-confidence queries escalate.")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

if prompt := st.chat_input("Ask a support question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        resp = requests.post(
            f"{API}/chat",
            json={"session_id": st.session_state.session_id, "message": prompt},
            timeout=120,
        ).json()
        if resp.get("escalate"):
            st.warning(resp["answer"])
        else:
            st.write(resp["answer"])
        st.caption(f"confidence={resp.get('confidence')}")
        with st.expander("📎 Evidence"):
            for i, s in enumerate(resp.get("sources", []), 1):
                st.markdown(f"**[{i}] {s['metadata'].get('source','?')}** · score={s['score']}")
                st.write(s["text"])
    st.session_state.messages.append({"role": "assistant", "content": resp["answer"]})
