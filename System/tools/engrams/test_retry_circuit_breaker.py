import time

EXOCORTEX_MANIFEST = {
    "name": "test_retry_circuit_breaker",
    "description": "Simulates and tests a basic retry circuit breaker pattern, demonstrating its states (CLOSED, OPEN, HALF-OPEN) and transitions.",
    "version": "1.0.0",
    "author": "Brain_OS",
    "tags": ["circuit_breaker", "retry", "resilience", "testing"],
}


class CircuitBreaker:
    """
    A simple Circuit Breaker implementation to protect against repeated failures.
    States: CLOSED, OPEN, HALF_OPEN.
    """

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __init__(self, failure_threshold: int, reset_timeout: int):
        """
        Initializes the Circuit Breaker.

        Args:
            failure_threshold (int): Number of consecutive failures before tripping to OPEN state.
            reset_timeout (int): Time in seconds to wait before transitioning from OPEN to HALF_OPEN.
        """
        if not isinstance(failure_threshold, int) or failure_threshold <= 0:
            raise ValueError("failure_threshold must be a positive integer.")
        if not isinstance(reset_timeout, int) or reset_timeout <= 0:
            raise ValueError("reset_timeout must be a positive integer.")

        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time = None

    def _trip(self):
        """Transitions the circuit breaker to the OPEN state."""
        self.state = self.OPEN
        self.last_failure_time = time.time()
        print(f"  [CircuitBreaker] TRIPPED! State: {self.state}")

    def _reset(self):
        """Transitions the circuit breaker to the CLOSED state."""
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        print(f"  [CircuitBreaker] RESET. State: {self.state}")

    def _half_open(self):
        """Transitions the circuit breaker to the HALF_OPEN state."""
        self.state = self.HALF_OPEN
        print(f"  [CircuitBreaker] HALF-OPEN. State: {self.state}")

    def call(self, operation_func, *args, **kwargs):
        """
        Attempts to execute an operation through the circuit breaker.

        Args:
            operation_func (callable): The function to execute.
            *args, **kwargs: Arguments to pass to operation_func.

        Returns:
            tuple: (bool, any) - True if operation succeeded, False otherwise,
                   and the result or error message.
        """
        if self.state == self.OPEN:
            if time.time() - self.last_failure_time > self.reset_timeout:
                self._half_open()
            else:
                time_remaining = self.reset_timeout - (
                    time.time() - self.last_failure_time
                )
                print(
                    f"  [CircuitBreaker] is OPEN. Operation BLOCKED. (Time remaining: {time_remaining:.1f}s)"
                )
                return False, "Circuit Breaker is OPEN"

        try:
            result = operation_func(*args, **kwargs)
            if self.state == self.HALF_OPEN:
                self._reset()  # Successful call in HALF_OPEN resets the breaker
            elif self.state == self.CLOSED:
                self.failure_count = 0  # Reset failure count on success
            print(f"  [CircuitBreaker] Operation SUCCESS. State: {self.state}")
            return True, result
        except Exception as e:
            if self.state == self.HALF_OPEN:
                self._trip()  # Failure in HALF_OPEN trips it again
            elif self.state == self.CLOSED:
                self.failure_count += 1
                print(
                    f"  [CircuitBreaker] Operation FAILED. Failure count: {self.failure_count}/{self.failure_threshold}"
                )
                if self.failure_count >= self.failure_threshold:
                    self._trip()
            return False, str(e)


class FlakyOperation:
    """
    A simulated operation that fails a specified number of times before succeeding,
    and can be configured to force success for testing purposes.
    """

    def __init__(self, fail_count_before_success: int):
        """
        Initializes the flaky operation.

        Args:
            fail_count_before_success (int): Number of initial consecutive failures
                                             before the operation starts succeeding.
        """
        if (
            not isinstance(fail_count_before_success, int)
            or fail_count_before_success < 0
        ):
            raise ValueError(
                "fail_count_before_success must be a non-negative integer."
            )
        self._initial_fail_count = fail_count_before_success
        self._current_attempts = 0
        self._force_success = False

    def execute(self):
        """
        Executes the simulated operation.
        Raises ValueError if it's configured to fail, returns a success message otherwise.
        """
        self._current_attempts += 1
        print(
            f"  [FlakyOperation] Attempting operation (total attempt {self._current_attempts})..."
        )

        if self._force_success:
            self._force_success = False  # Reset for next call
            return "Operation forced to succeed!"

        if self._current_attempts <= self._initial_fail_count:
            raise ValueError(f"Simulated failure on attempt {self._current_attempts}")
        else:
            return f"Operation successful after {self._initial_fail_count} initial failures!"

    def reset_for_test(self, force_success_next_call: bool = False):
        """
        Resets the operation's internal state for testing.

        Args:
            force_success_next_call (bool): If True, the very next call to execute()
                                            will succeed regardless of fail_count.
        """
        self._current_attempts = 0
        self._force_success = force_success_next_call
        if force_success_next_call:
            print("  [FlakyOperation] Configured to succeed on next call.")
        else:
            print("  [FlakyOperation] Reset to initial failure pattern.")


