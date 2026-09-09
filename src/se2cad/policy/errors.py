"""Conversion-policy failures."""

from __future__ import annotations

from se2cad.preflight.model import ConversionPreflight


class ConversionPolicyError(Exception):
    """Base class for strict/permissive conversion-policy failures."""


class ConversionRefusedError(ConversionPolicyError):
    """Strict conversion refused because a block is unknown or unsupported."""

    def __init__(self, message: str, preflight: ConversionPreflight) -> None:
        super().__init__(message)
        self.preflight = preflight


class UnknownConversionPolicyError(ConversionPolicyError):
    """Caller named a policy that is not strict or permissive."""
