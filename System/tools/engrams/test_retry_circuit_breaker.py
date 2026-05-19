import time
import threading  # For thread safety in CircuitBreaker

EXOCORTEX_MANIFEST = {
    "name": "test_retry_circuit_breaker",
    "description": "Simulates and tests a retry circuit breaker pattern with states: CLOSED, OPEN, HALF_OPEN.",
    "version": "1.0.0",
    "author": "Brain_OS",
    "tags": ["circuit_breaker", "retry", "resilience", "testing"],
}

# --- Circuit Breaker States ---
CLOSED = "CLOSED"
OPEN = "OPEN"
HALF_OPEN = "HALF_OPEN"


# --- Custom Exceptions ---
class CircuitBreakerException(Exception):
    """Base exception for Circuit Breaker."""

    pass


class CircuitBreakerOpenException(CircuitBreakerException):
    """Exception raised when the circuit is open and blocks a call."""

    pass


# --- Circuit Breaker Class ---
class CircuitBreaker:
    def __init__(
        self, failure_threshold=3, reset_timeout=5, retry_attempts=2, retry_delay=0.1
    ):
        """
        Initializes the CircuitBreaker.

        Args:
            failure_threshold (int): Number of consecutive failures to open the circuit.
            reset_timeout (int): Time (in seconds) the circuit stays open before going half-open.
            retry_attempts (int): Max retries for a single call when the circuit is closed.
            retry_delay (float): Delay (in seconds) between retries.
        """
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay

        self.current_state = CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.lock = threading.Lock()  # Ensures thread safety for state changes

    def _open_circuit(self):
        """Transitions the circuit to the OPEN state."""
        self.current_state = OPEN
        self.last_failure_time = time.time()
        print(
            f"Circuit Breaker: Circuit opened at {self.last_failure_time:.2f}. Too many failures."
        )

    def _close_circuit(self):
        """Transitions the circuit to the CLOSED state."""
        self.current_state = CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        print("Circuit Breaker: Circuit closed. Service is healthy again.")

    def _half_open_circuit(self):
        """Transitions the circuit to the HALF_OPEN state."""
        self.current_state = HALF_OPEN
        print("Circuit Breaker: Circuit half-open. Allowing one test call.")

    def call(self, func, *args, **kwargs):
        """
        Executes the given function through the circuit breaker.

        Args:
            func (callable): The function to execute.
            *args: Positional arguments for func.
            **kwargs: Keyword arguments for func.

        Returns:
            Any: The result of the executed function.

        Raises:
            CircuitBreakerOpenException: If the circuit is open and blocks the call,
                                         or if a half-open test call fails and re-opens the circuit.
            CircuitBreakerException: If all retries fail when the circuit is closed.
            Exception: Any other exception raised by the wrapped function.
        """
        with self.lock:
            if self.current_state == OPEN:
                if time.time() - self.last_failure_time > self.reset_timeout:
                    self._half_open_circuit()
                else:
                    print(
                        f"Circuit Breaker: Circuit is OPEN. Blocking call to {func.__name__}."
                    )
                    raise CircuitBreakerOpenException("Circuit is open")

            # Determine max attempts based on current state
            # HALF_OPEN state only allows one attempt (the test call)
            # CLOSED state allows initial attempt + retry_attempts
            max_attempts = (
                1 if self.current_state == HALF_OPEN else (self.retry_attempts + 1)
            )

            for attempt in range(max_attempts):
                try:
                    result = func(*args, **kwargs)
                    # If successful
                    if self.current_state == HALF_OPEN:
                        self._close_circuit()  # Test call succeeded, close circuit
                    elif self.current_state == CLOSED:
                        self.failure_count = 0  # Reset failure count on success
                    return result
                except Exception as e:
                    print(
                        f"Circuit Breaker: Call to {func.__name__} failed (attempt {attempt + 1}/{max_attempts}): {e}"
                    )

                    if self.current_state == HALF_OPEN:
                        # Half-open test call failed, re-open the circuit
                        self._open_circuit()
                        raise CircuitBreakerOpenException(
                            "Circuit re-opened after half-open test failure"
                        ) from e

                    # Only increment failure count and check threshold if in CLOSED state
                    if self.current_state == CLOSED:
                        self.failure_count += 1
                        if self.failure_count >= self.failure_threshold:
                            self._open_circuit()
                            raise CircuitBreakerOpenException(
                                "Circuit opened due to consecutive failures"
                            ) from e

                    # If more retries are allowed in CLOSED state, wait and try again
                    if attempt < max_attempts - 1:
                        time.sleep(self.retry_delay)
                    else:
                        # All attempts failed (either retries exhausted in CLOSED, or single half-open attempt failed)
                        raise CircuitBreakerException(
                            f"All attempts failed for {func.__name__}"
                        ) from e


# --- Simulated Unreliable Service ---
_service_call_counter = (
    0  # This counter tracks actual attempts to the underlying service
)


