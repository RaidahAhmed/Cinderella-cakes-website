# Cinderella Cakes — Frontend

This is the React (Vite) frontend for the Cinderella Cakes website. See the root `README.md`
(one folder up) for the full setup guide covering both this app and the Flask/Python backend.

The backend is written in Python using Flask (Flask-SQLAlchemy, Flask-Migrate, JWT auth); it lives
in the `backend/` folder and is started with `python run.py`.

Quick start:
```
npm install
npm run dev
```

## API URL

The frontend talks to the backend through a single configurable origin. Create a `.env` file in
this folder to point at your Flask server:

```
VITE_API_URL=http://localhost:5000
```

When `VITE_API_URL` is not set, requests are sent to the same origin that served the app
(useful when the built frontend and the API are deployed behind one domain).
