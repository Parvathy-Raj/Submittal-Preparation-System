# Kinetics Submittal Control

Kinetics Submittal Control is a web-based document controller for preparing material submittal packages. Users enter project details, select products, upload project-specific attachments, review the package index/order, and generate one final submission-ready PDF.

The system preserves approved PDF templates and existing PDF documents. It only overlays dynamic text on cover/index/divider templates, arranges the selected documents, and merges everything into the final submittal package.

## Current version

Current version date: 07 July 2026

This version includes:

- Railway cloud deployment support.
- React frontend with modern blue/white Kinetics-themed UI.
- FastAPI backend with PostgreSQL.
- JWT authentication.
- Role-based access:
  - `system_admin`
  - `admin`
  - `user`
- System admin user management:
  - create users/admins
  - edit name/email/password/role
  - activate/deactivate accounts
- Admin product management.
- Multiple PDF uploads per product.
- Product document categories including:
  - Proposed Materials
  - Product Catalogues
  - Test Reports
  - Country of Origin
  - Draft Warranty Certificate
  - Compliance
- User-only product viewing; normal users cannot create products.
- New submittal form with:
  - project details
  - material/submittal title
  - client/consultant/main contractor/subcontractor
  - submitted-by company dropdown
  - product selection from database
  - project-specific attachment uploads by index/divider section
  - custom index/divider sections
- Editable package `INDEX` before generation.
- Divider/index order rearrangement.
- Document order rearrangement inside each divider.
- Generated index page follows the selected divider order.
- Index page uses the approved table style:
  - `TABLE OF CONTENTS`
  - `SR NO.`
  - no page numbers
  - no individual document list
- Draft/failed submittals can be reopened and edited.
- Generated/completed submittals are counted in analytics; drafts/failed records are excluded.
- Interactive admin analytics dashboard with user-wise bar chart and time filters.
- Browser back button works between app pages instead of logging the user out.
- Broken UI encoding characters fixed.
- Railway missing-font crash fixed.
- Cover page fallback layout tuned for the approved Kinetics cover template.
- Existing company/product/project PDFs remain unchanged.

## Live Railway deployment

The system has been prepared for Railway deployment using separate services:

1. PostgreSQL database
2. Backend API
3. Frontend web app

Railway-specific Dockerfiles:

```text
Dockerfile.backend
Dockerfile.frontend
```

Current Railway URL examples used during deployment:

```text
Backend:  https://backend-production-8fad.up.railway.app
Frontend: https://frontend-production-d60c0.up.railway.app
```

These URLs may change if Railway services/domains are regenerated.

## Architecture

```text
.
|-- backend/
|   |-- app/
|   |   |-- main.py          # FastAPI routes and generation workflow
|   |   |-- models.py        # SQLAlchemy models
|   |   |-- schemas.py       # Pydantic schemas
|   |   |-- pdf_engine.py    # Template overlay and PDF assembly
|   |   |-- security.py      # JWT auth and role checks
|   |   |-- database.py      # Database engine/session
|   |   `-- config.py        # Environment settings
|   `-- tests/
|-- frontend/
|   |-- src/
|   |   |-- main.tsx         # React application
|   |   |-- api.ts           # API client
|   |   |-- styles.css       # Base UI styles
|   |   |-- management.css   # Management UI styles
|   |   `-- kinetics.css     # Kinetics theme
|   `-- public/
|       |-- kinetics-logo.png
|       `-- favicon.jpg
|-- docs/
|   |-- Deployment_Options_Comparison.docx
|   |-- Deployment_Options_Comparison.md
|   `-- Railway_Deployment_Guide.md
|-- Dockerfile.backend
|-- Dockerfile.frontend
|-- docker-compose.yml
`-- README.md
```

Technology stack:

- Frontend: React, TypeScript, Vite, Nginx
- Backend: Python FastAPI, SQLAlchemy 2, Pydantic
- Database: PostgreSQL
- PDF processing: pypdf and ReportLab
- Local runtime: Docker Compose
- Cloud deployment: Railway

## Local quick start

### 1. Install Docker Desktop

Install Docker Desktop for Windows and make sure Docker Engine is running.

Check from PowerShell:

```powershell
docker version
docker compose version
```

### 2. Create `.env`

Create `.env` in the project root:

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

For production, change:

- `POSTGRES_PASSWORD`
- `JWT_SECRET`
- `BOOTSTRAP_ADMIN_PASSWORD`

### 3. Start locally

From the project root:

```powershell
docker compose up -d --build
```

Open:

- Web app: [http://localhost:8080](http://localhost:8080)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

Default local bootstrap admin:

```text
Email: admin@example.com
Password: ChangeMe123!
```

Note: changing `BOOTSTRAP_ADMIN_PASSWORD` after the user already exists does not reset the existing password.

## Railway deployment

Railway deployment uses three services.

### PostgreSQL service

Create a Railway PostgreSQL database service.

The backend should use the database variable:

```env
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

