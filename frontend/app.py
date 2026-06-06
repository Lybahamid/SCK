import streamlit as st

from api import (
    generate_context,
    get_sessions,
    get_session,
    get_contexts,
    delete_session,
)

st.set_page_config(
    page_title="SCK Testing Dashboard",
    layout="wide",
)

st.title("SCK Testing Dashboard")

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Generate Context",
        "Sessions",
        "Session Details",
        "Contexts",
    ]
)

# --------------------------------------------------
# Generate Context
# --------------------------------------------------

with tab1:
    st.header("Generate Context")

    text = st.text_area(
        "Conversation Text",
        height=300,
    )

    col1, col2 = st.columns(2)

    with col1:
        strategy = st.selectbox(
    "Strategy",
    [
        "full",
        "concise",
        "technical",
        "creative",
        "full_ai",
    ],
)

    with col2:
        target_platform = st.selectbox(
            "Target Platform",
            [
                "generic",
                "chatgpt",
                "claude",
            ],
        )

    if st.button("Generate Context"):
        if not text.strip():
            st.warning("Please enter some conversation text.")
        else:
            try:
                response = generate_context(
                    text,
                    strategy,
                    target_platform,
                )

                if response.status_code == 200:
                    payload = response.json()

                    st.success("Context generated successfully.")

                    st.json(payload)

                    if (
                        "data" in payload
                        and "context" in payload["data"]
                    ):
                        st.text_area(
                            "Generated Context",
                            payload["data"]["context"],
                            height=400,
                        )

                else:
                    st.error(response.text)

            except Exception as e:
                st.error(str(e))


# --------------------------------------------------
# Sessions
# --------------------------------------------------

with tab2:
    st.header("Session History")

    if st.button("Refresh Sessions"):
        response = get_sessions()

        if response.status_code == 200:
            payload = response.json()

            st.write(
                f"Total Sessions: {payload.get('total', 0)}"
            )

            sessions = payload.get("sessions", [])

            if sessions:
                st.dataframe(sessions)
            else:
                st.info("No sessions found.")
        else:
            st.error(response.text)


# --------------------------------------------------
# Session Details
# --------------------------------------------------

with tab3:
    st.header("Session Details")

    session_id = st.text_input(
        "Session ID",
        key="details_session_id",
    )

    if st.button("Get Session"):
        if session_id:
            response = get_session(session_id)

            if response.status_code == 200:
                st.json(response.json())
            else:
                st.error(response.text)


# --------------------------------------------------
# Contexts
# --------------------------------------------------

with tab4:
    st.header("Session Contexts")

    context_session_id = st.text_input(
        "Session ID",
        key="contexts_session_id",
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Get Contexts"):
            if context_session_id:
                response = get_contexts(
                    context_session_id
                )

                if response.status_code == 200:
                    st.json(response.json())
                else:
                    st.error(response.text)

    with col2:
        if st.button("Delete Session"):
            if context_session_id:
                response = delete_session(
                    context_session_id
                )

                if response.status_code == 200:
                    st.success(
                        "Session deleted successfully."
                    )
                    st.json(response.json())
                else:
                    st.error(response.text)