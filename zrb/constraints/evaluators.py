from datetime import time, datetime
from ..core.models import Constraint, User, Role, Zone, Operation
from .base import ConstraintEvaluator

class SoDEvaluator(ConstraintEvaluator):
    """
    Evaluates Separation of Duty constraints.
    Supports:
      - Role conflict: condition = {"cannot_have_role": "role_id"}
      - Self-approval: condition = {"prohibited_relation": "self", "attribute": "creator_id"}
    The context must contain a 'storage' key for role conflict checks.
    """
    def evaluate(self, constraint: Constraint, user: User, role: Role, zone: Zone,
                 operation: Operation, context=None) -> bool:
        # If constraint has a target user_id and it doesn't match, ignore
        target = constraint.target or {}
        if target.get("user_id") and target["user_id"] != user.id:
            return False

        # If constraint targets a specific operation and it's not the current one, ignore
        if target.get("operation_id") and target["operation_id"] != operation.id:
            return False

        cond = constraint.condition or {}

        # 1) Role conflict: user cannot have a specific role
        if "cannot_have_role" in cond:
            forbidden_role_id = cond["cannot_have_role"]
            storage = context.get("storage") if context else None
            if storage is None:
                # Without storage we cannot check role membership; assume no violation
                return False
            # Get all roles of the user in the current zone
            user_roles = storage.get_user_roles(user.id, zone.id)
            if any(r.id == forbidden_role_id for r in user_roles):
                return True   # violation – user holds forbidden role
            return False

        # 2) Self‑approval: user cannot approve their own resource
        if cond.get("prohibited_relation") == "self":
            attribute = cond.get("attribute", "creator_id")
            if context is None:
                return False
            creator_id = context.get(attribute)
            if creator_id and str(creator_id) == user.id:
                return True   # violation – user is also the creator
            return False

        # If no known condition, no violation
        return False
    

class TemporalEvaluator(ConstraintEvaluator):
    def evaluate(self, constraint: Constraint, user: User, role: Role, zone: Zone, operation: Operation, context=None) -> bool:
        cond = constraint.condition or {}
        now = datetime.now()
        if "time_range" in cond:
            start, end = cond["time_range"]
            start_t = time.fromisoformat(start)
            end_t = time.fromisoformat(end)
            if not (start_t <= now.time() <= end_t):
                return False
        return True

class AttributeEvaluator(ConstraintEvaluator):
    def evaluate(self, constraint: Constraint, user: User, role: Role, zone: Zone, operation: Operation, context=None) -> bool:
        cond = constraint.condition or {}
        attr = cond.get("attribute")
        op = cond.get("operator")
        val = cond.get("value")
        user_attr = user.attributes.get(attr)
        if op == ">=" and isinstance(user_attr, (int, float)) and user_attr >= val:
            return True
        return False

class ContextEvaluator(ConstraintEvaluator):
    def evaluate(self, constraint: Constraint, user: User, role: Role, zone: Zone, operation: Operation, context=None) -> bool:
        if context is None:
            return False
        cond = constraint.condition or {}
        for k, expected in cond.items():
            if context.get(k) != expected:
                return False
        return True
