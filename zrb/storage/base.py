from abc import ABC, abstractmethod
from typing import Optional, List, Set, Dict
from ..core.models import User, Zone, Role, Operation, UserZoneRole, GammaMapping, Constraint

class Storage(ABC):
    @abstractmethod
    def get_user(self, user_id: str) -> Optional[User]:
        pass

    @abstractmethod
    def get_zone(self, zone_id: str) -> Optional[Zone]:
        pass

    @abstractmethod
    def get_role(self, role_id: str) -> Optional[Role]:
        pass

    @abstractmethod
    def get_operation(self, op_id: str) -> Optional[Operation]:
        pass

    @abstractmethod
    def get_user_roles(self, user_id: str, zone_id: str) -> List[Role]:
        """Return all roles of user in given zone."""
        pass

    @abstractmethod
    def get_zone_roles(self, zone_id: str) -> List[Role]:
        pass

    @abstractmethod
    def get_zone_children(self, zone_id: str) -> List[Zone]:
        pass

    @abstractmethod
    def get_gamma_mappings(self, child_zone_id: str, child_role_id: str) -> List[GammaMapping]:
        pass

    @abstractmethod
    def get_constraints(self, **filters) -> List[Constraint]:
        pass

    # Write methods (omitted for brevity, but should exist)