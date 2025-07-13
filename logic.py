from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from models import (Category, History, Material, Product, ProductParts,
                    Project, ProjectParts)


# ───────── categories ─────────
def get_categories(db: Session):
    return db.execute(select(Category)).scalars().all()


def create_category(db: Session, name: str):
    cat = db.execute(select(Category).filter_by(name=name)).scalar_one_or_none()
    if cat:
        return cat
    cat = Category(name=name)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def assign_product_categories(db: Session, product: Product, names: list[str]):
    product.categories.clear()
    for nm in names:
        cat = db.execute(select(Category).filter_by(name=nm)).scalar_one_or_none()
        if not cat:
            cat = Category(name=nm)
            db.add(cat)
            db.flush()
        product.categories.append(cat)
    db.commit()
    db.refresh(product)
    return product


# ───────── products ─────────
def get_products(db: Session, category_names: list[str] | None = None):
    q = db.query(Product).options(joinedload(Product.categories))
    if category_names:
        q = q.join(Product.categories).filter(Category.name.in_(category_names))
    return q.all()


def create_product(
    db: Session,
    name: str,
    description: str = "",
    note: str = "",
    production_time: int | None = None,
):
    p = Product(
        name=name,
        description=description,
        note=note,
        production_time=production_time,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def update_product(
    db: Session,
    pid: int,
    name: str,
    description: str = "",
    note: str = "",
    production_time: int | None = None,
):
    p = db.query(Product).filter_by(id=pid).first()
    if not p:
        return None
    p.name = name
    p.description = description
    p.note = note
    p.production_time = production_time
    db.commit()
    db.refresh(p)
    return p


def delete_product(db: Session, pid: int):
    p = db.query(Product).filter_by(id=pid).first()
    if p:
        db.delete(p)
        db.commit()


# ───────── product BOM ─────────
def get_product_parts(db: Session, product_id: int):
    return (
        db.query(ProductParts)
        .options(joinedload(ProductParts.material))
        .filter_by(product_id=product_id)
        .all()
    )


def add_material_to_product(db: Session, product_id: int, material_id: int, qty: int):
    row = (
        db.query(ProductParts)
        .filter_by(product_id=product_id, material_id=material_id)
        .first()
    )
    if row:
        row.quantity_required += qty
    else:
        db.add(
            ProductParts(
                product_id=product_id,
                material_id=material_id,
                quantity_required=qty,
            )
        )
    db.commit()


def remove_material_from_product(db: Session, part_id: int):
    pp = db.query(ProductParts).filter_by(id=part_id).first()
    if pp:
        db.delete(pp)
        db.commit()


# ────────────── MATERIALS ──────────────
def get_materials(db: Session):
    return db.query(Material).all()


def get_material_by_name(db: Session, name: str):
    return db.query(Material).filter_by(name=name).first()


def create_material(
    db: Session,
    name: str,
    stock_qty: int = 0,
    type: str = "general",
    material_type: str | None = None,
    tube_profile: str | None = None,
    tube_length: int | None = None,
    tube_quantity: int | None = None,
    tube_dimension: str | None = None,
    tube_thickness: str | None = None,
):
    m = Material(
        name=name,
        stock_qty=stock_qty,
        type=type,
        material_type=material_type,
        tube_profile=tube_profile,
        tube_length=tube_length,
        tube_quantity=tube_quantity,
        tube_dimension=tube_dimension,
        tube_thickness=tube_thickness,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def update_material_details(
    db: Session,
    material_id: int,
    stock_qty: int | None = None,
    tube_length: int | None = None,
    tube_quantity: int | None = None,
    tube_dimension: str | None = None,
    tube_thickness: str | None = None,
    tube_profile: str | None = None,
    material_type: str | None = None,
):
    m = db.query(Material).filter_by(id=material_id).first()
    if not m:
        raise ValueError("Material not found")

    if stock_qty is not None:
        m.stock_qty = stock_qty
    m.tube_length = tube_length
    m.tube_quantity = tube_quantity
    m.tube_dimension = tube_dimension
    m.tube_thickness = tube_thickness
    m.tube_profile = tube_profile
    m.material_type = material_type

    db.commit()
    db.refresh(m)
    return m


def delete_material(db: Session, material_id: int):
    m = db.query(Material).filter_by(id=material_id).first()
    if m:
        db.delete(m)
        db.commit()


# ────────────── PROJECTS ──────────────
def get_projects(db: Session):
    return db.query(Project).all()


def get_project_parts(db: Session, project_id: int):
    return db.query(ProjectParts).filter_by(project_id=project_id).all()


def ensure_project_has_parts(db: Session, project: Project):
    if not project or get_project_parts(db, project.id):
        return
    if not project.product:
        return
    prod = db.query(Product).filter_by(name=project.product).first()
    if not prod:
        return
    prod_parts = get_product_parts(db, prod.id)
    multiplier = project.quantity or 1
    for pp in prod_parts:
        db.add(
            ProjectParts(
                project_id=project.id,
                material_id=pp.material_id,
                quantity_required=pp.quantity_required * multiplier,
            )
        )
    db.commit()


def create_project(
    db: Session,
    name: str,
    description: str,
    parts: list[dict],
    **extra,
):
    p = Project(name=name, description=description, **extra)
    db.add(p)
    db.commit()
    db.refresh(p)

    qty_multiplier = extra.get("quantity", 1)

    if not parts:
        prod_name = extra.get("product")
        if prod_name:
            prod = db.query(Product).filter_by(name=prod_name).first()
            if prod:
                prod_parts = get_product_parts(db, prod.id)
                parts = [
                    {
                        "material_id": pp.material_id,
                        "quantity_required": pp.quantity_required * qty_multiplier,
                    }
                    for pp in prod_parts
                ]

    for prt in parts:
        db.add(
            ProjectParts(
                project_id=p.id,
                material_id=prt["material_id"],
                quantity_required=prt["quantity_required"],
            )
        )
    db.commit()
    return p


def update_project_field(db: Session, project_id: int, field: str, value):
    p = db.query(Project).filter_by(id=project_id).first()
    if not p:
        return None
    setattr(p, field, value)
    db.commit()
    db.refresh(p)
    return p


def delete_project(db: Session, project_id: int):
    p = db.query(Project).filter_by(id=project_id).first()
    if p:
        db.delete(p)
        db.commit()


# ────────────── STOCK DEDUCTION ──────────────
def start_project_deduct_inventory(db: Session, project_id: int):
    project = db.query(Project).filter_by(id=project_id).first()
    ensure_project_has_parts(db, project)

    parts = get_project_parts(db, project_id)
    for prt in parts:
        mat = db.query(Material).filter_by(id=prt.material_id).first()
        if mat is None or mat.stock_qty < prt.quantity_required:
            raise ValueError(
                f"Insufficient stock for {mat.name if mat else prt.material_id}"
            )

    for prt in parts:
        mat = db.query(Material).filter_by(id=prt.material_id).first()
        mat.stock_qty -= prt.quantity_required
        db.add(
            History(
                project_id=project_id,
                action="Stock deducted",
                details=f"-{prt.quantity_required} from {mat.name}",
            )
        )
    db.commit()
    return True


# ────────────── HISTORY ──────────────
def get_history(db: Session):
    return db.query(History).all()


def add_history_entry(
    db: Session,
    action: str,
    details: str,
    project_id: int | None = None,
):
    db.add(
        History(
            timestamp=datetime.now(),
            project_id=project_id,
            action=action,
            details=details,
        )
    )
    db.commit()
