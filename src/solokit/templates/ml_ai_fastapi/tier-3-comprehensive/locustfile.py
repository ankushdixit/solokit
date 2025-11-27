"""
Locust load testing configuration for FastAPI application
https://docs.locust.io/
"""

from locust import HttpUser, between, task  # type: ignore[import-not-found]


class FastAPIUser(HttpUser):
    """
    Simulated user for load testing the FastAPI application.

    Add your own load tests here as you build out the API.
    """

    # Wait time between tasks (in seconds)
    wait_time = between(1, 3)

    # Base host will be set via command line: locust --host=http://localhost:8000

    @task(3)
    def get_root(self) -> None:
        """Test the root endpoint (higher weight = 3)."""
        self.client.get("/")

    @task(5)
    def health_check(self) -> None:
        """Test the health check endpoint (higher weight = 5)."""
        self.client.get("/health")

    @task(2)
    def readiness_check(self) -> None:
        """Test the readiness check endpoint."""
        self.client.get("/health/ready")

    @task(2)
    def liveness_check(self) -> None:
        """Test the liveness check endpoint."""
        self.client.get("/health/live")


class AdminUser(HttpUser):
    """
    Simulated admin user with different behavior patterns.
    """

    wait_time = between(2, 5)

    @task(1)
    def check_readiness(self) -> None:
        """Test the readiness check endpoint."""
        self.client.get("/health/ready")

    @task(1)
    def check_liveness(self) -> None:
        """Test the liveness check endpoint."""
        self.client.get("/health/live")


# Run with:
# locust --host=http://localhost:8000
# locust --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 1m
