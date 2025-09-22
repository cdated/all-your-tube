"""
Test UI rendering without actual downloads.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_workdir = Path(temp_dir)
        with patch.dict(os.environ, {"AYT_WORKDIR": str(test_workdir)}):
            # Import app AFTER setting environment variable
            # pylint: disable=import-outside-toplevel
            from all_your_tube.app import app

            app.config["TESTING"] = True
            with app.test_client() as test_client:
                yield test_client


def test_index_page_renders(client):
    """Test that the main download form page renders correctly."""
    response = client.get("/yourtube/")
    assert response.status_code == 200
    assert b"<title>All Your Tube" in response.data


def test_index_page_contains_form(client):
    """Test that the index page contains the expected form elements."""
    response = client.get("/yourtube/")
    assert response.status_code == 200

    # Check for form elements
    assert b'form id="downloadForm"' in response.data
    assert b'<label for="url"' in response.data
    assert b'<label for="directory"' in response.data


def test_save_endpoint_requires_post(client):
    """Test that the save endpoint only accepts POST requests."""
    response = client.get("/yourtube/save")
    assert response.status_code == 405  # Method Not Allowed


@patch("all_your_tube.app.subprocess.Popen")
def test_save_endpoint_with_valid_data_ajax(mock_popen, client):
    """Test save endpoint with valid form data via AJAX (returns JSON)."""
    # Mock the subprocess
    mock_process = mock_popen.return_value
    mock_process.pid = 12345

    response = client.post(
        "/yourtube/save",
        data={"url": "https://example.com/video", "directory": "test_dir"},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    # Should return JSON response with success and pid
    assert response.status_code == 200
    assert response.content_type == "application/json"
    json_data = response.get_json()
    assert json_data["success"] is True
    assert "pid" in json_data
    # ULID should be 26 characters long
    assert len(json_data["pid"]) == 26
    assert "stream_url" in json_data


def test_static_files_served(client):
    """Test that static files are served correctly."""
    # This assumes there's at least one CSS file in static/
    response = client.get("/yourtube/static/css/main.css")
    assert response.status_code == 200
    response = client.get("/yourtube/static/js/main.js")
    assert response.status_code == 200
    response = client.get("/yourtube/static/fake_test.css")
    assert response.status_code == 404


@patch("all_your_tube.app.subprocess.Popen")
def test_save_creates_workdir_subdirectory(mock_popen, client):
    """Test that save endpoint calls popen with the subdir"""
    mock_process = mock_popen.return_value
    mock_process.pid = 12345

    client.post(
        "/yourtube/save",
        data={"url": "https://example.com/video", "directory": "subdir/nested"},
    )

    # Check that subprocess was called with correct working directory
    mock_popen.assert_called_once()
    call_args = mock_popen.call_args
    assert "cwd" in call_args.kwargs
    assert "subdir/nested" in str(call_args.kwargs["cwd"])