If the Railway database service has a different name, update `Postgres` accordingly.

### Backend service variables

Use the same GitHub repository and set:

```env
RAILWAY_DOCKERFILE_PATH=Dockerfile.backend
DATABASE_URL=${{Postgres.DATABASE_URL}}
JWT_SECRET=<long-random-secret>
BOOTSTRAP_ADMIN_EMAIL=<admin-email>
BOOTSTRAP_ADMIN_PASSWORD=<temporary-admin-password>
JWT_MINUTES=480
MAX_UPLOAD_MB=100
CORS_ORIGINS=http://localhost:8080,https://your-frontend-domain.up.railway.app
CORS_ORIGIN_REGEX=https://.*\.railway\.app
```

Backend health check:

```text
https://your-backend-domain.up.railway.app/health
```

Expected response:

```json
{"status":"ok"}
```

### Frontend service variables

Use the same GitHub repository and set:

```env
RAILWAY_DOCKERFILE_PATH=Dockerfile.frontend
VITE_API_URL=https://your-backend-domain.up.railway.app/api/v1
```

When generating the frontend public domain, use port:

```text
8080
```

### Railway notes

- Keep the GitHub repository private.
- Do not delete the Railway PostgreSQL service; it contains deployed data.
- Uploaded PDFs/templates are stored in PostgreSQL.
- Configure backups before using real company data.
- After code changes, push to GitHub and redeploy the affected Railway service.
- Frontend changes require frontend redeploy.
- Backend/API/PDF changes require backend redeploy.

More details are in:

[docs/Railway_Deployment_Guide.md](docs/Railway_Deployment_Guide.md)

## User roles

### System admin

System admin can:

- Manage all users and admins.
- Change names, emails, passwords, roles, and active status.
- Access admin features.
- View analytics.

Safeguards:

- A system admin cannot deactivate their own account.
- A system admin cannot remove their own system admin role.

### Admin

Admin can:

- Upload approved templates.
- Upload controlled standard documents.
- Create and edit products.
- Upload multiple product PDFs.
- Map product documents to product records.
- View products/documents/templates.
- Create and generate submittals.
- View analytics.

### User

User can:

- View available products and product document details.
- Create new submittals.
- Select products.
- Upload project-specific attachments.
- Review/rearrange package index/order.
- Generate/download final PDFs.

User cannot:

- Create products.
- Manage templates.
- Manage controlled documents.
- Manage users.

## Admin setup workflow

Before users generate submittals, an admin/system admin should:

1. Upload active templates:
   - `cover`
   - `index`
   - `divider`
2. Upload standard company documents:
   - Company Profile
   - Trade License
   - List of Previous Projects
   - Previous Approvals
   - other company standard documents
3. Create products in `Product list`.
4. Upload one or more PDFs for each product by document type.
5. Create user accounts.
6. Test a sample submittal generation.

