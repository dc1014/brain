# --- System/tests/cortical/test_mirror_neurons.py ---
import json
import os
from pathlib import Path
from typing import Any
from typer.testing import CliRunner
from System.neuroanatomy.cortical.mirror_neurons import MirrorNeurons
from System.cli import app

runner = CliRunner()


def test_mirror_neurons_observes_and_potentiates(tmp_path: Path) -> None:
    """Verifies that mirror neuron hooks cleanly capture tracks and run Hebbian potentiation logic."""
    mn = MirrorNeurons(observation_vault=str(tmp_path))

    steps = ["uv run ruff check .", "uv run mypy System/"]
    mn.observe_and_record("ForgeAgent", "Verify code health invariants", steps)

    target_log = tmp_path / "Meta" / "mirror_observations.jsonl"
    assert target_log.exists()

    with open(target_log, "r", encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["resonance_score"] == 1.0
    assert data["parameterized_chain"] == steps

    mn.observe_and_record("ForgeAgent", "Verify code health invariants", steps)
    with open(target_log, "r", encoding="utf-8") as f:
        potentiated_lines = f.readlines()
    assert len(potentiated_lines) == 1
    potentiated_data = json.loads(potentiated_lines[0])
    assert potentiated_data["resonance_score"] == 1.5


def test_mirror_neurons_synchronizes_cross_platform_paths(tmp_path: Path) -> None:
    """Confirms that cross-platform backslashes are normalized cleanly into agnostically matched paths."""
    mn = MirrorNeurons(observation_vault=str(tmp_path))

    steps = ["System\\tools\\epistemic.py", "System\\cli.py"]
    mn.observe_and_record("SwarmAgent", "Process Windows Target Loop", steps)

    matched_track = mn.synchronize_muscle_memory("Process Windows Target Loop")
    assert matched_track == ["System/tools/epistemic.py", "System/cli.py"]


def test_mirror_neurons_token_based_stylistic_imitation_profiling(
    tmp_path: Path,
) -> None:
    """Tests zero-token python token stream style extraction and prompt generation inject context routines."""
    mn = MirrorNeurons(observation_vault=str(tmp_path))

    code_stub = (
        'def testFuncCamel():\t\n\t"""Mandatory Docstring Signature"""\n\treturn True'
    )
    mn.analyze_and_mirror_style(code_stub, mode="code")

    assert mn.style_path.exists()
    prompt_block = mn.inject_stylistic_prompt_context()

    assert "camelCase" in prompt_block
    assert "tabs" in prompt_block
    assert "True" in prompt_block


def test_mirror_neurons_malformed_syntax_resilience(tmp_path: Path) -> None:
    """Proves that unclosed string literals or broken indents are caught safely by lexer protection gates."""
    mn = MirrorNeurons(observation_vault=str(tmp_path))
    broken_code = 'def crash_loop():\n    unclosed_str = """Mismatched triple quote sequence markers'
    mn.analyze_and_mirror_style(broken_code, mode="code")
    assert mn.style_path.exists()


def test_mirror_neurons_markdown_ast_block_classification(tmp_path: Path) -> None:
    """Validates that prose cadences parse documents as structured blocks, filtering header noise completely."""
    mn = MirrorNeurons(observation_vault=str(tmp_path))

    markdown_payload = (
        "# Architectural Specification\n\n"
        "> [!info]\n"
        "> Implements unified cortical micro-AST processing tokens.\n\n"
        "  * Core point item layout execution step.\n"
        "  * Secondary structural block parameter configuration pass.\n"
        "This element contains a **bold text layout preference component** entry.\n"
        "This element contains an _italics preference format_ marker.\n!"
    )

    mn.analyze_and_mirror_style(markdown_payload, mode="prose")

    assert mn.style_path.exists()
    prompt_override = mn.inject_stylistic_prompt_context()

    assert "Bullet type '*'" in prompt_override
    assert "2-spaces" in prompt_override
    assert "asterisks" in prompt_override
    assert "underscores" in prompt_override
    assert "expressive" in prompt_override


def test_mirror_neurons_markdown_code_fence_isolation(tmp_path: Path) -> None:
    """Proves that text decoration symbols inside code fences are isolated and skipped entirely from prose metrics."""
    mn = MirrorNeurons(observation_vault=str(tmp_path))

    markdown_payload = (
        "# Code Block Leak Check\n\n"
        "- Standard prose line using dash bullets.\n\n"
        "```python\n"
        "# This block uses an asterisk or exclamation but should be skipped completely!\n"
        "* Nested element inside code sample\n"
        "```\n"
    )

    mn.analyze_and_mirror_style(markdown_payload, mode="prose")

    assert mn.style_path.exists()
    prompt_override = mn.inject_stylistic_prompt_context()

    assert "Bullet type '-'" in prompt_override
    assert "expressive" not in prompt_override


def test_mirror_neurons_markdown_blockquote_and_nested_italics(tmp_path: Path) -> None:
    """Verifies that blockquote prefixes are isolated, allowing the micro-AST parser to capture nested underscores and indicators."""
    mn = MirrorNeurons(observation_vault=str(tmp_path))

    markdown_payload = (
        "# Blockquote Testing Pass\n\n"
        "> This line sits inside a blockquote and contains a detailed _nested underscore italics format_ preferences check marker.\n"
    )
    mn.analyze_and_mirror_style(markdown_payload, mode="prose")

    assert mn.style_path.exists()
    prompt_override = mn.inject_stylistic_prompt_context()
    assert "underscores" in prompt_override


def test_mirror_neurons_allostatic_value_compression(tmp_path: Path) -> None:
    """Confirms that momentum parameters below the noise threshold are systematically compressed and purged to prevent value leakage."""
    mn = MirrorNeurons(observation_vault=str(tmp_path))
    mn.analyze_and_mirror_style("def baseline(): pass", mode="code")

    with open(mn.style_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["allostatic_momentum"]["indentation"]["aberrant-noise-key"] = 0.02

    with open(mn.style_path, "w", encoding="utf-8") as f:
        json.dump(data, f)

    mn.analyze_and_mirror_style("def baseline(): pass", mode="code")

    with open(mn.style_path, "r", encoding="utf-8") as f:
        compressed_data = json.load(f)

    assert (
        "aberrant-noise-key"
        not in compressed_data["allostatic_momentum"]["indentation"]
    )


def test_mirror_neurons_empathy_resonance_coefficient(tmp_path: Path) -> None:
    """Validates that empathy resonance score computations properly calculate compatibility weight boosts matching fingerprints."""
    mn = MirrorNeurons(observation_vault=str(tmp_path))
    mn.analyze_and_mirror_style("def first_func():\n    pass", mode="code")
    mn.analyze_and_mirror_style("def second_func():\n    pass", mode="code")

    matching_text = "def validated_script_node():\n    return True"
    resonance_score = mn.calculate_empathy_resonance(matching_text, mode="code")
    assert resonance_score == 0.5


def test_mirror_neurons_hash_cache_eviction_policy(tmp_path: Path) -> None:
    """Asserts that when the lookahead cache ledger spikes to capacity limits, it clears older elements via standard FIFO queues smoothly."""
    mn = MirrorNeurons(observation_vault=str(tmp_path))
    mn.analyze_and_mirror_style("def baseline(): pass", mode="code")

    for idx in range(2005):
        mn._resonance_cache[idx] = 0.25

    assert len(mn._resonance_cache) == 2005
    mn.calculate_empathy_resonance("def baseline(): pass", mode="code")
    assert len(mn._resonance_cache) <= 1506


def test_mirror_neurons_synaptic_neuroplasticity_bridge(tmp_path: Path) -> None:
    """Verifies that slow-wave consolidation accurately serializes a long-term engram node, and initializations bootstrap missing style cards from it."""
    mn = MirrorNeurons(observation_vault=str(tmp_path))

    studio_dir = tmp_path / "Studio"
    studio_dir.mkdir(parents=True, exist_ok=True)
    (studio_dir / "worker.py").write_text(
        "def rawCamelCase():\t\n\tpass", encoding="utf-8"
    )

    # Execute full consolidation to compile the independent long-term engram file
    mn.consolidate_stylistic_baseline()
    assert mn.engram_path.exists()

    # Remove the active stylistic fingerprint card file completely
    os.remove(mn.style_path)
    assert not mn.style_path.exists()

    # Initialize a clean mirror neurons class instance to engage automated onboarding bootstrap sequences
    new_mn = MirrorNeurons(observation_vault=str(tmp_path))
    assert new_mn.style_path.exists()

    prompt_override = new_mn.inject_stylistic_prompt_context()
    assert "camelCase" in prompt_override
    assert "tabs" in prompt_override


def test_mirror_neurons_style_drift_bounds_momentum(tmp_path: Path) -> None:
    """Validates allostatic momentum dampening prevents isolated aberrant scripts from corrupting global rules instantly."""
    mn = MirrorNeurons(observation_vault=str(tmp_path))

    baseline_code = "def worker_node():\n    pass"
    for _ in range(3):
        mn.analyze_and_mirror_style(baseline_code, mode="code")

    prompt_one = mn.inject_stylistic_prompt_context()
    assert "4-spaces" in prompt_one

    aberrant_code = "def customTabNode():\t\n\tpass"
    mn.analyze_and_mirror_style(aberrant_code, mode="code")

    prompt_two = mn.inject_stylistic_prompt_context()
    assert "4-spaces" in prompt_two
    assert "tabs" not in prompt_two

    for _ in range(3):
        mn.analyze_and_mirror_style(aberrant_code, mode="code")

    prompt_three = mn.inject_stylistic_prompt_context()
    assert "tabs" in prompt_three


def test_mirror_neurons_atomic_file_swap_safety(tmp_path: Path) -> None:
    """Proves that file updates occur out of atomic temporary buffer swaps, protecting profiles from partial-write errors."""
    mn = MirrorNeurons(observation_vault=str(tmp_path))
    mn.analyze_and_mirror_style("def test_atomic(): pass", mode="code")
    assert mn.style_path.exists()

    tmp_style = mn.style_path.with_suffix(".tmp")
    assert not tmp_style.exists()


def test_mirror_neurons_multi_file_style_sampling_consensus(tmp_path: Path) -> None:
    """Verifies that slow-wave consensus loops accurately compute plurality vector winners cross-sampling code blocks."""
    mn = MirrorNeurons(observation_vault=str(tmp_path))

    studio_dir = tmp_path / "Studio"
    studio_dir.mkdir(parents=True, exist_ok=True)

    (studio_dir / "a.py").write_text("def first_func():\n  pass", encoding="utf-8")
    (studio_dir / "b.py").write_text("def second_func():\n  pass", encoding="utf-8")
    (studio_dir / "c.py").write_text("def third_func():\t\n\tpass", encoding="utf-8")

    mn.consolidate_stylistic_baseline()

    assert mn.style_path.exists()
    prompt_override = mn.inject_stylistic_prompt_context()
    assert "2-spaces" in prompt_override
    assert "tabs" not in prompt_override


def test_mirror_neurons_dynamic_synaptic_alignment(tmp_path: Path) -> None:
    """Confirms that context location parameters execute on-the-fly layout overrides over standard baseline consensus structures."""
    mn = MirrorNeurons(observation_vault=str(tmp_path))

    global_payload = "def global_baseline():\n    pass"
    mn.analyze_and_mirror_style(global_payload, mode="code")

    specific_dir = tmp_path / "Studio" / "Microservice"
    specific_dir.mkdir(parents=True, exist_ok=True)
    local_script = specific_dir / "endpoint.py"
    local_script.write_text("def rawCamelCaseTarget(): pass", encoding="utf-8")

    prompt_override = mn.inject_stylistic_prompt_context(
        domain_or_path="Studio/Microservice"
    )
    assert "camelCase" in prompt_override


def test_mirror_neurons_transient_file_eviction_handling(
    tmp_path: Path, mocker
) -> None:
    """Validates that transient file unlinking events pop matching handles cleanly from memory maps during fast phasic sweeps."""
    mocker.patch("System.neuroanatomy.cortical.mirror_neurons.ROOT_DIR", tmp_path)
    mocker.patch("System.cli_somatic.ROOT_DIR", tmp_path)

    studio_dir = tmp_path / "Studio"
    studio_dir.mkdir(parents=True, exist_ok=True)
    code_file = studio_dir / "transient.py"
    code_file.write_text("def temp_loop(): pass", encoding="utf-8")

    runner.invoke(app, ["watch", "--max-loops", "1"])
    os.remove(code_file)

    result = runner.invoke(app, ["watch", "--max-loops", "1"])
    assert result.exit_code == 0


def test_mirror_neurons_allostatic_refractory_window(tmp_path: Path, mocker) -> None:
    """Confirms that the allostatic refractory window clusters successive micro-saves flawlessly before execution."""
    # ⚡ SCAFFOLDING FIX: Generate the mocked config directory within the sandbox path boundary
    (tmp_path / "System" / "config").mkdir(parents=True, exist_ok=True)
    # Seed a placeholder configuration fingerprint record so the module initialization exists natively
    (tmp_path / "System" / "config" / "stylistic_fingerprint.json").write_text(
        "{}", encoding="utf-8"
    )

    mocker.patch("System.neuroanatomy.cortical.mirror_neurons.ROOT_DIR", tmp_path)
    mocker.patch("System.cli_somatic.ROOT_DIR", tmp_path)

    # State vectors mapping out deterministic virtual time progression parameters
    # State vectors mapping out deterministic virtual time progression parameters
    time_values = [1000.0, 1001.0, 1002.0, 1050.0, 1060.0, 1070.0, 1080.0, 1090.0]
    time_idx_t = 0
    time_idx_m = 0

    # ⚡ FIXED: Decouple the two clocks so they don't consume each other's time arrays
    def mock_time_t() -> float:
        nonlocal time_idx_t
        val = time_values[min(time_idx_t, len(time_values) - 1)]
        time_idx_t += 1
        return val

    def mock_time_m() -> float:
        nonlocal time_idx_m
        val = time_values[min(time_idx_m, len(time_values) - 1)]
        time_idx_m += 1
        return val

    mocker.patch("time.time", side_effect=mock_time_t)
    mocker.patch("time.monotonic", side_effect=mock_time_m)
    mocker.patch("time.sleep")

    studio_dir = tmp_path / "Studio"
    studio_dir.mkdir(parents=True, exist_ok=True)
    code_file = studio_dir / "worker.py"
    code_file.write_text(
        'def camelCaseStateTwo():\t\n\t"""Docs"""\n\tpass', encoding="utf-8"
    )

    # Mirror a tracking map of filesystem mtime updates matching execution states natively
    stat_mtimes = [1000.0, 1001.0, 1002.0, 1002.0, 1002.0, 1002.0, 1002.0, 1002.0]
    stat_idx = 0

    class MockStatResult:
        def __init__(self, mtime: float) -> None:
            self.st_mode = 33188  # standard S_IFREG file identifier flag
            self.st_mtime = mtime

    orig_stat = Path.stat

    # 🔐 DESCRIPTOR PROPER BINDING: Intercept target nodes natively using real Python descriptors
    def mock_stat(self: Path, *args: Any, **kwargs: Any) -> Any:
        nonlocal stat_idx
        try:
            if isinstance(self, Path) and self.name == "worker.py":
                val = stat_mtimes[min(stat_idx, len(stat_mtimes) - 1)]
                stat_idx += 1
                return MockStatResult(val)
        except Exception:
            pass
        return orig_stat(self, *args, **kwargs)

    mocker.patch.object(Path, "stat", new=mock_stat)

    # ⚡ FIXED: Increase max-loops to 8 so the watcher has enough ticks to clear the window
    runner.invoke(app, ["watch", "--max-loops", "8"])

    mn = MirrorNeurons(observation_vault=str(tmp_path))
    assert mn.style_path.exists()

    prompt_override = mn.inject_stylistic_prompt_context()
    assert "camelCase" in prompt_override
    assert "tabs" in prompt_override


def test_mirror_neurons_typer_cli_pipeline(tmp_path: Path, mocker) -> None:
    """End-to-end functional test proving Typer app endpoints correctly invoke mirror neuron hooks."""
    (tmp_path / "System" / "config").mkdir(parents=True, exist_ok=True)
    (tmp_path / "System" / "config" / "stylistic_fingerprint.json").write_text(
        "{}", encoding="utf-8"
    )

    mocker.patch("System.neuroanatomy.cortical.mirror_neurons.ROOT_DIR", tmp_path)
    mocker.patch("System.cli_somatic.ROOT_DIR", tmp_path)

    # ⚡ FIXED: Typer's stream routing can silently swallow rich console output during Pytest runs.
    # We patch the console explicitly to verify the behavioral output regardless of internal pipe routing.
    mock_print = mocker.patch("System.cli_somatic.console.print")

    observe_result = runner.invoke(
        app,
        [
            "observe",
            "ForgeAgent",
            "Compile Workspace Assets",
            "uv run ruff check ., pytest System/",
        ],
        catch_exceptions=False,  # ⚡ Surface any hidden Typer exceptions
    )
    assert observe_result.exit_code == 0

    sync_mirror_result = runner.invoke(
        app, ["sync-mirror", "Compile Workspace Assets"], catch_exceptions=False
    )
    assert sync_mirror_result.exit_code == 0

    # Mathematically prove the console was commanded to print the success signal
    printed_strings = " ".join(
        [str(call.args[0]) for call in mock_print.call_args_list if call.args]
    )
    assert "Mirror Match Found!" in printed_strings

    sample_file = tmp_path / "sample.py"
    sample_file.write_text(
        'def modular_snake():\n  """Docs"""\n  pass', encoding="utf-8"
    )

    imitate_result = runner.invoke(
        app, ["imitate", str(sample_file), "--mode", "code"], catch_exceptions=False
    )
    assert imitate_result.exit_code == 0

    printed_strings_imitate = " ".join(
        [str(call.args[0]) for call in mock_print.call_args_list if call.args]
    )
    assert "Synaptic Style Card updated" in printed_strings_imitate