def _unreliable_service_call(call_id, force_fail=False):
    """
    A simulated service call that can be forced to fail.
    It also increments a global counter for every actual attempt.

    Args:
        call_id (str): An identifier for the current call.
        force_fail (bool): If True, the call will fail.

    Returns:
        str: A success message.

    Raises:
        ValueError: If the simulated call fails.
    """
    global _service_call_counter
    _service_call_counter += 1
    print(f"  Service Call {call_id}: Attempting call #{_service_call_counter}...")
    if force_fail:
        print(f"  Service Call {call_id}: Call #{_service_call_counter} FORCED FAILED.")
        raise ValueError(f"Simulated service failure for call #{_service_call_counter}")
    print(f"  Service Call {call_id}: Call #{_service_call_counter} SUCCEEDED.")
    return f"Success from call {call_id} (service call #{_service_call_counter})"


# --- Main Execution Function ---
def execute_reflex():
    """
    Demonstrates the functionality of the Circuit Breaker pattern.
    """
    print("--- Starting Circuit Breaker Test ---")

    # Initialize circuit breaker with specific parameters for demonstration
    # Failure threshold: 3 consecutive failures to open the circuit
    # Reset timeout: 5 seconds before the circuit transitions from OPEN to HALF_OPEN
    # Retry attempts: 2 retries (meaning a total of 3 attempts for a single logical call)
    # Retry delay: 0.1 seconds between retries
    cb = CircuitBreaker(
        failure_threshold=3, reset_timeout=5, retry_attempts=2, retry_delay=0.1
    )

    print("\n--- Phase 1: Demonstrate failures, retries, and circuit opening ---")
    # We need 3 consecutive logical calls to fail to open the circuit (failure_threshold=3).
    # With 2 retries, each logical cb.call makes 3 attempts if the underlying service keeps failing.
    # So, if we force _unreliable_service_call to fail for 3 consecutive cb.calls:
    # cb.call 1: fails 3 times -> failure_count = 1
    # cb.call 2: fails 3 times -> failure_count = 2
    # cb.call 3: fails 3 times -> failure_count = 3 -> CIRCUIT OPENS
    # Subsequent calls will be blocked immediately.
    for i in range(1, 5):  # Iterate enough times to open the circuit and then block
        print(f"\nMain Loop Iteration {i}: Current Circuit state: {cb.current_state}")
        try:
            # Force failure for the first 3 logical calls to open the circuit
            should_fail = i <= 3
            result = cb.call(
                _unreliable_service_call, f"main_loop_{i}", force_fail=should_fail
            )
            print(f"Main Loop Iteration {i}: Result: {result}")
        except CircuitBreakerOpenException as e:
            print(f"Main Loop Iteration {i}: Caught CircuitBreakerOpenException: {e}")
        except CircuitBreakerException as e:
            print(
                f"Main Loop Iteration {i}: Caught CircuitBreakerException (all retries failed): {e}"
            )
        except Exception as e:
            print(f"Main Loop Iteration {i}: Caught unexpected exception: {e}")
        time.sleep(0.2)  # Small delay between main loop iterations for readability

    print(
        "\n--- Phase 2: Wait for reset timeout and demonstrate HALF_OPEN state (success) ---"
    )
    print(
        f"Circuit is currently {cb.current_state}. Waiting for {cb.reset_timeout} seconds for it to go HALF_OPEN..."
    )
    time.sleep(cb.reset_timeout + 1)  # Wait a bit longer than reset_timeout

    print(
        f"\nMain Loop Iteration (after wait): Current Circuit state: {cb.current_state}"
    )
    try:
        # This call should trigger HALF_OPEN, and we'll make it succeed to close the circuit
        result = cb.call(
            _unreliable_service_call, "half_open_test_success", force_fail=False
        )
        print(f"Main Loop Iteration (after wait): Result: {result}")
    except CircuitBreakerOpenException as e:
        print(
            f"Main Loop Iteration (after wait): Caught CircuitBreakerOpenException: {e}"
        )
    except CircuitBreakerException as e:
        print(
            f"Main Loop Iteration (after wait): Caught CircuitBreakerException (all attempts failed): {e}"
        )
    except Exception as e:
        print(f"Main Loop Iteration (after wait): Caught unexpected exception: {e}")

    print(f"\nFinal Circuit state after successful half-open test: {cb.current_state}")

    print("\n--- Phase 3: Demonstrate HALF_OPEN state (failure) and re-opening ---")
    # Manually force the circuit to OPEN and set last_failure_time to trigger HALF_OPEN on next call
    cb._open_circuit()
    cb.last_failure_time = (
        time.time() - cb.reset_timeout - 1
    )  # Force half-open on next call
    print(
        f"Manually forced circuit to OPEN, then simulated waiting for reset. Current Circuit state: {cb.current_state}"
    )

    try:
        # This call should trigger HALF_OPEN, and we'll make it fail to re-open the circuit
        result = cb.call(
            _unreliable_service_call, "half_open_test_failure", force_fail=True
        )
        print(f"Main Loop Iteration (half-open fail): Result: {result}")
    except CircuitBreakerOpenException as e:
        print(
            f"Main Loop Iteration (half-open fail): Caught CircuitBreakerOpenException: {e}"
        )
    except CircuitBreakerException as e:
        print(
            f"Main Loop Iteration (half-open fail): Caught CircuitBreakerException (all attempts failed): {e}"
        )
    except Exception as e:
        print(f"Main Loop Iteration (half-open fail): Caught unexpected exception: {e}")

    print(f"\nFinal Circuit state after failed half-open test: {cb.current_state}")
    print("--- Circuit Breaker Test Finished ---")
