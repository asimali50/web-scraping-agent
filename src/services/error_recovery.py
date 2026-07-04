"""Error recovery and retry logic for resilient processing"""

import asyncio
import random
from typing import Callable, Any, Optional, TypeVar, Coroutine
from enum import Enum

from src.services.logger_service import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class RetryStrategy(Enum):
    """Retry strategy types"""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    RANDOM = "random"
    FIXED = "fixed"


class RetryConfig:
    """Configuration for retry behavior"""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay_seconds: float = 1.0,
        max_delay_seconds: float = 30.0,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        backoff_factor: float = 2.0,
    ):
        """
        Initialize retry config

        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay_seconds: Initial delay between retries
            max_delay_seconds: Maximum delay between retries
            strategy: Retry strategy to use
            backoff_factor: Multiplier for exponential backoff
        """
        self.max_attempts = max_attempts
        self.initial_delay_seconds = initial_delay_seconds
        self.max_delay_seconds = max_delay_seconds
        self.strategy = strategy
        self.backoff_factor = backoff_factor

    def get_delay(self, attempt_number: int) -> float:
        """
        Calculate delay for given attempt number

        Args:
            attempt_number: Which attempt (0-indexed)

        Returns:
            Delay in seconds
        """
        if self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.initial_delay_seconds * (self.backoff_factor ** attempt_number)
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.initial_delay_seconds * (attempt_number + 1)
        elif self.strategy == RetryStrategy.RANDOM:
            delay = random.uniform(self.initial_delay_seconds, self.max_delay_seconds)
        else:  # FIXED
            delay = self.initial_delay_seconds

        return min(delay, self.max_delay_seconds)


class ErrorRecovery:
    """Error recovery and retry handler"""

    # Retryable exceptions (transient errors)
    RETRYABLE_ERRORS = (
        TimeoutError,
        ConnectionError,
        OSError,
        RuntimeError,
    )

    # Non-retryable exceptions (permanent errors)
    NON_RETRYABLE_ERRORS = (
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
    )

    @staticmethod
    async def retry_async(
        coro_func: Callable[..., Coroutine],
        *args,
        config: Optional[RetryConfig] = None,
        **kwargs,
    ) -> Any:
        """
        Execute async function with retry logic

        Args:
            coro_func: Async function to call
            *args: Positional arguments
            config: Retry configuration
            **kwargs: Keyword arguments

        Returns:
            Result from coro_func

        Raises:
            The last exception if all retries exhausted
        """
        if config is None:
            config = RetryConfig()

        last_exception = None

        for attempt in range(config.max_attempts):
            try:
                logger.debug(f"Attempt {attempt + 1}/{config.max_attempts}")
                result = await coro_func(*args, **kwargs)
                return result

            except ErrorRecovery.NON_RETRYABLE_ERRORS as e:
                logger.warning(f"Non-retryable error: {e}")
                raise

            except Exception as e:
                last_exception = e
                is_last_attempt = attempt == config.max_attempts - 1

                if is_last_attempt:
                    logger.error(f"All {config.max_attempts} attempts failed")
                    raise

                delay = config.get_delay(attempt)
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)

        raise last_exception

    @staticmethod
    def retry_sync(
        func: Callable,
        *args,
        config: Optional[RetryConfig] = None,
        **kwargs,
    ) -> Any:
        """
        Execute sync function with retry logic

        Args:
            func: Function to call
            *args: Positional arguments
            config: Retry configuration
            **kwargs: Keyword arguments

        Returns:
            Result from func

        Raises:
            The last exception if all retries exhausted
        """
        if config is None:
            config = RetryConfig()

        last_exception = None

        for attempt in range(config.max_attempts):
            try:
                logger.debug(f"Attempt {attempt + 1}/{config.max_attempts}")
                result = func(*args, **kwargs)
                return result

            except ErrorRecovery.NON_RETRYABLE_ERRORS as e:
                logger.warning(f"Non-retryable error: {e}")
                raise

            except Exception as e:
                last_exception = e
                is_last_attempt = attempt == config.max_attempts - 1

                if is_last_attempt:
                    logger.error(f"All {config.max_attempts} attempts failed")
                    raise

                delay = config.get_delay(attempt)
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                asyncio.run(asyncio.sleep(delay))

        raise last_exception


class CircuitBreaker:
    """Circuit breaker pattern for failing services"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 60.0,
        name: str = "CircuitBreaker",
    ):
        """
        Initialize circuit breaker

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout_seconds: Time before attempting recovery
            name: Name for logging
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.name = name

        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open

    def record_success(self) -> None:
        """Record successful operation"""
        self.failure_count = 0
        self.state = "closed"
        logger.debug(f"{self.name}: Circuit closed (success)")

    def record_failure(self) -> None:
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = asyncio.get_event_loop().time() if self.state != "closed" else None

        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(
                f"{self.name}: Circuit opened after {self.failure_count} failures"
            )

    def is_available(self) -> bool:
        """Check if circuit breaker allows requests"""
        if self.state == "closed":
            return True

        if self.state == "open":
            if self.last_failure_time is None:
                return False

            elapsed = asyncio.get_event_loop().time() - self.last_failure_time
            if elapsed >= self.recovery_timeout_seconds:
                self.state = "half_open"
                self.failure_count = 0
                logger.info(f"{self.name}: Circuit half-open, testing recovery")
                return True

            return False

        # half_open state
        return True

    async def call_with_breaker(
        self,
        coro_func: Callable[..., Coroutine],
        *args,
        **kwargs,
    ) -> Any:
        """
        Execute coroutine with circuit breaker protection

        Args:
            coro_func: Async function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result from coro_func

        Raises:
            RuntimeError if circuit is open
        """
        if not self.is_available():
            raise RuntimeError(f"{self.name}: Circuit breaker is open")

        try:
            result = await coro_func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise
