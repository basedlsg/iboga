"""Core Bildung / Iboga runtime primitives.

The public product is the curriculum runner. The Iboga protocol is an internal
discontinuity primitive; this package keeps its artifacts explicit, inspectable,
and safe to evaluate without anthropomorphic claims.
"""

from .bardo import BardoSession
from .seals import VERIFIED_SEALS, saturn_test, validate_seal
from .stages import STAGES, audit_stage_cases, get_stage

__all__ = ["BardoSession", "STAGES", "VERIFIED_SEALS", "audit_stage_cases", "get_stage", "saturn_test", "validate_seal"]
