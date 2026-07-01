# Kinetics Submittal Control

Kinetics Submittal Control is a web application for preparing submission-ready material submittal packages from approved templates and controlled PDF documents.

The system acts like a digital document controller: users enter project information, select products, upload project-specific attachments, review the package index/order, and generate one final merged PDF. Approved template PDFs and source document PDFs are preserved; the system only overlays dynamic text on templates and arranges/merges existing PDFs.

## Current version highlights

- Kinetics-branded React UI with local logo and favicon assets.
- Admin and user role separation.
- PostgreSQL storage for metadata and PDF/template binaries.
- Approved cover, index, and divider PDF templates.
- Dynamic cover page fields for project, material/submittal title, client/consultant/main contractor/subcontractor/submitted by, revision, date, and submittal number.
- Product list managed by admin.
- Multiple product document uploads per product.
- Product-to-document mapping.
- Product dropdown in new submittal form.
- Project-specific attachments by divider section.
- Editable package `INDEX` before generation.
- Divider/index order can be rearranged before generating.
- Final index page follows the rearranged divider order.
- Index page renders in the approved table style: `TABLE OF CONTENTS` and `SR NO.`
- Existing company, product, and project PDFs are appended unchanged.

## Architecture

```text
.
|-- backend/
|   |-- app/
|   |   |-- main.py          # FastAPI routes and generation workflow
|   |   |-- models.py        # SQLAlchemy models
|   |   |-- schemas.py       # Pydantic request/response schemas
|   |   |-- pdf_engine.py    # Template overlay and PDF assembly
|   |   |-- security.py      # JWT auth and role checks
|   |   |-- database.py      # Database session/engine
|   |   `-- config.py        # Environment settings
|   `-- tests/
|-- frontend/
|   |-- src/
|   |   |-- main.tsx         # React application
|   |   |-- api.ts           # API client
|   |   |-- styles.css       # Base UI styles
|   |   |-- management.css   # Admin/product/submittal UI styles
|   |   `-- kinetics.css     # Kinetics-branded theme
|   `-- public/
|       |-- kinetics-logo.png
|       `-- favicon.jpg
|-- docker-compose.yml
`-- README.md
```

Technology stack:

- Frontend: React, TypeScript, Vite, Nginx
- Backend: Python FastAPI, SQLAlchemy 2, Pydantic
- Database: PostgreSQL
- PDF processing: pypdf and ReportLab
- Deployment/dev runtime: Docker Compose

## Quick start

### 1. Install Docker Desktop

Install Docker Desktop for Windows and make sure Docker Engine is running.

In PowerShell, check:

```powershell
docker version
docker compose version
```

If Docker says it cannot connect to the Docker API or Docker daemon, open Docker Desktop and wait until it says the engine is running.

### 2. Create `.env`

Create a `.env` file in the project root:

```env
POSTGRES_DB=submittals
POSTGRES_USER=submittals
POSTGRES_PASSWORD=change-me
DATABASE_URL=postgresql+psycopg://submittals:change-me@db:5432/submittals
JWT_SECRET=replace-with-a-long-random-secret
BOOTSTRAP_ADMIN_EMAIL=admin@example.com
BOOTSTRAP_ADMIN_PASSWORD=ChangeMe123!
MAX_UPLOAD_MB=100
VITE_API_URL=http://localhost:8000/api/v1
```

For production, change `POSTGRES_PASSWORD`, `JWT_SECRET`, and the bootstrap admin password.

### 3. Start the application

From the project root:

```powershell
docker compose up -d --build
```

Open:

