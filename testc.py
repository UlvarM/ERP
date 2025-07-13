"""
Täidab warehouse.db inventari- ja tootetabelid demoadmetega.

Käivita:
    python -m tests.seed_demo_data
"""

from database import SessionLocal, engine
from logic import (add_material_to_product, assign_product_categories,
                   create_category, create_material, create_product)
from models import Base


def run():
    # loo tabelid, kui neid veel pole
    Base.metadata.create_all(engine)

    with SessionLocal() as db:
        # ───── Lao materjalid ─────
        alu20 = create_material(
            db,
            name="NELIKANT 20×20×2 ALU 6 m",
            stock_qty=120,
            type="tube",
            material_type="aluminium",
            tube_profile="nelikanttoru",
            tube_length=6000,
            tube_dimension="20×20",
            tube_thickness="2",
        )
        alu40 = create_material(
            db,
            name="NELIKANT 40×20×2 ALU 6 m",
            stock_qty=100,
            type="tube",
            material_type="aluminium",
            tube_profile="nelikanttoru",
            tube_length=6000,
            tube_dimension="40×20",
            tube_thickness="2",
        )
        plate = create_material(
            db,
            name="PLEKK S235 5 mm",
            stock_qty=500,
            type="general",
            material_type="steel",
        )
        bolt = create_material(
            db,
            name="Polt M8×20",
            stock_qty=1000,
            type="general",
            material_type="steel",
        )

        # ───── Kategooria ─────
        create_category(db, "Test")

        # ───── Toode 1: Raam 1 ─────
        raam = create_product(db, "Raam 1", "Lihtne toruraam")
        assign_product_categories(db, raam, ["Test"])
        add_material_to_product(db, raam.id, alu20.id, 4)
        add_material_to_product(db, raam.id, alu40.id, 2)
        add_material_to_product(db, raam.id, plate.id, 1)

        # ───── Toode 2: Riiul 1 ─────
        riiul = create_product(db, "Riiul 1", "Riiul toruraamiga")
        assign_product_categories(db, riiul, ["Test"])
        add_material_to_product(db, riiul.id, alu20.id, 6)
        add_material_to_product(db, riiul.id, plate.id, 2)
        add_material_to_product(db, riiul.id, bolt.id, 24)

        db.commit()

    print("Demoadmed lisatud.")


if __name__ == "__main__":
    run()
