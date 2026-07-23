import hashlib
import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from io import BytesIO
from fastapi import Depends, FastAPI, File, Form, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from pypdf import PdfReader
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from .config import settings
from .database import Base, SessionLocal, engine, get_db
from .models import Document, DocumentKind, Product, Role, Submittal, SubmittalAttachment, SubmittalStatus, Template, TemplateKind, User
from .pdf_engine import FileEntry, Section, assemble, effective_field_map
from .schemas import DocumentOut, ProductCreate, ProductOut, ProductUpdate, SubmittalCreate, SubmittalOut, SubmittalUpdate, TemplateOut, Token, UserCreate, UserOut, UserUpdate
from .security import admin_only, create_token, current_user, hash_password, system_admin_only, verify_password


def read_pdf(upload: UploadFile) -> bytes:
    content = upload.file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, "File exceeds upload limit")
    if upload.content_type != "application/pdf" or not content.startswith(b"%PDF"):
        raise HTTPException(400, "Only PDF files are accepted")
    try:
        PdfReader(BytesIO(content))
    except Exception as exc:
        raise HTTPException(400, "Invalid PDF") from exc
    return content


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text("ALTER TYPE role ADD VALUE IF NOT EXISTS 'system_admin'"))
    with engine.begin() as connection:
        for column, sql_type in (("main_contractor", "VARCHAR(255)"), ("subcontractor", "VARCHAR(255)"), ("submitted_by", "VARCHAR(255)"), ("submitted_by_role", "VARCHAR(160)")):
            connection.execute(text(f"ALTER TABLE submittals ADD COLUMN IF NOT EXISTS {column} {sql_type}"))
        connection.execute(text("ALTER TABLE submittal_attachments ADD COLUMN IF NOT EXISTS category VARCHAR(120) DEFAULT 'Proposed Materials'"))
        connection.execute(text("ALTER TABLE submittals ADD COLUMN IF NOT EXISTS material_description VARCHAR(255) DEFAULT 'Acoustic Treatment'"))
        connection.execute(text("ALTER TABLE submittals ADD COLUMN IF NOT EXISTS document_order JSONB DEFAULT '[]'::jsonb"))
        connection.execute(text("ALTER TABLE submittals ADD COLUMN IF NOT EXISTS section_order JSONB DEFAULT '[]'::jsonb"))
        connection.execute(text("ALTER TABLE documents DROP CONSTRAINT IF EXISTS uq_document_revision"))
        connection.execute(text("DROP INDEX IF EXISTS ix_products_code"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_products_code ON products (code)"))
        connection.execute(text("UPDATE products SET code = BTRIM(code) WHERE code <> BTRIM(code)"))
        connection.execute(text("UPDATE documents SET category = 'List of Previous Projects' WHERE kind = 'standard' AND (LOWER(name) LIKE '%list of project%' OR LOWER(name) LIKE '%project list%')"))
        connection.execute(text("UPDATE users SET role = 'system_admin' WHERE email = :email"), {"email": settings.bootstrap_admin_email.lower()})
    with SessionLocal() as db:
        if not db.scalar(select(User).where(User.email == settings.bootstrap_admin_email.lower())):
            db.add(User(email=settings.bootstrap_admin_email.lower(), full_name="System Administrator", password_hash=hash_password(settings.bootstrap_admin_password), role=Role.system_admin))
            db.commit()
    yield


app = FastAPI(title="Submittal Preparation API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_origin_regex=settings.cors_origin_regex, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/v1/auth/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == form.username.lower()))
    if not user or not user.is_active or not verify_password(form.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    return Token(access_token=create_token(user), user=UserOut.model_validate(user))


@app.get("/api/v1/auth/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@app.get("/api/v1/users", response_model=list[UserOut])
def users(_: User = Depends(system_admin_only), db: Session = Depends(get_db)):
    return db.scalars(select(User).order_by(User.full_name)).all()


@app.post("/api/v1/users", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, _: User = Depends(system_admin_only), db: Session = Depends(get_db)):
    user = User(email=payload.email.lower(), full_name=payload.full_name, password_hash=hash_password(payload.password), role=payload.role)
    db.add(user); db.commit(); db.refresh(user)
    return user


@app.put("/api/v1/users/{user_id}", response_model=UserOut)
def update_user(user_id: uuid.UUID, payload: UserUpdate, actor: User = Depends(system_admin_only), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    if payload.email is not None:
        user.email = payload.email.lower()
    if payload.full_name is not None:
        user.full_name = payload.full_name.strip()
    if payload.password:
        user.password_hash = hash_password(payload.password)
    if payload.role is not None:
        if user.id == actor.id and payload.role != Role.system_admin:
            raise HTTPException(400, "You cannot remove your own system administrator role")
        user.role = payload.role
    if payload.is_active is not None:
        if user.id == actor.id and not payload.is_active:
            raise HTTPException(400, "You cannot deactivate your own account")
        user.is_active = payload.is_active
    db.commit(); db.refresh(user)
    return user


@app.get("/api/v1/documents", response_model=list[DocumentOut])
def documents(_: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Document).order_by(Document.sequence, Document.name)).all()


@app.post("/api/v1/documents", response_model=DocumentOut, status_code=201)
def upload_document(name: str = Form(), kind: DocumentKind = Form(), category: str = Form("General"), revision: str = Form("0"), sequence: int = Form(100), file: UploadFile = File(), _: User = Depends(admin_only), db: Session = Depends(get_db)):
    content = read_pdf(file)
    digest = hashlib.sha256(content).hexdigest()
    existing = db.scalar(select(Document).where(Document.kind == kind, Document.sha256 == digest))
    if existing:
        # Reuse identical stored PDFs across products instead of duplicating the
        # binary. Upgrade legacy categories when the admin supplies a real type.
        if kind == DocumentKind.product and existing.category in {"General", "Product Document"}:
            existing.category = category
            db.commit(); db.refresh(existing)
        return existing
    item = Document(name=name.strip(), kind=kind, category=category, revision=revision.strip(), sequence=sequence, file_name=file.filename or f"{name}.pdf", sha256=digest, content=content)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/api/v1/documents/{document_id}/file")
def document_file(document_id: uuid.UUID, _: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.get(Document, document_id)
    if not item:
        raise HTTPException(404, "Document not found")
    return StreamingResponse(BytesIO(item.content), media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="{item.file_name}"', "ETag": item.sha256})


@app.delete("/api/v1/documents/{document_id}", status_code=204)
def delete_document(document_id: uuid.UUID, _: User = Depends(admin_only), db: Session = Depends(get_db)):
    item = db.get(Document, document_id)
    if not item:
        raise HTTPException(404, "Document not found")
    db.delete(item); db.commit()
    return Response(status_code=204)


@app.get("/api/v1/templates", response_model=list[TemplateOut])
def templates(_: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Template).order_by(Template.kind, Template.name)).all()


@app.post("/api/v1/templates", response_model=TemplateOut, status_code=201)
def upload_template(name: str = Form(), kind: TemplateKind = Form(), revision: str = Form("0"), field_map: str = Form("{}"), file: UploadFile = File(), _: User = Depends(admin_only), db: Session = Depends(get_db)):
    content = read_pdf(file)
    try:
        mapping = json.loads(field_map)
    except json.JSONDecodeError as exc:
        raise HTTPException(400, "field_map must be valid JSON") from exc
    if kind == TemplateKind.cover:
        db.query(Template).filter(Template.kind == kind, Template.name == name).update({Template.is_active: False})
    else:
        db.query(Template).filter(Template.kind == kind).update({Template.is_active: False})
    item = Template(name=name, kind=kind, revision=revision, field_map=mapping, file_name=file.filename or f"{name}.pdf", sha256=hashlib.sha256(content).hexdigest(), content=content)
    db.add(item); db.commit(); db.refresh(item)
    return item


@app.get("/api/v1/templates/{template_id}/file")
def template_file(template_id: uuid.UUID, _: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.get(Template, template_id)
    if not item:
        raise HTTPException(404, "Template not found")
    return StreamingResponse(BytesIO(item.content), media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="{item.file_name}"', "ETag": item.sha256})


@app.delete("/api/v1/templates/{template_id}", status_code=204)
def delete_template(template_id: uuid.UUID, _: User = Depends(admin_only), db: Session = Depends(get_db)):
    item = db.get(Template, template_id)
    if not item:
        raise HTTPException(404, "Template not found")
    db.delete(item); db.commit()
    return Response(status_code=204)


@app.get("/api/v1/products", response_model=list[ProductOut])
def products(_: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Product).order_by(Product.name)).all()


@app.post("/api/v1/products", response_model=ProductOut, status_code=201)
def create_product(payload: ProductCreate, _: User = Depends(admin_only), db: Session = Depends(get_db)):
    docs = db.scalars(select(Document).where(Document.id.in_(payload.document_ids))).all() if payload.document_ids else []
    item = Product(code=payload.code.strip(), name=payload.name.strip(), description=payload.description, documents=list(docs))
    db.add(item); db.commit(); db.refresh(item)
    return item


@app.put("/api/v1/products/{product_id}", response_model=ProductOut)
def update_product(product_id: uuid.UUID, payload: ProductUpdate, _: User = Depends(admin_only), db: Session = Depends(get_db)):
    item = db.get(Product, product_id)
    if not item:
        raise HTTPException(404, "Product not found")
    docs = db.scalars(select(Document).where(Document.id.in_(payload.document_ids), Document.kind == DocumentKind.product)).all() if payload.document_ids else []
    item.code = payload.code.strip()
    item.name = payload.name.strip()
    item.description = payload.description
    item.documents = list(docs)
    db.commit(); db.refresh(item)
    return item


@app.get("/api/v1/submittals", response_model=list[SubmittalOut])
def list_submittals(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(Submittal).order_by(Submittal.created_at.desc())
    if user.role not in {Role.admin, Role.system_admin}:
        query = query.where(Submittal.created_by_id == user.id)
    return db.scalars(query).unique().all()


@app.post("/api/v1/submittals", response_model=SubmittalOut, status_code=201)
def create_submittal(payload: SubmittalCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    products = db.scalars(select(Product).where(Product.id.in_(payload.product_ids), Product.is_active.is_(True))).all() if payload.product_ids else []
    data = payload.model_dump(exclude={"product_ids", "document_order", "section_order"})
    item = Submittal(**data, document_order=[str(document_id) if document_id else None for document_id in payload.document_order], section_order=payload.section_order, products=list(products), created_by_id=user.id)
    db.add(item); db.commit(); db.refresh(item)
    return item


@app.put("/api/v1/submittals/{submittal_id}", response_model=SubmittalOut)
def update_submittal(submittal_id: str, payload: SubmittalUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    try:
        item = db.get(Submittal, uuid.UUID(submittal_id))
    except ValueError:
        item = None
    if not item or (user.role not in {Role.admin, Role.system_admin} and item.created_by_id != user.id):
        raise HTTPException(404, "Submittal not found")
    if item.status == SubmittalStatus.generated:
        raise HTTPException(409, "Generated submittals cannot be edited. Create a new revision instead.")
    products = db.scalars(select(Product).where(Product.id.in_(payload.product_ids), Product.is_active.is_(True))).all() if payload.product_ids else []
    data = payload.model_dump(exclude={"product_ids", "document_order", "section_order"})
    for field, value in data.items():
        setattr(item, field, value)
    item.document_order = [str(document_id) if document_id else None for document_id in payload.document_order]
    item.section_order = payload.section_order
    item.products = list(products)
    item.status = SubmittalStatus.draft
    item.error_message = None
    db.commit(); db.refresh(item)
    return item


def normalize_company_key(value: str | None) -> str:
    return "".join(ch for ch in (value or "").lower() if ch.isalnum())


def select_cover_template(templates: list[Template], submitted_by: str | None) -> Template:
    covers = [template for template in templates if template.kind == TemplateKind.cover]
    if not covers:
        raise HTTPException(409, "Missing active templates: cover")
    if len(covers) == 1:
        return covers[0]
    submitted_key = normalize_company_key(submitted_by)
    company_aliases = {
        "kineticsmiddleeastllc": ("kineticsmiddleeast", "middleeast", "kmellc", "kme"),
        "kineticsacousticstechnicalservicesllc": ("kineticsacousticstechnicalservices", "acousticstechnicalservices", "acoustictechnicalservices", "kats", "ats"),
        "kineticssoundandvibrationcontrol": ("kineticssoundandvibrationcontrol", "soundandvibrationcontrol", "ksvc", "svc"),
    }
    aliases = company_aliases.get(submitted_key, (submitted_key,))
    for template in covers:
        haystack = normalize_company_key(f"{template.name} {template.file_name}")
        if any(alias and alias in haystack for alias in aliases):
            return template
    raise HTTPException(409, f"No active cover template matched submitted by: {submitted_by or 'blank'}. Name the cover template with the company name.")


@app.post("/api/v1/submittals/{submittal_id}/attachments", status_code=201)
def add_attachment(submittal_id: str, name: str = Form(), category: str = Form("Proposed Materials"), sequence: int = Form(1000), file: UploadFile = File(), user: User = Depends(current_user), db: Session = Depends(get_db)):
    try:
        item = db.get(Submittal, uuid.UUID(submittal_id))
    except ValueError:
        item = None
    if not item or (user.role not in {Role.admin, Role.system_admin} and item.created_by_id != user.id):
        raise HTTPException(404, "Submittal not found")
    content = read_pdf(file)
    attachment = SubmittalAttachment(submittal_id=item.id, name=name, category=category, sequence=sequence, sha256=hashlib.sha256(content).hexdigest(), content=content)
    db.add(attachment); db.commit()
    return {"id": attachment.id, "name": attachment.name}


@app.post("/api/v1/submittals/{submittal_id}/generate", response_model=SubmittalOut)
def generate_submittal(submittal_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    try:
        item = db.get(Submittal, uuid.UUID(submittal_id))
    except ValueError:
        item = None
    if not item or (user.role not in {Role.admin, Role.system_admin} and item.created_by_id != user.id):
        raise HTTPException(404, "Submittal not found")
    active_template_list = db.scalars(select(Template).where(Template.is_active.is_(True))).all()
    active_templates = {t.kind: t for t in active_template_list if t.kind != TemplateKind.cover}
    missing = [kind.value for kind in (TemplateKind.cover, TemplateKind.index, TemplateKind.divider) if kind == TemplateKind.cover and not any(t.kind == TemplateKind.cover for t in active_template_list) or kind != TemplateKind.cover and kind not in active_templates]
    if missing:
        raise HTTPException(409, f"Missing active templates: {', '.join(missing)}")
    standard = db.scalars(select(Document).where(Document.kind == DocumentKind.standard, Document.is_active.is_(True)).order_by(Document.sequence)).all()
    default_section_order = ["Company Profile", "Trade License", "Proposed Materials", "Product Catalogues", "Test Reports", "Country of Origin", "Draft Warranty Certificate", "List of Previous Projects", "Previous Approvals"]
    configured_sections = [str(name).strip() for name in (item.section_order or []) if str(name).strip()]
    attachment_sections = [attachment.category.strip() for attachment in item.attachments if attachment.category and attachment.category.strip()]
    section_order = list(dict.fromkeys(configured_sections))
    section_order.extend(name for name in default_section_order if name not in section_order)
    section_order.extend(name for name in attachment_sections if name not in section_order)
    grouped: dict[str, list[tuple[int, int, FileEntry]]] = {name: [] for name in section_order}
    custom_rank = {str(document_id): rank for rank, document_id in enumerate(item.document_order or []) if document_id}
    has_custom_order = bool(custom_rank)
    insertion_order = 0
    def section_name(name: str, category: str) -> str:
        # The administrator's configured divider category is authoritative.
        # Filename matching is only a compatibility fallback for older records.
        if category in grouped:
            return category
        combined = name.lower()
        if category == "Compliance":
            return "Proposed Materials"
        rules = (("company profile", "Company Profile"), ("trade license", "Trade License"), ("proposed material", "Proposed Materials"), ("compliance", "Proposed Materials"), ("datasheet", "Product Catalogues"), ("data sheet", "Product Catalogues"), ("catalog", "Product Catalogues"), ("test", "Test Reports"), ("country of origin", "Country of Origin"), ("warranty", "Draft Warranty Certificate"), ("list of project", "List of Previous Projects"), ("project list", "List of Previous Projects"), ("previous project", "List of Previous Projects"), ("approval", "Previous Approvals"))
        return next((section for needle, section in rules if needle in combined), "Proposed Materials")
    def add_document(doc: Document) -> None:
        nonlocal insertion_order
        rank = custom_rank.get(str(doc.id), 10000 + doc.sequence) if has_custom_order else doc.sequence
        grouped[section_name(doc.name, doc.category)].append((rank, insertion_order, FileEntry(doc.file_name or doc.name, doc.content)))
        insertion_order += 1
    for doc in standard:
        add_document(doc)
    seen = set()
    for product in item.products:
        docs = [doc for doc in sorted(product.documents, key=lambda x: x.sequence) if doc.is_active and doc.id not in seen]
        seen.update(doc.id for doc in docs)
        for doc in docs:
            add_document(doc)
    for attachment in sorted(item.attachments, key=lambda x: x.sequence):
        rank = attachment.sequence if has_custom_order else attachment.sequence
        grouped[section_name(attachment.name, attachment.category)].append((rank, insertion_order, FileEntry(attachment.name, attachment.content)))
        insertion_order += 1
    sections = [Section(name, [entry for _, _, entry in sorted(grouped[name])]) for name in section_order if grouped[name]]
    values = {"project_name": item.project_name, "material_description": item.material_description, "cover_material_line": f"FOR {item.material_description.upper()}", "project_number": item.project_number or "", "client": item.client or "", "consultant": item.consultant or "", "main_contractor": item.main_contractor or "", "subcontractor": item.subcontractor or "", "submitted_by": item.submitted_by or "", "submitted_by_role": item.submitted_by_role or "", "submittal_number": item.number, "revision": item.revision, "submission_date": item.submission_date.isoformat(), "footer_reference": f"DATE: {item.submission_date.strftime('%d-%b-%Y').upper()} | {item.number}-R{item.revision}", "product_details": ", ".join(p.name for p in item.products)}
    parties = [("CLIENT", item.client), ("CONSULTANT", item.consultant), ("MAIN CONTRACTOR", item.main_contractor), ("SUB CONTRACTOR", item.subcontractor)]
    for slot, (role, name) in enumerate(((role, name) for role, name in parties if name), 1):
        values[f"party_{slot}_name"] = name or ""
        values[f"party_{slot}_role"] = role
    try:
        cover_template = select_cover_template(active_template_list, item.submitted_by)
        index_template = active_templates[TemplateKind.index]
        divider_template = active_templates[TemplateKind.divider]
        item.final_pdf = assemble(
            (cover_template.content, effective_field_map(TemplateKind.cover.value, cover_template.field_map)),
            (index_template.content, effective_field_map(TemplateKind.index.value, index_template.field_map)),
            (divider_template.content, effective_field_map(TemplateKind.divider.value, divider_template.field_map)),
            values,
            sections,
        )
        item.final_sha256 = hashlib.sha256(item.final_pdf).hexdigest()
        item.status = SubmittalStatus.generated
        item.generated_at = datetime.now(timezone.utc)
        item.error_message = None
    except Exception as exc:
        item.status = SubmittalStatus.failed
        item.error_message = str(exc)[:2000]
        db.commit()
        raise HTTPException(422, f"PDF generation failed: {exc}") from exc
    db.commit(); db.refresh(item)
    return item


@app.delete("/api/v1/submittals/{submittal_id}", status_code=204)
def delete_submittal(submittal_id: str, _: User = Depends(admin_only), db: Session = Depends(get_db)):
    try:
        item = db.get(Submittal, uuid.UUID(submittal_id))
    except ValueError:
        item = None
    if not item:
        raise HTTPException(404, "Submittal not found")
    db.delete(item)
    db.commit()
    return Response(status_code=204)


@app.get("/api/v1/submittals/{submittal_id}/download")
def download(submittal_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    try:
        item = db.get(Submittal, uuid.UUID(submittal_id))
    except ValueError:
        item = None
    if not item or not item.final_pdf or (user.role not in {Role.admin, Role.system_admin} and item.created_by_id != user.id):
        raise HTTPException(404, "Generated submittal not found")
    filename = f"{item.number}-R{item.revision}.pdf".replace("/", "-")
    return StreamingResponse(BytesIO(item.final_pdf), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}"', "ETag": item.final_sha256 or ""})

