from unittest.mock import patch
from System.neuroanatomy.peripheral.motor import motor_neuron
import asyncio
import pytest


# 1. Create dummy tools to test the decorator natively
@motor_neuron(energy_cost=50)
def dummy_sync_tool(x: int) -> int:
    return x * 2


@motor_neuron(energy_cost=100)
async def dummy_async_tool(x: int) -> int:
    await asyncio.sleep(0.01)
    return x * 2


@patch("System.neuroanatomy.peripheral.motor.log_metabolism")
def test_motor_neuron_sync_interception(mock_log):
    """Proves the motor neuron intercepts sync functions and logs metabolism."""
    result = dummy_sync_tool(5)

    # Validation
    assert result == 10
    mock_log.assert_called_once_with(50)


@pytest.mark.asyncio
@patch("System.neuroanatomy.peripheral.motor.log_metabolism")
async def test_motor_neuron_async_interception(mock_log):
    """Proves the motor neuron cleanly wraps async functions without breaking the event loop."""
    result = await dummy_async_tool(5)

    # Validation
    assert result == 10
    mock_log.assert_called_once_with(100)
