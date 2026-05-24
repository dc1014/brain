import pytest
from pathlib import Path


def test_watch_daemon_normalizes_typer_option_regression(
    mocker, tmp_path: Path
) -> None:
    """Proves the somatosensory watch daemon handles non-integer OptionInfo objects

    gracefully when invoked programmatically by background daemon threads.
    """
    from System.cli_somatic import watch

    # Bind the file scanner to an empty temporary path
    mocker.patch("System.cli_somatic.ROOT_DIR", tmp_path)

    # Patch MirrorNeurons to prevent destructive background disk writes during tests
    mocker.patch("System.cli_somatic.MirrorNeurons")

    # Interrupt the infinite loop on the very first iteration using a time.sleep side effect
    mocker.patch(
        "System.cli_somatic.time.sleep",
        side_effect=KeyboardInterrupt("Refractory Guard Passed"),
    )

    # Simulate the exact type-mismatched descriptor object injected by Typer/Medulla threads
    mock_option_info = mocker.MagicMock()

    # Execute the daemon loop tracking track
    with pytest.raises(KeyboardInterrupt, match="Refractory Guard Passed"):
        watch(max_loops=mock_option_info)

    # If the execution reached time.sleep and raised the KeyboardInterrupt, it proves
    # that the guard successfully normalized the state to None and avoided the TypeError!