def execute_reflex():
    """
    Main function to execute the circuit breaker test.
    """
    print("--- Starting Circuit Breaker Test ---")

    # Configuration for the circuit breaker and flaky operation
    FAILURE_THRESHOLD = 3
    RESET_TIMEOUT = 5  # seconds

    circuit_breaker = CircuitBreaker(FAILURE_THRESHOLD, RESET_TIMEOUT)
    flaky_op = FlakyOperation(fail_count_before_success=FAILURE_THRESHOLD)

    print(
        f"\nPhase 1: Triggering failures to trip the circuit breaker (threshold={FAILURE_THRESHOLD})..."
    )
    for i in range(
        FAILURE_THRESHOLD + 1
    ):  # Try one more time than needed to show it trips
        print(f"\n--- Call {i + 1} (State: {circuit_breaker.state}) ---")
        success, result = circuit_breaker.call(flaky_op.execute)
        if not success:
            print(f"  Call failed: {result}")
        else:
            print(f"  Call succeeded: {result}")
        time.sleep(0.5)  # Simulate some delay between calls

    print(
        "\nPhase 2: Circuit breaker should be OPEN. Subsequent calls should be blocked."
    )
    for i in range(2):
        print(f"\n--- Call {i + 1} (State: {circuit_breaker.state}) ---")
        success, result = circuit_breaker.call(flaky_op.execute)
        if not success:
            print(f"  Call failed: {result}")
        else:
            print(f"  Call succeeded: {result}")
        time.sleep(0.5)

    print(
        f"\nPhase 3: Waiting for reset timeout ({RESET_TIMEOUT}s) to allow HALF-OPEN state..."
    )
    time.sleep(RESET_TIMEOUT + 1)  # Wait a bit longer than the timeout

    print("\nPhase 4: Circuit breaker should be HALF-OPEN. Making a test call.")
    flaky_op.reset_for_test(
        force_success_next_call=True
    )  # Configure flaky op to succeed
    print(f"\n--- Call 1 (State: {circuit_breaker.state}) ---")
    success, result = circuit_breaker.call(flaky_op.execute)
    if not success:
        print(f"  Call failed: {result}")
    else:
        print(f"  Call succeeded: {result}")
    time.sleep(0.5)

    if circuit_breaker.state == CircuitBreaker.CLOSED:
        print(
            "\nPhase 5: Circuit breaker is now CLOSED. Operations should succeed normally (or fail and start counting again)."
        )
        flaky_op.reset_for_test(
            force_success_next_call=False
        )  # Reset flaky op to its initial failure pattern
        for i in range(3):
            print(f"\n--- Call {i + 1} (State: {circuit_breaker.state}) ---")
            success, result = circuit_breaker.call(flaky_op.execute)
            if not success:
                print(f"  Call failed: {result}")
            else:
                print(f"  Call succeeded: {result}")
            time.sleep(0.5)
    else:
        print(
            f"\nPhase 5: Circuit breaker did not close. Current state: {circuit_breaker.state}"
        )
        print(
            "This means the test call in HALF-OPEN failed, tripping the breaker again."
        )
        # Demonstrate that it's OPEN again and will block
        print(f"\n--- Call 2 (State: {circuit_breaker.state}) ---")
        success, result = circuit_breaker.call(flaky_op.execute)
        if not success:
            print(f"  Call failed: {result}")
        else:
            print(f"  Call succeeded: {result}")
        time.sleep(0.5)
        print(f"\nWaiting again for reset timeout ({RESET_TIMEOUT}s)...")
        time.sleep(RESET_TIMEOUT + 1)
        print(f"\n--- Call 3 (State: {circuit_breaker.state}) ---")
        flaky_op.reset_for_test(
            force_success_next_call=True
        )  # Ensure it succeeds this time
        success, result = circuit_breaker.call(flaky_op.execute)
        if not success:
            print(f"  Call failed: {result}")
        else:
            print(f"  Call succeeded: {result}")
        time.sleep(0.5)
        if circuit_breaker.state == CircuitBreaker.CLOSED:
            print("\nCircuit breaker is now CLOSED after second attempt in HALF-OPEN.")
        else:
            print(
                f"\nCircuit breaker remains {circuit_breaker.state}. Test completed with persistent failure."
            )

    print("\n--- Circuit Breaker Test Finished ---")


if __name__ == "__main__":
    execute_reflex()
