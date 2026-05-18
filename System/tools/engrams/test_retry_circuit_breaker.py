import time

EXOCORTEX_MANIFEST = {
    "name": "test_retry_circuit_breaker",
    "description": "Simulates a retry circuit breaker pattern to test resilience. The simulated task fails deterministically for a set number of initial attempts before succeeding or opening the circuit.",
    "version": "1.0.0",
    "author": "Brain_OS",
    "tags": ["testing", "resilience", "circuit_breaker", "retry"],
}

# Global counter for simulating failures in the unreliable_task
# This makes the task's behavior deterministic for testing purposes.
_unreliable_task_call_count = 0
# Configure how many times the unreliable_task should fail before succeeding.
# E.g., if set to 2, the first two calls will fail, the third and subsequent will succeed.
_unreliable_task_fail_until_count = 2


def unreliable_task():
    """
    Simulates a task that might fail.
    It fails for the first `_unreliable_task_fail_until_count` calls, then succeeds.
    """
    global _unreliable_task_call_count
    _unreliable_task_call_count += 1
    print(f"  Attempting task (internal call count: {_unreliable_task_call_count})...")

    if _unreliable_task_call_count <= _unreliable_task_fail_until_count:
        print("  Task FAILED (simulated)!")
        raise RuntimeError("Simulated service failure")
    else:
        print("  Task SUCCEEDED (simulated)!")
        return "Success!"


def execute_reflex():
    """
    Implements a retry circuit breaker pattern to test resilience.
    It attempts to execute a potentially unreliable task, retrying on failure
    up to a maximum number of retries, and opening a circuit if consecutive
    failures exceed a defined threshold.
    """
    print("Initiating retry circuit breaker test...")

    max_retries = 5
    # The number of consecutive failures after which the circuit "opens"
    # and no further attempts are made.
    failure_threshold = 3
    retry_delay_seconds = 1

    consecutive_failures = 0
    attempts = 0
    task_successful = False
    circuit_opened = False

    print(
        f"Configuration: max_retries={max_retries}, failure_threshold={failure_threshold}, retry_delay_seconds={retry_delay_seconds}s"
    )
    print(
        f"Simulated task will fail for the first {_unreliable_task_fail_until_count} attempts, then succeed."
    )

    while attempts < max_retries and not task_successful and not circuit_opened:
        attempts += 1
        print(f"\nAttempt {attempts}/{max_retries}:")

        # Check if the circuit is already open before making an attempt
        if consecutive_failures >= failure_threshold:
            print(
                f"Circuit OPENED: {consecutive_failures} consecutive failures reached. Stopping further attempts."
            )
            circuit_opened = True
            break  # Exit the loop as circuit is open

        try:
            result = unreliable_task()
            print(f"Task completed successfully: {result}")
            task_successful = True
            consecutive_failures = 0  # Reset consecutive failures on success
        except RuntimeError as e:
            print(f"Task failed: {e}")
            consecutive_failures += 1

            if consecutive_failures >= failure_threshold:
                print(
                    f"Circuit OPENED: {consecutive_failures} consecutive failures reached. Stopping further attempts."
                )
                circuit_opened = True
            elif attempts < max_retries:
                print(
                    f"Retrying in {retry_delay_seconds} second(s)... (Consecutive failures: {consecutive_failures})"
                )
                time.sleep(retry_delay_seconds)
            else:
                print("Max retries reached. Task ultimately failed.")

    print("\n--- Circuit Breaker Test Summary ---")
    if task_successful:
        print("Result: Task ultimately succeeded.")
    elif circuit_opened:
        print(
            "Result: Circuit opened due to excessive consecutive failures. Task ultimately failed."
        )
    else:
        print(
            "Result: Max retries reached without success and circuit did not open. Task ultimately failed."
        )

    print("------------------------------------")


if __name__ == "__main__":
    execute_reflex()
