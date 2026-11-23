from vigilo.ratelimit import RateLimiter


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_limits_per_key_within_the_window():
    clock = FakeClock()
    limiter = RateLimiter(max_events=2, window_seconds=60, clock=clock)
    assert limiter.allow("a")
    assert limiter.allow("a")
    assert not limiter.allow("a")
    assert limiter.allow("b")  # another IP is not affected


def test_events_expire_after_the_window():
    clock = FakeClock()
    limiter = RateLimiter(max_events=1, window_seconds=60, clock=clock)
    assert limiter.allow("a")
    clock.now = 59.9
    assert not limiter.allow("a")
    clock.now = 60.0
    assert limiter.allow("a")
