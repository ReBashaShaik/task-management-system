"""Shared IP-based limits for public authentication routes."""
from slowapi import Limiter
from slowapi.util import get_remote_address

# A simple in-memory limit is enough for this single-instance learning project.
limiter = Limiter(key_func=get_remote_address)