- Web app: [http://localhost:8080](http://localhost:8080)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

Default bootstrap admin:

```text
Email: admin@example.com
Password: ChangeMe123!
```

The bootstrap admin is created automatically if it does not already exist.

## User roles

### Admin

Admins can:

- Upload and replace approved templates.
- Upload controlled standard documents.
- Create product records.
- Upload multiple PDF files for each product.
- Assign document types/categories to product files.
- Edit product details and mapped files.
- Manage users.
- View, generate, and download submittals.

### User

Users can:

- View available products and product document details.
- Create new submittals.
- Select products from the product list.
- Upload project-specific attachments.
- Review and rearrange the package index/order before generation.
- Generate and download final submittal PDFs.

Users cannot create products or manage templates/documents.

## Admin setup workflow

Before users generate submittals, an admin should complete this setup:

1. Sign in as admin.
2. Upload active templates:
   - `cover`
   - `index`
   - `divider`
3. Upload standard company documents, such as:
   - Company Profile
   - Trade License
   - List of Previous Projects
   - Previous Approvals
4. Create products in `Product list`.
5. For each product, upload one or more product PDFs by type, such as:
   - Proposed Materials
   - Product Catalogues
   - Test Reports
   - Country of Origin
   - Draft Warranty Certificate
   - Compliance
6. Add user accounts if needed.

## New submittal workflow

1. User opens `New submittal`.
2. User enters project information:
   - Submittal number
   - Revision
   - Project name
   - Material / submittal title
   - Project number
   - Client
   - Consultant
   - Main contractor
   - Subcontractor
   - Submitted by
   - Submitted by role
   - Submission date
3. User selects products from the product dropdown.
4. System automatically collects mapped product documents.
5. User uploads optional project-specific PDFs by divider section.
6. User opens `INDEX`.
7. User reviews and rearranges divider order and document order.
8. User clicks `Create and generate PDF`.
9. System generates the final PDF.
10. User downloads the package from the dashboard.

## Submitted by options

The `Submitted by` field is a dropdown with:

- Kinetics Middle East LLC
- Kinetics Acoustic Services LLC
- Kinetics Sound and Vibration Control
- Kinetics Metal Construction Industries LLC

## Document sections

The package currently supports these divider sections:

1. Company Profile
2. Trade License
3. Proposed Materials
4. Product Catalogues
5. Test Reports
6. Country of Origin
7. Draft Warranty Certificate
8. List of Previous Projects
9. Previous Approvals

The user can rearrange these before generation in the `INDEX` review section.

## Dynamic index behavior

The index page uses the approved index PDF template as its background/base.

The system overlays a dynamic table matching the template style:

- Left heading: `TABLE OF CONTENTS`
- Right heading: `SR NO.`
- One row per divider section
- Divider names in uppercase
- Serial numbers in the right column
- No document list
- No page numbers

If the user rearranges the dividers in the `INDEX` review section, the generated index table follows that same order.

Example:

```text
TABLE OF CONTENTS                         SR NO.
COMPANY PROFILE                              1
TRADE LICENSE                                2
PROPOSED MATERIALS                           3
PRODUCT CATALOGUES                           4
TEST REPORTS                                 5
COUNTRY OF ORIGIN                            6
DRAFT WARRANTY CERTIFICATE                   7
LIST OF PREVIOUS PROJECTS                    8
PREVIOUS APPROVALS                           9
```

## PDF generation rules

The PDF engine follows these rules:

- Approved template PDFs are used as-is.
- Dynamic text is added as an overlay.
- Existing document PDFs are never edited.
- Original document quality is preserved.
- Original page sizes/media boxes are preserved.
- Product documents are fetched from product mappings.
- Project-specific attachments are inserted into their selected divider sections.
- Documents are merged according to the reviewed package order.

## Template field maps

Templates can include a JSON field map. Coordinates are PDF points from the bottom-left corner.

Example cover field:

```json
{
  "project_name": {
    "page": 0,
    "x": 306,
    "y": 535,
    "font": "Calibri-Light",
    "font_size": 60,
    "align": "center",
    "color": "#FF0000",
    "max_width": 430
  }
}
```

Supported common properties:

- `page`
- `x`
- `y`
- `font`
- `font_size`
- `color`
- `align`
- `max_width`
- `literal`
- `underline`
- `underline_width`

Templates may also use `__masks__` to cover fixed text areas before dynamic text is drawn.

Example:

```json
{
  "__masks__": [
    {
      "page": 0,
      "x": 82,
      "y": 515,
      "width": 448,
      "height": 78,
      "color": "#FFFFFF"
    }
  ]
}
```

The active index template can have an empty field map. In that case, the backend uses the built-in Kinetics table overlay style.

## Local logo assets

The app serves the Kinetics logo locally from:

```text
frontend/public/kinetics-logo.png
frontend/public/favicon.jpg
```

This avoids missing logos in Chrome due to external image blocking or network issues.

If the logo does not appear after rebuilding, hard refresh Chrome:

```text
Ctrl + Shift + R
```

You can also verify the logo directly:

[http://localhost:8080/kinetics-logo.png](http://localhost:8080/kinetics-logo.png)

## Useful Docker commands

Start/rebuild all services:

```powershell
docker compose up -d --build
```

Rebuild only frontend:

```powershell
docker compose up -d --build web
```

Rebuild only backend:

```powershell
docker compose up -d --build api
```

Check service status:

```powershell
docker compose ps
```

View backend logs:

```powershell
docker compose logs api --tail 120
```

Stop services:

```powershell
docker compose down
```

Stop services and remove database volume:

```powershell
docker compose down -v
```

Use `down -v` carefully because it deletes the PostgreSQL data volume.

## Development without Docker

Docker Compose is the recommended workflow, but local development is possible.

### Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The backend expects PostgreSQL to be available and `DATABASE_URL` to be set.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend dev server usually runs at:

[http://localhost:5173](http://localhost:5173)

## Tests and checks

Run backend tests inside the API container:

```powershell
docker compose exec api pytest
```

Run a Python syntax check:

```powershell
docker compose exec api python -m py_compile app/pdf_engine.py app/main.py
```

Build frontend:

```powershell
docker compose up -d --build web
```

## Troubleshooting

### PowerShell opens in `C:\Windows\System32`

That is normal when PowerShell is opened as administrator or from some shortcuts.

Go to the project folder:

```powershell
cd "C:\Users\parvathy\Documents\Submittal Preparation System"
```

Then run Docker commands from there.

### `docker` is not recognized

Docker Desktop is not installed or its CLI is not in PATH.

Install Docker Desktop, restart PowerShell, and check:

```powershell
docker version
```

### Cannot connect to Docker API / daemon

Open Docker Desktop and wait until Docker Engine has started.

Then retry:

```powershell
docker compose ps
```

### Missing active templates

Error:

```text
Missing active templates: cover, index, divider
```

Fix:

1. Sign in as admin.
2. Go to `Templates`.
3. Upload one active template for each kind:
   - `cover`
   - `index`
   - `divider`

### Logo not visible in Chrome

Hard refresh:

```text
Ctrl + Shift + R
```

Verify:

[http://localhost:8080/kinetics-logo.png](http://localhost:8080/kinetics-logo.png)

### Duplicate product code

Product codes are allowed to repeat because manufacturer document codes may be shared by multiple variants.

### Duplicate document names

Different products may use documents with the same display name and revision, for example `COMPLIANCE 1` revision `0`.

The system allows this. Identical PDFs are reused by SHA-256 hash to avoid duplicate binary storage.

## Production notes

- Change all secrets before deployment.
- Put the API behind HTTPS/TLS.
- Use a strong `JWT_SECRET`.
- Rotate or disable the bootstrap admin after creating named admin accounts.
- Configure PostgreSQL backups.
- Confirm storage growth, because PDF binaries are stored in PostgreSQL.
- Add antivirus/malware scanning for uploads at the ingress boundary.
- Set reverse proxy upload limits to match `MAX_UPLOAD_MB`.
- For high-volume usage, move PDF generation to a background worker queue.
- Keep approved templates under document control and revise them deliberately.

## Data storage

PostgreSQL stores:

- Users
- Products
- Documents
- Templates
- Product-document mappings
- Submittal records
- Project attachments
- Generated final PDFs

PDF and template binaries are stored in database `BYTEA` columns, matching the project requirement.

## Important operating note

Generated PDFs are stored as final outputs. If template logic or ordering behavior changes, old generated PDFs do not update automatically. Regenerate the submittal to produce a new final PDF with the latest behavior.
