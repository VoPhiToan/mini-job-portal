# Mini Job Portal

A beginner-friendly job search and recruitment website built as a portfolio project.

## Tech Stack

- HTML
- CSS
- JavaScript
- Python
- FastAPI
- SQLAlchemy
- Supabase PostgreSQL

## Run locally on Windows PowerShell

1. Create the virtual environment:

   ```powershell
   python -m venv .venv
   ```

2. Activate the virtual environment:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

4. Start FastAPI:

   ```powershell
   uvicorn app.main:app --reload
   ```

5. Open the application: [http://127.0.0.1:8000](http://127.0.0.1:8000)

6. Open Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Frontend

The frontend uses HTML, CSS, JavaScript, and the Fetch API.

Start the backend in Terminal 1:

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8002
```

Start the frontend in Terminal 2:

```powershell
cd frontend
python -m http.server 5500
```

Open the frontend at [http://127.0.0.1:5500](http://127.0.0.1:5500).

Swagger UI is available at [http://127.0.0.1:8002/docs](http://127.0.0.1:8002/docs).

## Production

- Frontend: [https://mini-job-portal.pages.dev](https://mini-job-portal.pages.dev)
- Backend API: [https://mini-job-portal-api.onrender.com](https://mini-job-portal-api.onrender.com)
- Swagger UI: [https://mini-job-portal-api.onrender.com/docs](https://mini-job-portal-api.onrender.com/docs)
- Database: Supabase PostgreSQL
- Hosting: Cloudflare Pages + Render
