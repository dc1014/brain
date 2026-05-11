from System.organs.broca import enforce_data_contract
from unittest.mock import MagicMock


def test_broca_perfect_articulation():
    response = "Here are my thoughts.\n<execute>\nrun_tests\n</execute>"
    is_valid, content = enforce_data_contract(response, "execute")
    assert is_valid is True
    assert content == "run_tests"


def test_broca_auto_heals_missing_close_tag():
    response = "<execute>\nbuild_app"  # Token limit cut off the end
    is_valid, content = enforce_data_contract(response, "execute")
    assert is_valid is True
    assert content == "build_app"


def test_broca_auto_heals_markdown_bleeding():
    response = "<execute>\n```bash\nnpm run dev\n```\n</execute>"
    is_valid, content = enforce_data_contract(response, "execute")
    assert is_valid is True
    assert content == "npm run dev"


def test_broca_catches_missing_tag():
    response = "I forgot to use the execution tags entirely."
    is_valid, content = enforce_data_contract(response, "execute")
    assert is_valid is False
    assert "BROCA ERROR" in content


def test_synthesize_speech(mocker, tmp_path):
    from System.organs.broca import synthesize_speech

    out_path = tmp_path / "out.mp3"

    # FIX: Patch litellm directly
    mock_speech = mocker.patch("litellm.speech")
    mock_response = MagicMock()
    mock_speech.return_value = mock_response

    result = synthesize_speech("Hello, world.", str(out_path))

    assert str(out_path) in result
    mock_response.stream_to_file.assert_called_once_with(str(out_path))
