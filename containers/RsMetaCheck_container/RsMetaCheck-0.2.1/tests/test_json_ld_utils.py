import json
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

import pytest

from metacheck.utils.json_ld_utils import fetch_latest_commit_id


def _mock_urlopen(payload: bytes) -> MagicMock:
    """Return a mock suitable for use as a urllib.request.urlopen context manager."""
    mock_response = MagicMock()
    mock_response.read.return_value = payload
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_response
    mock_cm.__exit__.return_value = False
    return mock_cm


class TestFetchLatestCommitIdEdgeCases:
    """Guard-clause inputs that must never trigger an HTTP request."""

    @pytest.mark.parametrize("url", ["", "Unknown", None])
    def test_returns_unknown_without_http_call(self, url):
        with patch(
            "metacheck.utils.json_ld_utils.urllib.request.urlopen"
        ) as mock_urlopen:
            result = fetch_latest_commit_id(url)
            assert result == "Unknown"
            mock_urlopen.assert_not_called()


class TestFetchLatestCommitIdGitHub:
    """GitHub URLs must return the 'sha' field from the GitHub REST API."""

    @patch("metacheck.utils.json_ld_utils.urllib.request.urlopen")
    def test_github_returns_sha(self, mock_urlopen):
        expected_sha = "bd7bbb5d08b6e08978cfcb449461bd23b32e17d9"
        payload = json.dumps({"sha": expected_sha}).encode()
        mock_urlopen.return_value = _mock_urlopen(payload)

        result = fetch_latest_commit_id(
            "https://github.com/SoftwareUnderstanding/sw-metadata-bot"
        )

        assert result == expected_sha

    @patch("metacheck.utils.json_ld_utils.urllib.request.urlopen")
    def test_github_http_error_returns_unknown(self, mock_urlopen):
        mock_urlopen.side_effect = HTTPError(
            url="https://api.github.com/repos/user/repo/commits/HEAD",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None,
        )

        result = fetch_latest_commit_id("https://github.com/user/nonexistent-repo")

        assert result == "Unknown"

    @patch("metacheck.utils.json_ld_utils.urllib.request.urlopen")
    def test_github_strips_git_suffix(self, mock_urlopen):
        expected_sha = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        payload = json.dumps({"sha": expected_sha}).encode()
        mock_urlopen.return_value = _mock_urlopen(payload)

        result = fetch_latest_commit_id("https://github.com/user/repo.git")

        assert result == expected_sha
        called_url = mock_urlopen.call_args[0][0].full_url
        assert "/repo.git" not in called_url


class TestFetchLatestCommitIdGitLab:
    """GitLab.com URLs must use the GitLab API v4 and return the 'id' field."""

    @patch("metacheck.utils.json_ld_utils.urllib.request.urlopen")
    def test_gitlab_com_returns_commit_id(self, mock_urlopen):
        expected_id = "9332e9b13882aa7e7f69dcafe7438ee100c5acba"
        payload = json.dumps([{"id": expected_id, "short_id": "9332e9b1"}]).encode()
        mock_urlopen.return_value = _mock_urlopen(payload)

        result = fetch_latest_commit_id(
            "https://gitlab.com/escape-ossr/rs_quality_checks"
        )

        assert result == expected_id

    @patch("metacheck.utils.json_ld_utils.urllib.request.urlopen")
    def test_gitlab_com_api_v4_endpoint_used(self, mock_urlopen):
        payload = json.dumps([{"id": "abc123", "short_id": "abc123"}]).encode()
        mock_urlopen.return_value = _mock_urlopen(payload)

        fetch_latest_commit_id("https://gitlab.com/escape-ossr/rs_quality_checks")

        called_url = mock_urlopen.call_args[0][0].full_url
        assert "api/v4/projects/escape-ossr%2Frs_quality_checks" in called_url

    @patch("metacheck.utils.json_ld_utils.urllib.request.urlopen")
    def test_gitlab_com_strips_trailing_slash(self, mock_urlopen):
        payload = json.dumps([{"id": "abc123"}]).encode()
        mock_urlopen.return_value = _mock_urlopen(payload)

        fetch_latest_commit_id("https://gitlab.com/escape-ossr/rs_quality_checks/")

        called_url = mock_urlopen.call_args[0][0].full_url
        assert "escape-ossr%2Frs_quality_checks" in called_url

    @patch("metacheck.utils.json_ld_utils.urllib.request.urlopen")
    def test_gitlab_com_strips_git_suffix(self, mock_urlopen):
        payload = json.dumps([{"id": "abc123"}]).encode()
        mock_urlopen.return_value = _mock_urlopen(payload)

        fetch_latest_commit_id("https://gitlab.com/escape-ossr/rs_quality_checks.git")

        called_url = mock_urlopen.call_args[0][0].full_url
        assert "rs_quality_checks.git" not in called_url

    @patch("metacheck.utils.json_ld_utils.urllib.request.urlopen")
    def test_gitlab_http_error_returns_unknown(self, mock_urlopen):
        mock_urlopen.side_effect = HTTPError(
            url="https://gitlab.com/api/v4/projects/...",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None,
        )

        result = fetch_latest_commit_id("https://gitlab.com/tofranco/private-repo")

        assert result == "Unknown"

    @patch("metacheck.utils.json_ld_utils.urllib.request.urlopen")
    def test_gitlab_url_error_returns_unknown(self, mock_urlopen):
        mock_urlopen.side_effect = URLError("Network unreachable")

        result = fetch_latest_commit_id(
            "https://gitlab.com/escape-ossr/rs_quality_checks"
        )

        assert result == "Unknown"

    def test_fetch_real_gitlab_com_repo(self):
        # This test makes a real HTTP request to GitLab.com, so it may be flaky.
        result = fetch_latest_commit_id(
            "https://gitlab.com/escape-ossr/rs_quality_checks"
        )
        assert isinstance(result, str)
        assert len(result) == 40  # Git commit hashes are 40 hex characters
