import requests

API_URL = "http://localhost:8000"


def generate_context(text, strategy, target_platform):
    response = requests.post(
        f"{API_URL}/api/parse/text",
        json={
            "text": text,
            "strategy": strategy,
            "target_platform": target_platform,
        },
    )
    return response


def get_sessions():
    return requests.get(f"{API_URL}/api/sessions")


def get_session(session_id):
    return requests.get(f"{API_URL}/api/sessions/{session_id}")


def get_contexts(session_id):
    return requests.get(f"{API_URL}/api/sessions/{session_id}/contexts")


def delete_session(session_id):
    return requests.delete(f"{API_URL}/api/sessions/{session_id}")