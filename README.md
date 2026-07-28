# Kinetics Submittal Control

Kinetics Submittal Control is a web-based submittal preparation system for assembling approved templates, company documents, product documents, and project-specific attachments into one final submission-ready PDF.

The application acts like a digital document controller. Users enter project information, select products, upload attachments, review the index/order, save drafts when needed, and generate the final PDF package.

## Latest version

Version date: 24 July 2026

Latest updates include:

- Clean blue/white Kinetics-themed interface.
- Cleaner New Submittal form layout.
- Overview dashboard is available to admin, system admin, and user profiles.
- Main dashboard charts:
  - Submittals by employee
  - Submittals by status
  - Monthly submittal trend
- Interactive dashboard drill-down:
  - click an employee to view their submittals
  - click a status to view matching submittals
- Save Draft workflow in New Submittal.
- Preview PDF workflow before final generation.
- Warning popup when leaving an unfinished submittal.
- Draft/In progress submittals can be reopened and continued.
- Generated submittals can be downloaded by any signed-in user.
- Draft and failed submittals can be edited.
- Completed/generated submittals can be reopened by the owner/admin for customer comment revisions.
- Users can edit/delete their own submittals.
- Admins/system admins can edit/delete all submittals.
- Product list supports multiple documents per product.
- Product documents are fetched automatically during submittal generation.
- Product documents can use fixed or custom index/document types.
- Company-specific cover, index, and divider templates are supported.
- Material/submittal title uses a dropdown with custom typing support.
- Client/consultant/contractor title labels can be customized per submittal.
- Custom index/divider sections are supported.
- Index order and divider order can be rearranged before generation.
- Cover, index, and divider pages use approved templates as the base design.
- Cover page text uses auto-layout for long project names and dynamic fields.
- Existing PDF documents remain unchanged.

## Technology stack

- Frontend: React, TypeScript, Vite, Nginx
- Backend: Python FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy
- Auth: JWT
- PDF processing: ReportLab and pypdf
- Local runtime: Docker Compose
- Cloud deployment: Railway

## Current Railway deployment

The app is deployed on Railway using separate services:

1. PostgreSQL database
2. Backend API
3. Frontend web app

Current deployment URLs used during setup:

```text
Backend:  https://backend-production-8fad.up.railway.app
Frontend: https://frontend-production-d60c0.up.railway.app
```

These URLs may change if Railway domains are regenerated.

## Project structure

```text
.
|-- backend/
|   |-- app/
|   |   |-- main.py          # FastAPI routes and generation workflow
|   |   |-- models.py        # SQLAlchemy database models
|   |   |-- schemas.py       # API schemas
|   |   |-- pdf_engine.py    # Template overlay and PDF assembly
|   |   |-- security.py      # Authentication and role checks
|   |   |-- database.py      # Database connection/session
|   |   `-- config.py        # Environment configuration
|   `-- requirements.txt
|-- frontend/
|   |-- src/
|   |   |-- main.tsx         # React app
|   |   |-- api.ts           # API client
|   |   |-- styles.css       # Base styles
|   |   |-- management.css   # Management page styles
|   |   `-- kinetics.css     # Kinetics theme and dashboard styles
|   |-- public/
|   |   |-- kinetics-logo.png
|   |   `-- favicon.jpg
|   |-- Dockerfile
|   |-- nginx.conf
|   `-- package.json
|-- docs/
|-- Dockerfile.backend
|-- Dockerfile.frontend
|-- docker-compose.yml
|-- .env.example
`-- README.md
```

## User roles

### System admin

System admin can:

- Manage all users.
- Create admins and users.
- Edit name, email, password, role, and active status.
- Activate/deactivate accounts.
- Access admin features.
- View dashboard analytics.

Safety rules:

- A system admin cannot deactivate their own account.
- A system admin cannot remove their own system admin role.

### Admin

Admin can:

- Upload approved templates.
- Upload standard company documents.
- Create and edit products.
- Upload multiple product PDFs.
- Map documents to products.
- Create submittals.
- Generate final PDFs.
- View dashboard analytics.

### User

User can:

- View the full overview dashboard and analytics.
- View available products.
- Create submittals.
- Select products.
- Upload project-specific attachments.
- Add custom index sections.
- Rearrange package order.
- Save drafts.
- Generate PDFs.
- Download any generated submittal.
- Edit/delete their own submittals.

