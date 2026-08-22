
import uuid

import httpx
import streamlit as st

st.set_page_config(page_title="Live News AI", page_icon="N", layout="centered")
api_url = st.sidebar.text_input("Backend URL", "http://127.0.0.1:8000")
st.sidebar.title("Live News AI")
st.sidebar.caption("Source-grounded answers about what is happening now.")
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if st.sidebar.button("Clear conversation"):
    try:
        httpx.delete(f"{api_url}/api/session/{st.session_state.session_id}", timeout=5)
    except httpx.HTTPError:
        pass
    st.session_state.messages = []
    st.rerun()
st.title("Live News AI")
st.caption("Ask questions about what is happening right now.")
for item in st.session_state.get("messages", []):
    with st.chat_message(item["role"]):
        st.markdown(item["content"])
        if item.get("sources"):
            with st.expander("Sources"):
                for source in item["sources"]:
                    st.markdown(f"[{source['source_name']}: {source['title']}]({source['url']})")
                st.caption(f"Confidence: {item['confidence']} | Searched: {item['searched_at']}")
if prompt := st.chat_input("What happened today?"):
    st.session_state.setdefault("messages", []).append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Researching current sources..."):
            try:
                response = httpx.post(
                    f"{api_url}/api/chat",
                    json={"session_id": st.session_state.session_id, "message": prompt},
                    timeout=60,
                )
                response.raise_for_status()
                data = response.json()
                st.markdown(data["answer"])
                if data["sources"]:
                    with st.expander("Sources"):
                        for source in data["sources"]:
                            st.markdown(
                                f"[{source['source_name']}: {source['title']}]({source['url']})"
                            )
                        st.caption(
                            f"Confidence: {data['confidence']} | Searched: {data['searched_at']}"
                        )
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": data["answer"],
                        "sources": data["sources"],
                        "confidence": data["confidence"],
                        "searched_at": data["searched_at"],
                    }
                )
            except httpx.ConnectError:
                st.error(
                    "Unable to connect to the news agent. "
                    "Please make sure the API server is running."
                )
            except httpx.HTTPStatusError as error:
                try:
                    detail = error.response.json().get(
                        "detail", "The news agent returned an error."
                    )
                except ValueError:
                    detail = "The news agent returned an error."
                st.error(str(detail))
            except (httpx.TimeoutException, ValueError):
                st.error("The news agent took too long to respond. Please try again.")
