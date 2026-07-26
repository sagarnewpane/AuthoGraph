# Authograph

Authograph is a secure image-sharing platform built with Django and SvelteKit.
It supports image encryption, watermarking, metadata management, access control,
activity logs, and AI-protection features.

## Tech Stack

- Django and Django REST Framework
- SvelteKit, Svelte 5, and Tailwind CSS
- SQLite
- Pillow, OpenCV, NumPy, and PyWavelets
- AES encryption using `cryptography`

## Requirements

- Python 3.10 or newer
- Node.js 20 or newer
- npm
- ExifTool (optional, for complete metadata support)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/sagarnewpane/AuthoGraph.git
cd AuthoGraph
```

### 2. Configure environment variables

Copy the included templates:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Edit the copied files if needed. The default frontend configuration already
connects to the local Django server.

Email credentials in `backend/.env` are optional unless password-reset emails
are required.

### 3. Install the project

On macOS, Linux, or WSL:

```bash
chmod +x setup_project.sh start_project.sh
./setup_project.sh
```

The setup script creates `.venv`, installs the backend and frontend
dependencies, creates `backend/db.sqlite3`, and applies the Django migrations.

To use a specific Python version:

```bash
PYTHON_BIN=python3.10 ./setup_project.sh
```

### 4. Start the project

```bash
./start_project.sh
```

Open:

- Frontend: `http://localhost:5173`
- Django API: `http://127.0.0.1:8000`
- Django admin: `http://127.0.0.1:8000/admin/`

Press `Ctrl+C` to stop both servers.

## Create an Admin Account

```bash
cd backend
../.venv/bin/python manage.py createsuperuser
```

## Manual Installation

If the setup script is unavailable:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r backend/requirements.txt

cd backend
../.venv/bin/python manage.py migrate

cd ../frontend
npm ci
```

Run Django and SvelteKit in separate terminals:

```bash
cd backend
../.venv/bin/python manage.py runserver
```

```bash
cd frontend
npm run dev
```

## Notes

- PostgreSQL is not required. Local data is stored in `backend/db.sqlite3`.
- Uploaded files are stored in `backend/media/`.
- Back up both `backend/db.sqlite3` and `backend/media/` when moving the project
  to another device.
- If uploads fail because `cryptography` is missing, rerun:

```bash
./.venv/bin/python -m pip install -r backend/requirements.txt
```

## License

This project is intended for academic and educational purposes.
