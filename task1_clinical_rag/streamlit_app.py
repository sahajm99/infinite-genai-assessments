"""Streamlit UI for the Clinical Knowledge Assistant (bonus)."""
import os

import requests
import streamlit as st

API = os.getenv("API_URL", "http://localhost:8001")

st.set_page_config(page_title="Clinical Knowledge Assistant", page_icon="🩺")
st.title("🩺 Clinical Knowledge Assistant")
st.caption("Answers are grounded ONLY in the provided (synthetic) clinical corpus.")

if "session_id" not in st.session_state:
    st.session_state.session_id = "streamlit-session"

with st.sidebar:
    st.subheader("Corpus")
    if st.button("Re-index documents"):
        r = requests.post(f"{API}/ingest", timeout=120)
        st.success(r.json())
    try:
        h = requests.get(f"{API}/health", timeout=10).json()
        st.metric("Chunks indexed", h.get("doc_count", "?"))
    except Exception as exc:  # noqa: BLE001
        st.warning(f"API not reachable: {exc}")

question = st.text_input("Ask a clinical question", placeholder="First-line agent for stage 1 hypertension?")
if st.button("Ask", type="primary") and question:
    with st.spinner("Retrieving and reasoning..."):
        resp = requests.post(
            f"{API}/ask",
            json={"question": question, "session_id": st.session_state.session_id},
            timeout=120,
        ).json()

    grounded = resp.get("grounded", False)
    st.markdown(f"### {'✅ Grounded answer' if grounded else '⚠️ Insufficient information'}")
    st.write(resp["answer"])
    st.caption(f"Latency: {resp.get('latency_ms', 0)} ms")

    with st.expander("📎 Cited sources / evidence"):
        for i, s in enumerate(resp.get("sources", []), 1):
            st.markdown(f"**[{i}] {s['metadata'].get('source', 'unknown')}** · score={s['score']}")
            st.write(s["text"])
