from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# ───────── association ─────────
product_categories = Table(
    "product_categories",
    Base.metadata,
    Column("product_id", Integer, ForeignKey("products.id"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id"), primary_key=True),
)

# ───────── categories ─────────
class Category(Base):
    __tablename__ = "categories"

    id   = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    products = relationship(
        "Product",
        secondary=product_categories,
        back_populates="categories",
    )

# ───────── products ─────────
class Product(Base):
    __tablename__ = "products"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String, unique=True, nullable=False)
    description     = Column(String)
    note            = Column(String)
    production_time = Column(Integer)                         # minutes

    parts      = relationship("ProductParts", back_populates="product", cascade="all, delete-orphan")
    categories = relationship("Category", secondary=product_categories, back_populates="products")

# ───────── materials ─────────
class Material(Base):
    __tablename__ = "materials"

    id             = Column(Integer, primary_key=True, index=True)
    name           = Column(String, unique=True, nullable=False)
    stock_qty      = Column(Integer, default=0)
    type           = Column(String, default="general")        # general | tube
    material_type  = Column(String)
    tube_profile   = Column(String)
    tube_length    = Column(Integer)
    tube_quantity  = Column(Integer)
    tube_dimension = Column(String)
    tube_thickness = Column(String)

# ───────── product-parts (BOM) ─────────
class ProductParts(Base):
    __tablename__ = "product_parts"

    id                = Column(Integer, primary_key=True, index=True)
    product_id        = Column(Integer, ForeignKey("products.id"))
    material_id       = Column(Integer, ForeignKey("materials.id"))
    quantity_required = Column(Integer, default=1)

    product  = relationship("Product", back_populates="parts")
    material = relationship("Material")

# ───────── projects ─────────
class Project(Base):
    __tablename__ = "projects"

    id           = Column(Integer, primary_key=True, index=True)
    name         = Column(String, nullable=False)
    description  = Column(String)

    delivery     = Column(String)
    customer     = Column(String)
    order_number = Column(String)
    product      = Column(String)           # Product.name
    notes        = Column(String)
    quantity     = Column(Integer)
    deadline     = Column(DateTime)

    afterone  = Column(String, default="-")
    cutting   = Column(String, default="-")
    laser     = Column(String, default="-")
    bending   = Column(String, default="-")
    drilling  = Column(String, default="-")
    welding   = Column(String, default="-")
    grinding  = Column(String, default="-")
    coating   = Column(String, default="-")
    delivered = Column(String, default="-")

    parts = relationship("ProjectParts", back_populates="project", cascade="all, delete-orphan")

# ───────── project-parts ─────────
class ProjectParts(Base):
    __tablename__ = "project_parts"

    id                = Column(Integer, primary_key=True, index=True)
    project_id        = Column(Integer, ForeignKey("projects.id"))
    material_id       = Column(Integer, ForeignKey("materials.id"))
    quantity_required = Column(Integer, default=1)

    project  = relationship("Project", back_populates="parts")
    material = relationship("Material")

# ───────── history ─────────
class History(Base):
    __tablename__ = "history"

    id         = Column(Integer, primary_key=True, index=True)
    timestamp  = Column(DateTime, default=datetime.now)
    project_id = Column(Integer, ForeignKey("projects.id"))
    action     = Column(String, nullable=False)
    details    = Column(String, nullable=False)

    project = relationship("Project")
