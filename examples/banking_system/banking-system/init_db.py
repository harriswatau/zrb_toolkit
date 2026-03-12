#!/usr/bin/env python3
import yaml
from zrb.storage.sqlalchemy import SQLAlchemyStore
from zrb.core.models import User, Zone, Role, Operation, GammaMapping, Constraint, UserZoneRole
from zrb.core.types import ConstraintType
import uuid

def load_config(config_file):
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

def init_db():
    store = SQLAlchemyStore("sqlite:///banking.db")
    store.create_all()

    config = load_config("config.yaml")

    # Create zones
    zone_map = {}
    for z in config["zones"]:
        zone = Zone(**z)
        store.create_zone(zone)
        zone_map[z["id"]] = zone

    # Create operations
    op_map = {}
    for o in config["operations"]:
        op = Operation(**o)
        store.create_operation(op)
        op_map[o["id"]] = op

    # Create roles (including extended ones)
    all_roles = config["roles"] + config.get("roles_extended", [])
    role_map = {}
    for r in all_roles:
        role = Role(
            id=r["id"],
            zone_id=r["zone_id"],
            name=r["name"],
            parent_role_id=r.get("parent_role_id"),
            description=r.get("description", ""),
            base_permissions=set(r.get("base_permissions", []))
        )
        store.create_role(role)
        role_map[r["id"]] = role

    # Create gamma mappings (if any)
    for g in config.get("gamma_mappings", []):
        gamma = GammaMapping(**g)
        store.create_gamma_mapping(gamma)

    # Create constraints
    for c in config.get("constraints", []):
        c["type"] = ConstraintType(c["type"])
        constraint = Constraint(**c)
        store.create_constraint(constraint)

    # Create users
    user_map = {}
    for u in config.get("users", []):
        user = User(**u)
        store.create_user(user)
        user_map[u["id"]] = user

    # Create assignments
    for a in config.get("assignments", []):
        uzr = UserZoneRole(**a)
        store.assign_user_to_role(uzr.user_id, uzr.zone_id, uzr.role_id)

    print("Database initialised successfully.")

if __name__ == "__main__":
    init_db()