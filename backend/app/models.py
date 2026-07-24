import enum
import uuid
from datetime import date, datetime
from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, Integer, LargeBinary, String, Table, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class Role(str, enum.Enum):
    system_admin = "system_admin"
    admin = "admin"
    user = "user"


class DocumentKind(str, enum.Enum):
    standard = "standard"
    product = "product"
    project = "project"


class TemplateKind(str, enum.Enum):
    cover = "cover"
    index = "index"
    divider = "divider"


class SubmittalStatus(str, enum.Enum):
    draft = "draft"
    generated = "generated"
    failed = "failed"


product_documents = Table(
    "product_documents", Base.metadata,
    Column("product_id", UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
    Column("document_id", UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True),
)

submittal_products = Table(
    "submittal_products", Base.metadata,
    Column("submittal_id", UUID(as_uuid=True), ForeignKey("submittals.id", ondelete="CASCADE"), primary_key=True),
    Column("product_id", UUID(as_uuid=True), ForeignKey("products.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.user)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Product(Base):
    __tablename__ = "products"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Manufacturer document codes can be shared by multiple product variants.
    code: Mapped[str] = mapped_column(String(80), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    documents: Mapped[list["Document"]] = relationship(secondary=product_documents, lazy="selectin")


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    kind: Mapped[DocumentKind] = mapped_column(Enum(DocumentKind))
    category: Mapped[str] = mapped_column(String(120), default="General")
    revision: Mapped[str] = mapped_column(String(40), default="0")
    sequence: Mapped[int] = mapped_column(Integer, default=100)
    file_name: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(100), default="application/pdf")
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    content: Mapped[bytes] = mapped_column(LargeBinary)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Template(Base):
    __tablename__ = "templates"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    kind: Mapped[TemplateKind] = mapped_column(Enum(TemplateKind), index=True)
    revision: Mapped[str] = mapped_column(String(40), default="0")
    field_map: Mapped[dict] = mapped_column(JSONB, default=dict)
    file_name: Mapped[str] = mapped_column(String(255))
    sha256: Mapped[str] = mapped_column(String(64))
    content: Mapped[bytes] = mapped_column(LargeBinary)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Submittal(Base):
    __tablename__ = "submittals"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    number: Mapped[str] = mapped_column(String(80), index=True)
    revision: Mapped[str] = mapped_column(String(40), default="0")
    project_name: Mapped[str] = mapped_column(String(255))
    material_description: Mapped[str] = mapped_column(String(255), default="Acoustic Treatment")
    document_order: Mapped[list] = mapped_column(JSONB, default=list)
    section_order: Mapped[list] = mapped_column(JSONB, default=list)
    project_number: Mapped[str | None] = mapped_column(String(100))
    client: Mapped[str | None] = mapped_column(String(255))
    client_title: Mapped[str | None] = mapped_column(String(120), default="CLIENT")
    consultant: Mapped[str | None] = mapped_column(String(255))
    consultant_title: Mapped[str | None] = mapped_column(String(120), default="CONSULTANT")
    main_contractor: Mapped[str | None] = mapped_column(String(255))
    main_contractor_title: Mapped[str | None] = mapped_column(String(120), default="MAIN CONTRACTOR")
    subcontractor: Mapped[str | None] = mapped_column(String(255))
    subcontractor_title: Mapped[str | None] = mapped_column(String(120), default="SUB CONTRACTOR")
    submitted_by: Mapped[str | None] = mapped_column(String(255))
    submitted_by_role: Mapped[str | None] = mapped_column(String(160))
    submission_date: Mapped[date] = mapped_column(Date, default=date.today)
    status: Mapped[SubmittalStatus] = mapped_column(Enum(SubmittalStatus), default=SubmittalStatus.draft)
    error_message: Mapped[str | None] = mapped_column(Text)
    final_pdf: Mapped[bytes | None] = mapped_column(LargeBinary)
    final_sha256: Mapped[str | None] = mapped_column(String(64))
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_by: Mapped[User] = relationship()
    products: Mapped[list[Product]] = relationship(secondary=submittal_products, lazy="selectin")
    attachments: Mapped[list["SubmittalAttachment"]] = relationship(cascade="all, delete-orphan", lazy="selectin")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SubmittalAttachment(Base):
    __tablename__ = "submittal_attachments"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submittal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("submittals.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(120), default="Proposed Materials")
    sequence: Mapped[int] = mapped_column(Integer, default=1000)
    sha256: Mapped[str] = mapped_column(String(64))
    content: Mapped[bytes] = mapped_column(LargeBinary)