## New submittal workflow

1. Open `New submittal`.
2. Enter project information:
   - Submittal number
   - Revision
   - Project name
   - Material/submittal title
   - Project number
   - Client
   - Consultant
   - Main contractor
   - Subcontractor
   - Submitted by
   - Submitted by role
   - Submission date
3. Select products from the product dropdown.
4. System fetches matching product documents.
5. Upload optional project-specific PDFs by divider section.
6. Add custom index/divider sections if required.
7. Open `INDEX`.
8. Rearrange divider order and document order.
9. Generate PDF.
10. Download final package from dashboard.

## Draft editing

When a submittal remains in `draft` or `failed` status:

- It appears in Recent Submittals with an `Edit` button.
- Clicking `Edit` reopens the saved submittal in the New Submittal form.
- The form preloads project information, selected products, section order, and document order.
- The user can update and generate again.

Generated submittals cannot be edited directly. Create a new revision instead.

## Submitted by options

The `Submitted by` dropdown includes:

- Kinetics Middle East LLC
- Kinetics Acoustic Services LLC
- Kinetics Sound and Vibration Control
- Kinetics Metal Construction Industries LLC

## Package sections

Default divider/index sections:

1. Company Profile
2. Trade License
3. Proposed Materials
4. Product Catalogues
5. Test Reports
6. Country of Origin
7. Draft Warranty Certificate
8. List of Previous Projects
9. Previous Approvals

Users can add custom sections during submittal creation.

## Dynamic index behavior

The generated index page uses the approved index PDF template as the background/base.

The system overlays a table with:

- `TABLE OF CONTENTS`
- `SR NO.`
- one row per divider section
- uppercase divider names
- serial numbers only
- no page numbers
- no individual document list

The generated index follows the rearranged package order.

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

- Approved template PDFs remain the base design.
- Dynamic fields are overlaid on cover/index/divider pages.
- Existing document PDFs are never edited.
- Original document quality is preserved.
- Original page sizes are preserved.
- Standard documents are added from the controlled document library.
- Product documents are fetched from product mappings.
- Project attachments are inserted under selected divider sections.
- Final package follows the reviewed index/order.

## Template field maps

Templates may include JSON field maps. Coordinates are PDF points from the bottom-left corner.

If a template field map is empty (`{}`), the backend uses built-in Kinetics fallback maps for:

- cover
- index
- divider

These fallback maps are tuned to the approved Kinetics cover/index/divider templates used during deployment.

Example cover field:

```json
{
  "project_name": {
    "page": 0,
    "x": 306,
    "y": 527,
    "font": "Calibri-Light",
    "font_size": 56,
    "align": "center",
    "color": "#FF0000",
    "max_width": 500
  }
}
```

Common supported field properties:

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

Templates may also use `__masks__` to cover old/sample template text before drawing dynamic values.

Example:

```json
{
  "__masks__": [
    {
      "page": 0,
      "x": 105,
      "y": 100,
      "width": 405,
      "height": 585,
      "color": "#FFFFFF"
    }
  ]
}
```

## Analytics dashboard

Admins/system admins can view analytics in Overview.

Analytics includes:

- user-wise submittal count bar chart
- month/year/date-range/all filters
- selected user detail view
- completed/generated submittal counts only

Draft and failed submittals are not counted in the report chart.

## Browser navigation

The frontend uses hash-based page navigation:

```text
#dashboard
#new
#products
#documents
#templates
#users
```

Browser Back/Forward moves between app pages.

Logout happens only when the logout button is clicked.

## Local logo assets

Logo and favicon are served locally:

```text
frontend/public/kinetics-logo.png
frontend/public/favicon.jpg
```

Local logo URL:

