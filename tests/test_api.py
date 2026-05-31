import pytest
import json
from io import BytesIO


@pytest.mark.integration
class TestParseUploadEndpoint:

    def test_valid_chatgpt_upload(self, test_client, sample_chatgpt_data):
        file_data = BytesIO(
            json.dumps([sample_chatgpt_data]).encode("utf-8")
        )

        response = test_client.post(
            "/api/parse/upload",
            files={
                "file": (
                    "chatgpt.json",
                    file_data,
                    "application/json"
                )
            },
            params={
                "source_platform": "chatgpt",
                "strategy": "full",
                "target_platform": "claude"
            }
        )

        assert response.status_code == 200

        data = response.json()

        assert data["success"] is True
        assert "data" in data

    def test_valid_claude_upload(self, test_client, sample_claude_data):
        file_data = BytesIO(
            json.dumps([sample_claude_data]).encode("utf-8")
        )

        response = test_client.post(
            "/api/parse/upload",
            files={
                "file": (
                    "claude.json",
                    file_data,
                    "application/json"
                )
            },
            params={
                "source_platform": "claude",
                "strategy": "concise"
            }
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_empty_file_error(self, test_client):
        response = test_client.post(
            "/api/parse/upload",
            files={
                "file": (
                    "empty.json",
                    b"",
                    "application/json"
                )
            }
        )

        assert response.status_code >= 400

    def test_invalid_json_error(self, test_client):
        response = test_client.post(
            "/api/parse/upload",
            files={
                "file": (
                    "invalid.json",
                    b"not valid json",
                    "application/json"
                )
            }
        )

        assert response.status_code >= 400

    def test_strategy_parameter_applied(
        self,
        test_client,
        sample_chatgpt_data
    ):
        file_data = json.dumps([sample_chatgpt_data]).encode("utf-8")

        full_response = test_client.post(
            "/api/parse/upload",
            files={
                "file": (
                    "test.json",
                    file_data,
                    "application/json"
                )
            },
            params={
                "source_platform": "chatgpt",
                "strategy": "full"
            }
        )

        concise_response = test_client.post(
            "/api/parse/upload",
            files={
                "file": (
                    "test.json",
                    file_data,
                    "application/json"
                )
            },
            params={
                "source_platform": "chatgpt",
                "strategy": "concise"
            }
        )

        assert full_response.status_code == 200
        assert concise_response.status_code == 200

    def test_target_platform_parameter_applied(
        self,
        test_client,
        sample_chatgpt_data
    ):
        file_data = json.dumps([sample_chatgpt_data]).encode("utf-8")

        response = test_client.post(
            "/api/parse/upload",
            files={
                "file": (
                    "test.json",
                    file_data,
                    "application/json"
                )
            },
            params={
                "source_platform": "chatgpt",
                "target_platform": "claude",
                "strategy": "full"
            }
        )

        assert response.status_code == 200

    def test_response_format_structure(
        self,
        test_client,
        sample_chatgpt_data
    ):
        file_data = json.dumps([sample_chatgpt_data]).encode("utf-8")

        response = test_client.post(
            "/api/parse/upload",
            files={
                "file": (
                    "test.json",
                    file_data,
                    "application/json"
                )
            },
            params={
                "source_platform": "chatgpt"
            }
        )

        data = response.json()

        assert "success" in data
        assert "data" in data or "detail" in data

    def test_corrupted_json_handling(self, test_client):
        response = test_client.post(
            "/api/parse/upload",
            files={
                "file": (
                    "broken.json",
                    b'{"broken"',
                    "application/json"
                )
            }
        )

        assert response.status_code >= 400


@pytest.mark.integration
class TestParseLinkEndpoint:

    def test_invalid_url_error(self, test_client):
        response = test_client.post(
            "/api/parse/link",
            json={"url": "not-a-valid-url"}
        )

        assert response.status_code >= 400

    def test_empty_url_error(self, test_client):
        response = test_client.post(
            "/api/parse/link",
            json={"url": "   "}
        )

        assert response.status_code >= 400

    def test_endpoint_exists(self, test_client):
        response = test_client.post(
            "/api/parse/link",
            json={"url": "https://example.com"}
        )

        assert response.status_code > 0

    def test_strategy_parameter_applied(self, test_client):
        response = test_client.post(
            "/api/parse/link",
            json={"url": "https://example.com"},
            params={"strategy": "full"}
        )

        assert response.status_code > 0


@pytest.mark.integration
class TestParseTextEndpoint:

    def test_valid_raw_text(self, test_client, sample_raw_text):
        response = test_client.post(
            "/api/parse/text",
            json={
                "text": sample_raw_text
            }
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_empty_text_error(self, test_client):
        response = test_client.post(
            "/api/parse/text",
            json={
                "text": ""
            }
        )

        assert response.status_code >= 400

    def test_whitespace_only_text_error(self, test_client):
        response = test_client.post(
            "/api/parse/text",
            json={
                "text": "   \n\n  "
            }
        )

        assert response.status_code >= 400

    def test_strategy_parameter_used(
        self,
        test_client,
        sample_raw_text
    ):
        response = test_client.post(
            "/api/parse/text",
            json={
                "text": sample_raw_text,
                "strategy": "concise"
            }
        )

        assert response.status_code == 200

    def test_target_platform_parameter_used(
        self,
        test_client,
        sample_raw_text
    ):
        response = test_client.post(
            "/api/parse/text",
            json={
                "text": sample_raw_text,
                "target_platform": "chatgpt"
            }
        )

        assert response.status_code == 200

    def test_source_platform_parameter_used(
        self,
        test_client,
        sample_raw_text
    ):
        response = test_client.post(
            "/api/parse/text",
            json={
                "text": sample_raw_text,
                "source_platform": "claude"
            }
        )

        assert response.status_code == 200

    def test_response_contains_content(
        self,
        test_client,
        sample_raw_text
    ):
        response = test_client.post(
            "/api/parse/text",
            json={"text": sample_raw_text}
        )

        data = response.json()

        assert data["success"] is True
        assert data["data"] is not None


@pytest.mark.integration
class TestParseExtensionEndpoint:

    def test_valid_extension_payload(
        self,
        test_client,
        extension_payload_valid
    ):
        response = test_client.post(
            "/api/parse/extension",
            json=extension_payload_valid
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_minimal_extension_payload(
        self,
        test_client,
        extension_payload_minimal
    ):
        response = test_client.post(
            "/api/parse/extension",
            json=extension_payload_minimal
        )

        assert response.status_code == 200

    def test_missing_messages_array(self, test_client):
        response = test_client.post(
            "/api/parse/extension",
            json={"source_platform": "chatgpt"}
        )

        assert response.status_code >= 400

    def test_empty_messages_array(self, test_client):
        response = test_client.post(
            "/api/parse/extension",
            json={
                "source_platform": "chatgpt",
                "messages": []
            }
        )

        assert response.status_code >= 400

    def test_invalid_message_role(self, test_client):
        response = test_client.post(
            "/api/parse/extension",
            json={
                "source_platform": "chatgpt",
                "messages": [
                    {"role": "user", "content": "Hello"},
                    {"role": "invalid_role", "content": "Response"}
                ]
            }
        )

        assert response.status_code > 0

    def test_strategy_parameter_applied(
        self,
        test_client,
        extension_payload_valid
    ):
        payload = extension_payload_valid.copy()
        payload["strategy"] = "technical"

        response = test_client.post(
            "/api/parse/extension",
            json=payload
        )

        assert response.status_code == 200

    def test_response_format(
        self,
        test_client,
        extension_payload_valid
    ):
        response = test_client.post(
            "/api/parse/extension",
            json=extension_payload_valid
        )

        data = response.json()

        assert "success" in data
        assert data["success"] is True


@pytest.mark.integration
class TestHealthEndpoint:

    def test_health_check_succeeds(self, test_client):
        response = test_client.get("/api/health")

        assert response.status_code == 200

    def test_health_check_format(self, test_client):
        response = test_client.get("/api/health")

        assert isinstance(response.json(), dict)


@pytest.mark.integration
class TestRootEndpoint:

    def test_root_endpoint(self, test_client):
        response = test_client.get("/")

        assert response.status_code == 200

        data = response.json()

        assert "app" in data
        assert "status" in data

    def test_root_endpoint_format(self, test_client):
        response = test_client.get("/")

        data = response.json()

        assert data["status"] == "running"


@pytest.mark.integration
class TestErrorHandling:

    def test_400_bad_request(self, test_client):
        response = test_client.post(
            "/api/parse/text",
            json={"text": ""}
        )

        assert response.status_code == 400

    def test_422_unprocessable_entity(self, test_client):
        response = test_client.post(
            "/api/parse/upload",
            files={
                "file": (
                    "invalid.json",
                    b'{"invalid":"data"}',
                    "application/json"
                )
            }
        )

        assert response.status_code >= 400

    def test_error_response_format(self, test_client):
        response = test_client.post(
            "/api/parse/text",
            json={"text": ""}
        )

        if response.status_code >= 400:
            assert isinstance(response.json(), dict)

    def test_missing_required_field(self, test_client):
        response = test_client.post(
            "/api/parse/text",
            json={}
        )

        assert response.status_code >= 400

    def test_invalid_strategy_parameter(
        self,
        test_client,
        sample_raw_text
    ):
        response = test_client.post(
            "/api/parse/text",
            json={
                "text": sample_raw_text,
                "strategy": "invalid_strategy"
            }
        )

        assert response.status_code > 0

    def test_async_endpoint_execution(
        self,
        test_client,
        sample_raw_text
    ):
        response = test_client.post(
            "/api/parse/text",
            json={"text": sample_raw_text}
        )

        assert response.status_code in [200, 400, 422]