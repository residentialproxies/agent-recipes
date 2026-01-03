"""Tests for circuit_breaker.py"""

import time
import pytest
from src.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    get_anthropic_breaker,
    get_github_breaker,
    reset_all_breakers,
)


class TestCircuitBreaker:
    def test_initial_state_is_closed(self):
        breaker = CircuitBreaker(failure_threshold=3, timeout=60)
        assert breaker.state == "closed"
        assert breaker.failure_count == 0
        assert not breaker.is_open

    def test_successful_call_does_not_change_state(self):
        breaker = CircuitBreaker(failure_threshold=3, timeout=60)
        result = breaker.call(lambda: "success")
        assert result == "success"
        assert breaker.state == "closed"
        assert breaker.failure_count == 0

    def test_opens_after_threshold_failures(self):
        breaker = CircuitBreaker(failure_threshold=3, timeout=60)
        
        def failing_func():
            raise ConnectionError("fail")
        
        # First two failures: still closed
        for _ in range(2):
            with pytest.raises(ConnectionError):
                breaker.call(failing_func)
        assert breaker.state == "closed"
        assert breaker.failure_count == 2
        
        # Third failure: opens circuit
        with pytest.raises(ConnectionError):
            breaker.call(failing_func)
        assert breaker.state == "open"
        assert breaker.is_open

    def test_open_rejects_calls_fast(self):
        breaker = CircuitBreaker(failure_threshold=2, timeout=60)
        
        def failing_func():
            raise ConnectionError("fail")
        
        # Trigger open
        with pytest.raises(ConnectionError):
            breaker.call(failing_func)
        with pytest.raises(ConnectionError):
            breaker.call(failing_func)
        assert breaker.state == "open"
        
        # Next call should fail fast with CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            breaker.call(lambda: "ok")

    def test_reset_closes_circuit(self):
        breaker = CircuitBreaker(failure_threshold=2, timeout=60)
        
        def failing_func():
            raise ConnectionError("fail")
        
        # Open the circuit
        with pytest.raises(ConnectionError):
            breaker.call(failing_func)
        with pytest.raises(ConnectionError):
            breaker.call(failing_func)
        assert breaker.state == "open"
        
        # Reset
        breaker.reset()
        assert breaker.state == "closed"
        assert breaker.failure_count == 0
        
        # Should work again
        result = breaker.call(lambda: "ok")
        assert result == "ok"

    def test_success_resets_failure_count(self):
        breaker = CircuitBreaker(failure_threshold=3, timeout=60)
        
        def failing_func():
            raise ConnectionError("fail")
        
        # 2 failures
        with pytest.raises(ConnectionError):
            breaker.call(failing_func)
        with pytest.raises(ConnectionError):
            breaker.call(failing_func)
        assert breaker.failure_count == 2
        
        # Success resets count
        breaker.call(lambda: "ok")
        assert breaker.failure_count == 0
        assert breaker.state == "closed"

    def test_only_counts_expected_exceptions(self):
        # Only count TimeoutError, ConnectionError, OSError
        breaker = CircuitBreaker(
            failure_threshold=2,
            timeout=60,
            expected_exceptions=(ConnectionError,),
        )
        
        def other_error():
            raise ValueError("not counted")
        
        # Other exceptions should not count toward threshold
        with pytest.raises(ValueError):
            breaker.call(other_error)
        assert breaker.failure_count == 0
        assert breaker.state == "closed"

    def test_half_open_allows_one_test_call(self):
        breaker = CircuitBreaker(failure_threshold=2, timeout=1)
        
        def failing_func():
            raise ConnectionError("fail")
        
        # Open the circuit
        with pytest.raises(ConnectionError):
            breaker.call(failing_func)
        with pytest.raises(ConnectionError):
            breaker.call(failing_func)
        assert breaker.state == "open"
        
        # Wait for timeout
        time.sleep(1.1)
        
        # Next call transitions to half-open
        result = breaker.call(lambda: "ok")
        assert result == "ok"
        # After success in half-open, should stay in half-open until threshold reached

    def test_half_open_failure_reopens(self):
        breaker = CircuitBreaker(failure_threshold=2, timeout=1, half_open_max_calls=1)
        
        def failing_func():
            raise ConnectionError("fail")
        
        # Open the circuit
        with pytest.raises(ConnectionError):
            breaker.call(failing_func)
        with pytest.raises(ConnectionError):
            breaker.call(failing_func)
        assert breaker.state == "open"
        
        # Wait for timeout
        time.sleep(1.1)
        
        # Failure in half-open reopens
        with pytest.raises(ConnectionError):
            breaker.call(failing_func)
        assert breaker.state == "open"

    def test_global_breakers_singleton(self):
        b1 = get_anthropic_breaker()
        b2 = get_anthropic_breaker()
        assert b1 is b2
        
        g1 = get_github_breaker()
        g2 = get_github_breaker()
        assert g1 is g2
        
        # Different instances
        assert b1 is not g1

    def test_reset_all_breakers(self):
        b1 = get_anthropic_breaker()
        g1 = get_github_breaker()
        
        # Manually open both
        b1._transition_to_open()
        g1._transition_to_open()
        
        assert b1.state == "open"
        assert g1.state == "open"
        
        reset_all_breakers()
        
        assert b1.state == "closed"
        assert g1.state == "closed"

    def test_repr(self):
        breaker = CircuitBreaker(name="test", failure_threshold=5, timeout=60)
        repr_str = repr(breaker)
        assert "test" in repr_str
        assert "closed" in repr_str
        assert "0/5" in repr_str