[http://localhost:8080/kinetics-logo.png](http://localhost:8080/kinetics-logo.png)

If the logo does not update, hard refresh:

```text
Ctrl + Shift + R
```

## Useful Docker commands

Start/rebuild all services:

```powershell
docker compose up -d --build
```

Rebuild frontend:

```powershell
docker compose up -d --build web
```

Rebuild backend:

```powershell
docker compose up -d --build api
```

Check services:

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

Stop services and delete local DB volume:

```powershell
docker compose down -v
```

Use `down -v` carefully because it deletes local PostgreSQL data.

## Development without Docker

Docker Compose is recommended. Local development is also possible.

### Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend dev server:

[http://localhost:5173](http://localhost:5173)

## Tests and checks

Run backend tests:

```powershell
docker compose exec api pytest
```

Build frontend:

```powershell
docker compose build web
```

Build Railway backend image:

```powershell
docker build -f Dockerfile.backend -t submittal-railway-backend-test .
```

Build Railway frontend image:

```powershell
docker build -f Dockerfile.frontend -t submittal-railway-frontend-test .
```

## Troubleshooting

### PowerShell opens in `C:\Windows\System32`

Go to the project folder:

```powershell
cd "C:\Users\parvathy\Documents\Submittal Preparation System"
```

### Docker is not recognized

Install Docker Desktop and restart PowerShell.

Check:

```powershell
docker version
```

### Cannot connect to Docker daemon

Open Docker Desktop and wait until Docker Engine is running.

### Missing active templates

Error:

```text
Missing active templates: cover, index, divider
```

Fix:

1. Sign in as admin/system admin.
2. Go to `Templates`.
3. Upload one active template for:
   - `cover`
   - `index`
   - `divider`

### PDF cover/index/divider not customized

Check:

- active templates exist
- template kind is correct
- backend was redeployed after PDF engine changes
- generated PDF is new, not an old stored output

If templates use `{}` as field map, the built-in fallback maps are used.

### Railway backend Application Not Found

Usually the old Railway domain was replaced or the service was deleted.

Use the current backend service domain from Railway.

### Railway frontend Application failed to respond

Check frontend public domain port:

```text
8080
```

Check frontend variable:

```env
VITE_API_URL=https://your-backend-domain.up.railway.app/api/v1
```

### Login says Request failed

Check:

- backend is online
- `VITE_API_URL` points to backend `/api/v1`
- backend `CORS_ORIGINS` includes the frontend URL
- account is active
- password is correct

### Bootstrap admin password does not work

The bootstrap password is only used when the account is first created.

If the account already exists, changing `BOOTSTRAP_ADMIN_PASSWORD` does not reset it.

Reset the password through system admin user management or directly in the database.

### Broken or corrupted UI text

This can be caused by encoding corruption in UI strings.

The current version uses plain safe characters such as `-` and `...`.

If this appears again, search the frontend source for mojibake/corrupted character sequences and replace them with plain text.

### Duplicate product codes

Product codes may repeat because manufacturer/product document codes can be shared by variants.

### Duplicate document names

Documents with the same name/revision can exist for different products.

## Production notes

- Keep Railway/GitHub access restricted.
- Keep the GitHub repository private.
- Use a strong `JWT_SECRET`.
- Change temporary bootstrap/admin passwords.
- Create named admin accounts instead of sharing one admin login.
- Configure PostgreSQL backups.
- Monitor Railway usage/billing.
- Confirm upload limits before large PDF usage.
- Store only approved documents/templates.
- Do not delete Railway PostgreSQL service unless data is intentionally being removed.
- Consider antivirus/malware scanning for uploaded files before wider rollout.

## Data storage

PostgreSQL stores:

- users
- products
- documents
- templates
- product-document mappings
- submittal records
- project attachments
- generated final PDFs

PDF/template binaries are stored in PostgreSQL `BYTEA` columns.

## Important operating note

Generated PDFs are stored as final output files. If template logic, index order, or cover layout changes later, old generated PDFs do not update automatically.

Regenerate the submittal to produce a new final PDF with the latest behavior.

