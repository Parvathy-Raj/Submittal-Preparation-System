# Railway Deployment Guide

## Submittal Preparation System

This guide explains how to deploy the system on Railway as three services:

1. PostgreSQL database
2. FastAPI backend
3. React frontend

Railway supports Dockerfile-based services, custom Dockerfile paths through `RAILWAY_DOCKERFILE_PATH`, Railway-provided domains with automatic SSL, and PostgreSQL service variables including `DATABASE_URL`.

---

## 1. Before You Start

You need:

- A Railway account
- A GitHub repository containing this project
- Railway project access
- A generated secure JWT secret
- A system admin email and password

Important: do not upload real company documents until deployment, login, backup, and access control are confirmed.

---

## 2. Push Project to GitHub

Railway deployment from GitHub is the easiest method.

From the project folder:

```powershell
git status
git add .
git commit -m "Prepare Railway deployment"
git push
```

If the project is not yet connected to GitHub, create a private repository first and push it there.

---

## 3. Create Railway Project

1. Open Railway.
2. Click **New Project**.
3. Choose **Deploy from GitHub repo**.
4. Select the project repository.

You will create separate services for backend and frontend from the same repository.

---

## 4. Add PostgreSQL

1. In the Railway project canvas, click **+ New**.
2. Select **Database**.
3. Choose **PostgreSQL**.

Railway will create variables such as:

- `DATABASE_URL`
- `PGHOST`
- `PGPORT`
- `PGUSER`
- `PGPASSWORD`
- `PGDATABASE`

The backend service should reference the PostgreSQL service `DATABASE_URL`.

---

## 5. Backend Service Setup

Create a backend service from the same GitHub repo.

In backend service variables, set:

```env
RAILWAY_DOCKERFILE_PATH=Dockerfile.backend
DATABASE_URL=${{Postgres.DATABASE_URL}}
JWT_SECRET=<generate-a-long-random-secret>
BOOTSTRAP_ADMIN_EMAIL=<your-admin-email>
BOOTSTRAP_ADMIN_PASSWORD=<temporary-strong-password>
JWT_MINUTES=480
MAX_UPLOAD_MB=100
CORS_ORIGINS=http://localhost:8080
CORS_ORIGIN_REGEX=https://.*\.railway\.app
```

Notes:

- Replace `Postgres` with the exact name of your Railway PostgreSQL service if Railway names it differently.
- `CORS_ORIGIN_REGEX` allows Railway frontend domains during trial deployment.
- For final production, replace this with an exact frontend domain in `CORS_ORIGINS`.

After deployment:

1. Open backend service.
2. Go to **Settings**.
3. Under **Networking → Public Networking**, click **Generate Domain**.
4. Copy the backend URL.

Backend health check URL:

```text
https://your-backend-domain.railway.app/health
```

Expected response:

```json
{"status":"ok"}
```

---

## 6. Frontend Service Setup

Create another service from the same GitHub repo for the frontend.

In frontend service variables, set:

```env
RAILWAY_DOCKERFILE_PATH=Dockerfile.frontend
VITE_API_URL=https://your-backend-domain.railway.app/api/v1
```

Replace `https://your-backend-domain.railway.app` with the backend domain generated in Railway.

Then:

1. Deploy frontend service.
2. Go to **Settings**.
3. Under **Networking → Public Networking**, click **Generate Domain**.
4. When Railway asks for the port, enter `8080`.
4. Open the frontend Railway URL.

---

## 7. First Login

Use the values configured in backend variables:

```text
Email: BOOTSTRAP_ADMIN_EMAIL
Password: BOOTSTRAP_ADMIN_PASSWORD
```

After login, change/create admin and user accounts from the system.

---

## 8. Recommended Production Changes

Before using Railway with real company documents:

- Use a strong `JWT_SECRET`.
- Change the temporary bootstrap admin password.
- Restrict `CORS_ORIGINS` to the exact frontend URL.
- Enable or schedule PostgreSQL backups.
- Confirm Railway billing limits.
- Confirm who has access to the Railway project.
- Test PDF upload, template upload, product creation, and final submittal download.

---

## 9. Common Issues

### Frontend opens but login fails

Check:

- `VITE_API_URL` is set to backend URL ending with `/api/v1`
- Backend service has a public Railway domain
- Backend CORS allows the frontend domain

### Backend deploys but cannot connect to database

Check:

- `DATABASE_URL=${{Postgres.DATABASE_URL}}`
- PostgreSQL service name is correct
- PostgreSQL service is running

### Site says application failed to respond

Check:

- Dockerfile path is correct
- Service logs show the app listening on the Railway-provided port
- Backend uses `backend/Dockerfile`
- Frontend uses `frontend/Dockerfile`

---

## 10. Official Railway References

- Dockerfiles: https://docs.railway.com/builds/dockerfiles
- PostgreSQL: https://docs.railway.com/databases/postgresql
- Public networking: https://docs.railway.com/networking/public-networking
- Variables: https://docs.railway.com/variables/reference
