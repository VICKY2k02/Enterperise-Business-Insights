# Enterprise Business Insights Mobile App

## 1. Project Overview

An enterprise business insights mobile application built using React Native, TypeScript, Expo, FastAPI, and PostgreSQL. It provides dashboard KPIs, revenue trends, order summaries, customer information, and recent activities.

## 2. Technologies Used

- **Frontend:** React Native, TypeScript, Expo
- **Backend:** Python, FastAPI, SQLAlchemy
- **Database:** PostgreSQL
- **Database Migrations:** Alembic

## 3. Project Structure

```text
enterprise-business-insights/
├── backend/
│   ├── app/
│   ├── scripts/
│   ├── alembic/
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   ├── App.tsx
│   └── package.json
└── README.md
```

## 4. Prerequisites

Install the following:

- Python
- Node.js and npm
- PostgreSQL
- Expo Go (if testing on a physical mobile device)

## 5. Database Setup

1. Start PostgreSQL.
2. Create a database named `enterprise_business_insights`.
3. Configure the database connection in `backend/.env`.

Example configuration (replace the placeholder with your own credentials):

```env
DATABASE_URL=postgresql+psycopg2://postgres:<YOUR_PASSWORD>@localhost:5432/enterprise_business_insights
```

Do not commit your actual `.env` file or database password to Git.

## 6. Backend Setup

Open PowerShell in the `backend` directory:

```powershell
cd backend
```

Create a virtual environment if one does not already exist:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Apply database migrations:

```powershell
python -m alembic upgrade head
```

Seed the database:

```powershell
python -m scripts.seed_data
```

Start the backend:

```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API documentation:

http://127.0.0.1:8000/docs

## 7. Frontend Setup

Open a separate PowerShell terminal in the `frontend` directory:

```powershell
cd frontend
npm install
```

Start Expo:

```powershell
npx expo start -c
```

For a physical device, configure the API base URL to use your computer's reachable local network IP address rather than `127.0.0.1`.

## 8. API Endpoints

- `GET /api/dashboard` — dashboard KPIs and summary data
- `GET /api/orders` — paginated orders
- `GET /api/customers` — paginated customers
- `GET /api/analytics/revenue-trend` — revenue trend with date filters
- `GET /api/activities` — recent activities

## 9. Database Migrations

Check the current migration:

```powershell
python -m alembic current
```

Check whether model changes require a migration:

```powershell
python -m alembic check
```

## 10. Notes

- Dashboard data is retrieved from the backend API.
- PostgreSQL stores data in its server-managed data directory, not as a database file inside this project.
- Keep credentials and environment-specific settings out of version control.
