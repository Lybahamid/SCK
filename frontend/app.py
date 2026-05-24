import os
import json
import httpx
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")


def call_parse_text(text, source_platform, strategy, target_platform):
    payload = {
        "text": text,
        "source_platform": source_platform,
        "strategy": strategy,
        "target_platform": target_platform,
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(f"{BACKEND_URL}/api/parse/text", json=payload)
        response.raise_for_status()
        return response.json()


def call_parse_link(url, strategy, target_platform):
    payload = {
        "url": url,
        "strategy": strategy,
        "target_platform": target_platform,
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(f"{BACKEND_URL}/api/parse/link", json=payload)
        response.raise_for_status()
        return response.json()


def call_parse_upload(file, source_platform, strategy, target_platform):
    files = {
        "file": (file.name, file.getvalue(), "application/json")
    }

    params = {
        "source_platform": source_platform,
        "strategy": strategy,
        "target_platform": target_platform,
    }

    with httpx.Client(timeout=60.0) as client:
        response = client.post(
            f"{BACKEND_URL}/api/parse/upload",
            params=params,
            files=files,
        )
        response.raise_for_status()
        return response.json()


def check_backend_health():
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{BACKEND_URL}/health")
            response.raise_for_status()
            return True
    except Exception:
        return False


st.set_page_config(
    page_title="SCK - Session Context Keeper",
    page_icon="SCK",
    layout="wide",
)

st.title("SCK - Session Context Keeper")
st.write("Generate structured continuation context for AI conversations.")

# Sidebar
st.sidebar.header("Configuration")

backend_ok = check_backend_health()
if backend_ok:
    st.sidebar.success("Backend is running")
else:
    st.sidebar.error("Backend is not reachable")

input_method = st.sidebar.selectbox(
    "Input Method",
    ["Raw Text", "Share Link", "JSON Upload"]
)

strategy = st.sidebar.selectbox(
    "Context Strategy",
    ["full", "concise", "technical", "creative"],
    index=0,
)

target_platform = st.sidebar.selectbox(
    "Target Platform",
    ["generic", "chatgpt", "claude", "gemini"],
    index=0,
)

st.divider()

response_data = None

if input_method == "Raw Text":
    st.subheader("Paste Conversation Text")

    source_platform = st.selectbox(
        "Source Platform",
        ["unknown", "chatgpt", "claude", "gemini"],
        index=0,
    )

    text_input = st.text_area(
        "Conversation Text",
        height=300,
        placeholder="Paste the conversation here...",
    )

    if st.button("Generate Context", type="primary"):
        if not text_input.strip():
            st.warning("Please paste some conversation text first.")
        else:
            try:
                with st.spinner("Generating context..."):
                    response_data = call_parse_text(
                        text_input,
                        source_platform,
                        strategy,
                        target_platform,
                    )
                st.session_state["last_response"] = response_data
            except httpx.HTTPStatusError as e:
                st.error(f"Backend returned an error: {e.response.text}")
            except Exception as e:
                st.error(f"Request failed: {str(e)}")

elif input_method == "Share Link":
    st.subheader("Paste Shared Conversation Link")

    url_input = st.text_input(
        "Share Link URL",
        placeholder="https://chatgpt.com/share/... or https://claude.ai/...",
    )

    if st.button("Generate Context", type="primary"):
        if not url_input.strip():
            st.warning("Please enter a share link first.")
        else:
            try:
                with st.spinner("Fetching and parsing link..."):
                    response_data = call_parse_link(
                        url_input,
                        strategy,
                        target_platform,
                    )
                st.session_state["last_response"] = response_data
            except httpx.HTTPStatusError as e:
                st.error(f"Backend returned an error: {e.response.text}")
            except Exception as e:
                st.error(f"Request failed: {str(e)}")

elif input_method == "JSON Upload":
    st.subheader("Upload Conversation Export File")

    source_platform = st.selectbox(
        "Export Source Platform",
        ["chatgpt", "claude"],
        index=0,
    )

    uploaded_file = st.file_uploader(
        "Upload JSON File",
        type=["json"],
    )

    if st.button("Generate Context", type="primary"):
        if uploaded_file is None:
            st.warning("Please upload a JSON file first.")
        else:
            try:
                with st.spinner("Uploading and parsing file..."):
                    response_data = call_parse_upload(
                        uploaded_file,
                        source_platform,
                        strategy,
                        target_platform,
                    )
                st.session_state["last_response"] = response_data
            except httpx.HTTPStatusError as e:
                st.error(f"Backend returned an error: {e.response.text}")
            except Exception as e:
                st.error(f"Request failed: {str(e)}")

# Persist latest result after reruns
if "last_response" in st.session_state:
    response_data = st.session_state["last_response"]

if response_data:
    st.divider()
    st.subheader("Generated Context")

    data = response_data.get("data", {})
    context = data.get("context", "")

    meta_col1, meta_col2, meta_col3, meta_col4 = st.columns(4)
    meta_col1.metric("Strategy", data.get("strategy", "N/A"))
    meta_col2.metric("Target Platform", data.get("target_platform", "N/A"))
    meta_col3.metric("Source Platform", data.get("source_platform", "N/A"))
    meta_col4.metric("Message Count", data.get("message_count", 0))

    st.text_area(
        "Context Output",
        value=context,
        height=400,
    )

    st.download_button(
        label="Download Context as TXT",
        data=context,
        file_name="sck_context.txt",
        mime="text/plain",
    )

    with st.expander("Raw API Response"):
        st.json(response_data)