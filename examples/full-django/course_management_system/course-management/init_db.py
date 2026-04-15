import yaml
from zrb.storage.sqlalchemy import SQLAlchemyStore

def init_db():
    store = SQLAlchemyStore("sqlite:///university.db")
    store.create_all()
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    # Bulk create methods (simplified)
    for z in config["zones"]:
        store.create_zone(z)
    for r in config["roles"]:
        store.create_role(r)
    for o in config["operations"]:
        store.create_operation(o)
    for g in config["gamma_mappings"]:
        store.create_gamma_mapping(g)
    for c in config["constraints"]:
        store.create_constraint(c)
    print("Database initialised.")

if __name__ == "__main__":
    init_db()