import functools
import asyncio
from typing import Callable, Any
from System.neuroanatomy.autonomic.interoception import log_metabolism


def motor_neuron(energy_cost: int = 15):
    """
    PERIPHERAL NERVOUS SYSTEM
    Wraps standard Python tools into biological motor pathways.
    Every time this tool is used, the OS 'feels' the physical exertion.
    """

    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                # 1. The OS feels the exertion before taking action
                log_metabolism(energy_cost)
                # 2. Execute the physical movement (the tool)
                return await func(*args, **kwargs)

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                # 1. The OS feels the exertion before taking action
                log_metabolism(energy_cost)
                # 2. Execute the physical movement (the tool)
                return func(*args, **kwargs)

            return sync_wrapper

    return decorator
