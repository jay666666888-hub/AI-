#!/usr/bin/env python3
"""
Retry Engine - 失败重试系统
指数退避 + 熔断器 + 备选策略
"""

import time
import random
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class RetryStrategy(Enum):
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIBONACCI = "fibonacci"


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class RetryConfig:
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout: float = 60.0


@dataclass
class RetryResult:
    success: bool
    attempts: int
    total_duration_ms: int
    last_error: str
    result: Any = None


@dataclass
class CircuitBreakerState:
    state: CircuitState = CircuitState.CLOSED
    failures: int = 0
    successes: int = 0
    last_failure_time: Optional[str] = None
    opened_at: Optional[str] = None


class CircuitBreakerOpenError(Exception):
    pass


class CircuitBreaker:
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError(f"Circuit {self.name} is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        if not self.state.opened_at:
            return True
        opened_time = datetime.fromisoformat(self.state.opened_at)
        elapsed = (datetime.now() - opened_time).total_seconds()
        return elapsed >= self.config.timeout

    def _on_success(self):
        if self.state.state == CircuitState.HALF_OPEN:
            self.state.successes += 1
            if self.state.successes >= self.config.success_threshold:
                self.state.state = CircuitState.CLOSED
                self.state.failures = 0
                self.state.successes = 0
                self.state.opened_at = None
        else:
            self.state.failures = 0

    def _on_failure(self):
        self.state.failures += 1
        self.state.last_failure_time = datetime.now().isoformat()

        if self.state.state == CircuitState.HALF_OPEN:
            self.state.state = CircuitState.OPEN
        elif self.state.failures >= self.config.failure_threshold:
            self.state.state = CircuitState.OPEN
            self.state.opened_at = datetime.now().isoformat()

    def get_status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.state.value,
            "failures": self.state.failures,
            "successes": self.state.successes,
            "opened_at": self.state.opened_at
        }


class RetryEngine:
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.stats: Dict[str, Dict[str, int]] = {}

    def get_circuit_breaker(self, name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name, config)
        return self.circuit_breakers[name]

    def retry(
        self,
        func: Callable,
        *args,
        config: RetryConfig = None,
        circuit_breaker: str = None,
        fallback: Callable = None,
        **kwargs
    ) -> RetryResult:
        config = config or RetryConfig()
        start_time = time.time()
        attempts = 0
        last_error = ""

        cb = None
        if circuit_breaker:
            cb = self.get_circuit_breaker(circuit_breaker)
            if cb.state.state == CircuitState.OPEN:
                if fallback:
                    return RetryResult(
                        success=True, attempts=0, total_duration_ms=0,
                        last_error="circuit_open_fallback", result=fallback()
                    )
                raise CircuitBreakerOpenError(f"Circuit {circuit_breaker} is OPEN")

        while attempts < config.max_attempts:
            attempts += 1
            try:
                if cb:
                    result = cb.call(func, *args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                duration_ms = int((time.time() - start_time) * 1000)
                self._record_attempt(circuit_breaker or "default", True, duration_ms)

                return RetryResult(
                    success=True, attempts=attempts, total_duration_ms=duration_ms,
                    last_error="", result=result
                )

            except Exception as e:
                last_error = str(e)
                duration_ms = int((time.time() - start_time) * 1000)

                if attempts >= config.max_attempts:
                    self._record_attempt(circuit_breaker or "default", False, duration_ms)

                    if fallback:
                        try:
                            fb_result = fallback()
                            return RetryResult(
                                success=True, attempts=attempts, total_duration_ms=duration_ms,
                                last_error=f"fallback_after_retry: {last_error}", result=fb_result
                            )
                        except Exception as fb_error:
                            return RetryResult(
                                success=False, attempts=attempts, total_duration_ms=duration_ms,
                                last_error=f"fallback_error: {fb_error}", result=None
                            )

                    return RetryResult(
                        success=False, attempts=attempts, total_duration_ms=duration_ms,
                        last_error=last_error, result=None
                    )

                delay = self._calculate_delay(config, attempts)
                time.sleep(delay)

        return RetryResult(
            success=False, attempts=attempts, total_duration_ms=int((time.time() - start_time) * 1000),
            last_error=last_error, result=None
        )

    def _calculate_delay(self, config: RetryConfig, attempt: int) -> float:
        if config.strategy == RetryStrategy.FIXED:
            delay = config.base_delay
        elif config.strategy == RetryStrategy.EXPONENTIAL:
            delay = config.base_delay * (config.exponential_base ** (attempt - 1))
        elif config.strategy == RetryStrategy.LINEAR:
            delay = config.base_delay * attempt
        else:
            delay = config.base_delay

        delay = min(delay, config.max_delay)
        if config.jitter:
            delay = delay * (0.5 + random.random() * 0.5)
        return delay

    def _record_attempt(self, name: str, success: bool, duration_ms: int):
        if name not in self.stats:
            self.stats[name] = {"total": 0, "success": 0, "failure": 0}
        self.stats[name]["total"] += 1
        if success:
            self.stats[name]["success"] += 1
        else:
            self.stats[name]["failure"] += 1

    def get_stats(self) -> Dict[str, Any]:
        result = {}
        for name, stats in self.stats.items():
            total = stats["total"]
            success = stats["success"]
            result[name] = {
                "total": total, "success": success, "failure": stats["failure"],
                "success_rate": f"{success/total*100:.1f}%" if total > 0 else "N/A"
            }
        circuits = {name: cb.get_status() for name, cb in self.circuit_breakers.items()}
        return {"retry_stats": result, "circuit_breakers": circuits}


_retry_engine: Optional['RetryEngine'] = None


def get_retry_engine() -> 'RetryEngine':
    global _retry_engine
    if _retry_engine is None:
        _retry_engine = RetryEngine()
    return _retry_engine
__exports__ = ['CircuitBreaker', 'CircuitBreakerConfig', 'CircuitBreakerOpenError', 'CircuitBreakerState', 'CircuitState', 'RetryConfig', 'RetryEngine', 'RetryResult', 'RetryStrategy', 'get_retry_engine']