User cannot:

- Manage users.
- Upload templates.
- Manage controlled documents.
- Create/edit products.
- Edit/delete other users' submittals.

## Local setup

### 1. Open the project folder

PowerShell may open in `C:\Windows\System32`. Go to the project folder first:

```powershell
cd "C:\Users\parvathy\Documents\Submittal Preparation System"
```

### 2. Create `.env`

Copy `.env.example` to `.env`, or create `.env` with:

```env
POSTGRES_DB=submittals
POSTGRES_USER=submittals
POSTGRES_PASSWORD=change-me
DATABASE_URL=postgresql+psycopg://submittals:change-me@db:5432/submittals
JWT_SECRET=replace-with-a-long-random-secret
BOOTSTRAP_ADMIN_EMAIL=admin@example.com
BOOTSTRAP_ADMIN_PASSWORD=ChangeMe123!
MAX_UPLOAD_MB=100
MAX_PACKAGE_SOURCE_MB=60
VITE_API_URL=http://localhost:8000/api/v1
```

### 3. Start locally

Make sure Docker Desktop is running, then:

```powershell
docker compose up -d --build
```

Open:

- Frontend: [http://localhost:8080](http://localhost:8080)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

Default local admin:

```text
Email: admin@example.com
Password: ChangeMe123!
```

Note: changing `BOOTSTRAP_ADMIN_PASSWORD` after the admin already exists does not reset the existing password.

## Railway deployment

Railway uses the GitHub repository and three services.

### PostgreSQL service

Create a Railway PostgreSQL service.

Use its database URL in the backend:

```env
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

If your database service has a different name, replace `Postgres` with that service name.

### Backend service

Backend service variables:

```env
RAILWAY_DOCKERFILE_PATH=Dockerfile.backend
DATABASE_URL=${{Postgres.DATABASE_URL}}
JWT_SECRET=<long-random-secret>
BOOTSTRAP_ADMIN_EMAIL=<admin-email>
BOOTSTRAP_ADMIN_PASSWORD=<temporary-admin-password>
JWT_MINUTES=480
MAX_UPLOAD_MB=100
MAX_PACKAGE_SOURCE_MB=60
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

### Frontend service

Frontend service variables:

```env
RAILWAY_DOCKERFILE_PATH=Dockerfile.frontend
VITE_API_URL=https://your-backend-domain.up.railway.app/api/v1
```

When generating the frontend public domain, use port:

```text
8080
```

### Deploying changes to Railway

After code changes:

1. Commit changes in GitHub Desktop.
2. Push to GitHub.
3. Railway will redeploy automatically.

Frontend-only changes usually require only the frontend service to redeploy.

Backend/API/PDF changes require the backend service to redeploy.

## Admin setup workflow

Before live users generate submittals:

1. Sign in as system admin/admin.
2. Upload approved templates:
   - cover, index, and divider for Kinetics Middle East LLC
   - cover, index, and divider for Kinetics Acoustics Technical Services LLC
   - cover, index, and divider for Kinetics Sound and Vibration Control
   - include the company name in each template name/file name
3. Upload standard company documents:
   - Company Profile
   - Trade License
   - List of Previous Projects
   - Previous Approvals
   - other standard documents
4. Create products in Product list.
5. Upload product PDFs by document type.
6. Create users/admins.
7. Test a sample submittal.

## Product document management

Admins can create products and upload multiple PDFs for each product.

Supported product document categories include:

- Proposed Materials
- Product Catalogues
- Test Reports
- Country of Origin
- Draft Warranty Certificate
- General Compliance Statement

Admins can also add custom product document/index types while creating or editing a product.

Examples:

- Acoustic Calculation
- Method Statement
- Technical Compliance
- Installation Manual

Custom product document types are carried into New Submittal as their own index/divider sections when that product is selected.

During submittal generation, selected products automatically bring their mapped documents into the correct divider sections.

## New submittal workflow

1. Open `New submittal`.
2. Enter project information.
3. Select products from the product dropdown.
4. Upload project-specific attachments if required.
5. Add custom index/divider sections if required.
6. Open `INDEX`.
7. Rearrange divider/index order if required.
8. Rearrange documents inside each divider if required.
9. Save as draft, preview the PDF, or generate final PDF.

Project information includes:

- Submittal number
- Revision
- Project name
- Material/submittal title selected from a dropdown or typed manually
- QTN REF
- Client
- Client title
- Consultant
- Consultant title
- Main contractor
- Main contractor title
- Subcontractor
- Subcontractor title
- Submitted by
- Submitted by role
- Submission date

Default party titles are:

- CLIENT
- CONSULTANT
- MAIN CONTRACTOR
- SUB CONTRACTOR

These can be changed per submittal when a client requires different wording.

Standard material/submittal options include:

- ACOUSTIC TREATMENT
- ACOUSTIC LAGGING
- ACOUSTIC LOUVERS
- ACOUSTIC UNDERLAY
- FLOATING FLOOR SYSTEM
- DIELECTRIC UNIONS
- DISMANTLING JOINTS
- ENGINEERING SERVICES
- FLEXIBLE HOSE CONNECTORS
- INERTIA BASES
- RUBBER FLEXIBLE CONNECTORS
- SEISMIC RESTRAINTS
- SOUND ATTENUATORS
- ST. STEEL EXPANSION JOINTS
- ST. STEEL FLEXIBLE CONNECTORS
- VIBRATION ISOLATORS

Users can type a custom value if the required material/submittal title is not in the list.

## Save draft workflow

New Submittal includes a `Save draft` button.

If a user starts a submittal and tries to leave the page, the system shows a popup:

- Stay here
- Leave without saving
- Save draft

Saved drafts appear in the submittal list as draft/in progress and can be reopened using `Edit`.

Drafts preserve:

- project information
- selected products
- selected section order
- selected document order
- uploaded project attachments saved before leaving

Generated submittals can also be reopened with `Edit`. After changes are saved, the submittal moves back to draft/in-progress until the revised PDF is generated again.

## Preview PDF workflow

New Submittal includes a `Preview PDF` button.

Preview PDF:

- saves the current package as a draft first
- opens a preview PDF in a new browser tab
- uses the same assembly engine as final generation
- does not mark the submittal as generated
- allows users to review cover, index, divider order, and attached documents before final generation

After previewing, users can continue editing or click generate to create the final PDF.

## Submitted by options

The Submitted by dropdown includes:

- Kinetics Middle East LLC
- Kinetics Acoustics Technical Services LLC
- Kinetics Sound and Vibration Control

The selected company controls which approved cover, index, and divider templates are used in the final PDF.

## Company-specific templates

The system supports separate cover, index, and divider templates for each `Submitted by` company.

Upload each company template in Templates using the correct kind:

- `cover`
- `index`
- `divider`

Include the company name in each template name or file name.

Recommended template names:

- Kinetics Middle East LLC - Cover
- Kinetics Middle East LLC - Index
- Kinetics Middle East LLC - Divider
- Kinetics Acoustics Technical Services LLC - Cover
- Kinetics Acoustics Technical Services LLC - Index
- Kinetics Acoustics Technical Services LLC - Divider
- Kinetics Sound and Vibration Control - Cover
- Kinetics Sound and Vibration Control - Index
- Kinetics Sound and Vibration Control - Divider

When generating a submittal, the backend matches the selected `Submitted by` company to the active template name or file name for each template kind.

The match is strict. If the selected company does not have a matching active cover, index, or divider template, generation/preview stops with a clear template-matching error.

## Default index/divider sections

Default sections:

1. Company Profile
2. Trade License
3. Proposed Materials
4. General Compliance Statement
5. Product Catalogues
6. Test Reports
7. Country of Origin
8. Draft Warranty Certificate
9. List of Previous Projects
10. Previous Approvals

Users can also add custom sections for client-specific requirements.

## Dynamic index behavior

The generated index page uses the approved index PDF template as the base design.

The system overlays a table with:

- `TABLE OF CONTENTS`
- `SR NO.`
- one row per divider/index section
- serial numbers only
- no page numbers
- no individual document list

If the package order is rearranged, the index page follows the rearranged order.

## PDF generation rules

- The selected company's approved cover template remains the base design.
- The selected company's approved index/divider templates remain the base design.
- Only dynamic text fields are overlaid.
- Cover text is auto-laid out to reduce overlap and improve long project-name readability.
- Existing PDF documents are not edited.
- Original PDF quality is preserved.
- Original page sizes are preserved.
- Standard documents are pulled from the controlled library.
- Product documents are pulled from product mappings.
- Project attachments are inserted under selected divider sections.
- Final PDF follows the reviewed index/order.

## Template field maps

Templates can include JSON field maps for exact text placement.

Coordinates are PDF points from the bottom-left corner.

If a template field map is empty (`{}`), the backend uses built-in Kinetics fallback maps for:

- cover
- index
- divider

Supported field properties include:

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

## Overview dashboard

System admins, admins, and users see the overview dashboard.

The dashboard includes:

- summary cards
- Submittals by employee chart
- Submittals by status chart
- Monthly trend chart
- date/month/year/all filters
- employee drill-down
- status drill-down

Clicking a chart bar shows the matching submittals below the charts.

Dashboard permissions:

- Admin/system admin can edit, delete, and download all submittals.
- Users can edit/delete their own submittals.
- Users can download any generated submittal, including submittals created by other users.
- Users cannot edit/delete other users' submittals.

## Browser navigation

The frontend uses hash navigation:

```text
#dashboard
#new
#products
#documents
#templates
#users
```

Browser Back/Forward moves between app pages.

Logout happens only from the logout button.

If the user leaves New Submittal with unsaved work, the save-draft popup appears.

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

Delete local database volume:

```powershell
docker compose down -v
```

Use `docker compose down -v` carefully because it deletes local PostgreSQL data.

## Testing/build checks

Build frontend:

```powershell
docker compose build --pull=false web
```

Build backend:

```powershell
docker compose build --pull=false api
```

Run backend tests:

```powershell
docker compose exec api pytest
```

## Troubleshooting

### Docker is not recognized

Install Docker Desktop and restart PowerShell.

Check:

```powershell
docker version
```

### Cannot connect to Docker daemon

Open Docker Desktop and wait until Docker Engine is running.

### Localhost refused to connect

Check containers:

```powershell
docker compose ps
```

Start them if needed:

```powershell
docker compose up -d
```

### Missing active templates

Error:

```text
Missing active templates: cover, index, divider
```

Fix:

1. Sign in as admin/system admin.
2. Go to Templates.
3. Upload active templates for:
   - cover
   - index
   - divider

### PDF not customized

Check:

- active templates exist
- template kinds are correct
- backend was redeployed after PDF engine changes
- you generated a new PDF, not an old stored output

### Railway frontend failed to respond

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
- frontend `VITE_API_URL` points to backend `/api/v1`
- backend CORS includes frontend domain
- account is active
- password is correct

### Bootstrap admin password does not work

The bootstrap password is only used when the account is first created.

If the account already exists, changing `BOOTSTRAP_ADMIN_PASSWORD` does not reset it.

Reset the password from system admin user management.

### Logo or UI not updated

Hard refresh the browser:

```text
Ctrl + F5
```

For Railway, make sure the frontend service redeployed after pushing changes.

### Railway backend out of memory

Large PDF packages can exceed Railway backend memory during preview/generation because PDFs are assembled in memory.

The backend checks source PDF package size using:

```env
MAX_PACKAGE_SOURCE_MB=60
```

If the package is too large, reduce/compress PDFs or increase Railway backend memory/plan.

Storage and memory are different:

- storage controls how much data can be kept
- memory/RAM controls how large a PDF package can be processed at one time

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

PDF/template files are stored in PostgreSQL binary columns.

## Production notes

- Keep the GitHub repository private.
- Use strong passwords and a strong `JWT_SECRET`.
- Do not share admin accounts.
- Create named accounts for each employee.
- Configure PostgreSQL backups before using real company data.
- Do not delete the Railway PostgreSQL service unless data removal is intentional.
- Monitor Railway usage and billing.
- Store only approved templates and documents.
- Consider antivirus scanning for uploaded PDFs before wider rollout.

## Important note

Generated PDFs are stored as final output files. If template logic, cover placement, index behavior, or document ordering rules change later, old generated PDFs do not update automatically.

Regenerate the submittal to produce a new final PDF with the latest behavior.
