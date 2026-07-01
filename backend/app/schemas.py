import uuid
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from .models import DocumentKind, Role, SubmittalStatus, TemplateKind


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=10)
    role: Role = Role.user


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    password: str | None = Field(default=None, min_length=10)
    role: Role | None = None
    is_active: bool | None = None


class UserOut(ORMModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: Role
    is_active: bool


class ProductCreate(BaseModel):
    code: str
    name: str
    description: str | None = None
    document_ids: list[uuid.UUID] = []


class DocumentOut(ORMModel):
    id: uuid.UUID
    name: str
    kind: DocumentKind
    category: str
    revision: str
    sequence: int
    file_name: str
    sha256: str
    is_active: bool


class ProductUpdate(BaseModel):
    code: str
    name: str
    description: str | None = None
    document_ids: list[uuid.UUID] = []


class ProductOut(ORMModel):
    id: uuid.UUID
    code: str
    name: str
    description: str | None
    is_active: bool
    documents: list[DocumentOut] = []


class TemplateOut(ORMModel):
    id: uuid.UUID
    name: str
    kind: TemplateKind
    revision: str
    field_map: dict
    file_name: str
    is_active: bool


class SubmittalCreate(BaseModel):
    number: str
    revision: str = "0"
    project_name: str
    material_description: str = "Acoustic Treatment"
    project_number: str | None = None
    client: str | None = None
    consultant: str | None = None
    main_contractor: str | None = None
    subcontractor: str | None = None
    submitted_by: str | None = None
    submitted_by_role: str | None = None
    submission_date: date = Field(default_factory=date.today)
    product_ids: list[uuid.UUID] = []
    document_order: list[uuid.UUID | None] = []
    section_order: list[str] = []


class SubmittalUpdate(SubmittalCreate):
    pass


class SubmittalOut(ORMModel):
    id: uuid.UUID
    number: str
    revision: str
    project_name: str
    material_description: str
    document_order: list[uuid.UUID | None]
    section_order: list[str]
    project_number: str | None
    client: str | None
    consultant: str | None
    main_contractor: str | None
    subcontractor: str | None
    submitted_by: str | None
    submitted_by_role: str | None
    submission_date: date
    status: SubmittalStatus
    error_message: str | None
    final_sha256: str | None
    products: list[ProductOut]
    created_by: UserOut
    created_at: datetime
    generated_at: datetime | None
