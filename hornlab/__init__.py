"""Bounded propositional definite-Horn inference and model witnesses."""
from .core import analyze, validate
from .verify import verify
__all__ = ['analyze', 'validate', 'verify']
