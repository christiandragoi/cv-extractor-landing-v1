from datetime import datetime
import structlog

logger = structlog.get_logger()


class CircuitBreaker:
    FAILURE_THRESHOLD = 3
    RECOVERY_TIMEOUT = 300

    def record_failure(self, provider):
        provider.circuit_breaker_failures += 1
        provider.circuit_breaker_last_failure = datetime.utcnow()
        if provider.circuit_breaker_failures >= self.FAILURE_THRESHOLD:
            provider.circuit_breaker_state = "OPEN"
            logger.warning(f"Circuit opened for provider {provider.display_name}")

    def record_success(self, provider):
        if provider.circuit_breaker_state == "HALF_OPEN":
            provider.circuit_breaker_state = "CLOSED"
            provider.circuit_breaker_failures = 0
            logger.info(f"Circuit closed for provider {provider.display_name}")

    def can_attempt(self, provider) -> bool:
        if provider.circuit_breaker_state == "CLOSED":
            return True
        if provider.circuit_breaker_state == "OPEN":
            if provider.circuit_breaker_last_failure:
                elapsed = (datetime.utcnow() - provider.circuit_breaker_last_failure).total_seconds()
                if elapsed > self.RECOVERY_TIMEOUT:
                    provider.circuit_breaker_state = "HALF_OPEN"
                    return True
        return False
