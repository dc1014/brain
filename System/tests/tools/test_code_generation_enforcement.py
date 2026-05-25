# --- System/tests/tools/test_code_generation_enforcement.py ---
import pytest
from System.tools.sandbox import execute_in_sandbox


class FakeStdin:
    def write(self, data):
        pass

    def close(self):
        pass

    async def drain(self):
        pass

    async def wait_closed(self):
        pass


def create_fake_process(chunks, returncode=0):
    class FakeStdout:
        def __init__(self):
            self.items = list(chunks)

        def at_eof(self):
            return not self.items

        async def read(self, *args, **kwargs):
            return self.items.pop(0) if self.items else b""

        async def readline(self, *args, **kwargs):
            return self.items.pop(0) if self.items else b""

    class FakeProcess:
        def __init__(self):
            self.returncode = returncode
            self.stdout = FakeStdout()
            self.stdin = FakeStdin()

        def kill(self):
            pass

        async def wait(self):
            return returncode

    return FakeProcess()


@pytest.mark.asyncio
async def test_code_generation_route_mandates_container_execution(
    tmp_path, monkeypatch, mocker
):
    monkeypatch.setenv("CORETEX_ENABLE_CODE_EXECUTION", "true")
    safe_workspace = tmp_path / "Studio" / "AppDevelopmentWorkspace"
    safe_workspace.mkdir(parents=True)

    chunks = [b"[__EXECUTION_COMPLETE__]\n"]

    async def mock_worker(*args, **kwargs):
        return create_fake_process(chunks)

    mocker.patch("System.tools.sandbox.get_pre_warmed_worker", side_effect=mock_worker)
    mocker.patch("asyncio.create_subprocess_exec", side_effect=mock_worker)

    res = await execute_in_sandbox(
        command="python script.py",
        workspace_path=safe_workspace,
        env_secrets={},
        route="CODE_GENERATION",
    )
    assert res.success is True


@pytest.mark.asyncio
async def test_container_blocks_system_core_pollution(tmp_path, monkeypatch):
    monkeypatch.setenv("CORETEX_ENABLE_CODE_EXECUTION", "true")
    unsafe_workspace = tmp_path / "System" / "core"
    unsafe_workspace.mkdir(parents=True)

    res = await execute_in_sandbox(
        "rm -rf *", workspace_path=unsafe_workspace, env_secrets={}, route="SWARM"
    )
    assert res.success is False
    assert "CRITICAL SECURITY TERMINATION" in str(res.block_reason)
