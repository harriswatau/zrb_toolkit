from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from ..core.models import User, Role, Zone, Operation, Constraint

class ConstraintEvaluator(ABC):
    @abstractmethod
    def evaluate(self, constraint: Constraint, user: User, role: Role, zone: Zone, operation: Operation, context: Optional[Dict] = None) -> bool:
        """Return True if constraint condition is met (for positive) or violation detected (for negative)."""
        pass