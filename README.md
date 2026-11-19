# Cinderella Cakes

Cinderella Cakes is a modern, responsive web application for a bakery based in Kampala, Uganda. It features a public-facing website for customers to explore cakes, view galleries, and place custom orders, alongside a secure administrative backend for managing content, galleries, and incoming orders.

## Tech Stack
* **Frontend:** React, React Router, Vite
* **Backend:** Python, Flask, SQLAlchemy, Flask-Migrate
* **Database:** MySQL
* **Authentication:** JWT (JSON Web Tokens)

## Key Features
* **Public Site:** Landing page, About Us, Contact information, interactive Gallery, and Order placement with WhatsApp integration.
* **Admin Dashboard:** Secure login, order management (new, confirmed, baking, ready, out_for_delivery, delivered, cancelled), gallery management, and content management (hero, navigation, pages).
* **Role-Based Access Control (RBAC):** Granular permissions for different admin roles (e.g., super_admin, admin, editor).
* **RESTful API:** Blueprint-organized modular Flask API.

## Setup Instructions

### Backend Setup
1. Ensure you have Python and MySQL (e.g., via XAMPP) installed.
2. Navigate to the `backend/` directory.
3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows
   pip install -r requirements.txt
   ```
4. Create your `.env` file in the `backend/` directory. All settings are read from environment
   variables loaded by `python-dotenv`, e.g. `SECRET_KEY`, `JWT_SECRET_KEY`,
   `DEV_DATABASE_URL` / `DATABASE_URL`, `CORS_ORIGINS`, and the mail/WhatsApp options.
5. Back up the selected database, confirm its environment/connection settings, and stop order writes
   during migration. From `backend/`, apply the checked-in migrations with the Windows virtual environment:
   ```powershell
   .\venv\Scripts\python.exe -m flask --app run:app db upgrade
   ```
   Revision `2b82845ea46d` follows `201fa049ee30`. It gives existing orders unique references and
   an initial status snapshot, mapping `pending` to `new`, `contacted` to `confirmed`,
   `in_progress` to `baking`, and `completed` to `delivered`. Canonical statuses stay unchanged.
   Unknown statuses stop migration before schema changes; review them explicitly instead of guessing.
   Revision `7c42e1f9a015` follows `2b82845ea46d` and adds a nullable unique gallery catalog identity.
   It does not rewrite titles, categories, media paths, orders, or credentials. The same `db upgrade`
   command applies the entire initial migration chain on an empty database; do not use `db.create_all`
   or stamp an existing database to bypass migrations. Use Python 3.10+ (SQLite 3.35+ for downgrade).
   SQLite regression coverage does not establish that the real MySQL database has been migrated or seeded.
6. Seed the selected database only after migration, gallery source preparation below, and an account review:
   ```powershell
   .\venv\Scripts\python.exe seed.py
   ```
   The seed preserves an existing admin's ID, password hash, role, and profile while changing its email
   to `cinderellacakes2@gmail.com`; it also updates existing public contact settings. The known legacy
   email is `admin@cinderellacakes.com`. A sole admin under another email can be renamed, but multiple
   admin candidates or email collisions stop seeding without account/role/settings changes.
   Existing credentials are never reset. An empty user database requires `ADMIN_INITIAL_PASSWORD`
   supplied privately in the process environment or an untracked backend `.env`; there is no default
   password. Do not put a password in source control or command examples. Remove the bootstrap variable
   after initialization. Existing site content and role permissions are retained.

   To import **only gallery media/metadata**, without creating or modifying any account, role, setting,
   or page, use the standalone mode instead (no admin password is required):
   ```powershell
   .\venv\Scripts\python.exe seed.py --help
   .\venv\Scripts\python.exe seed.py --gallery-only
   # Optional explicit source; relative paths are resolved from backend, not the shell directory.
   .\venv\Scripts\python.exe seed.py --gallery-only --source-dir "../frontend/src/assets/gallery"
   ```
7. Start the Flask server:
   ```bash
   python run.py
   ```

### Gallery source and persistent media

- The checked-in `backend/data/gallery_catalog.json` contains **120 originals: 119 JPG and 1 MP4**.
  It retains all 112 exact reference metadata mappings. The reference URL is provenance only: neither
  application requests nor import execution contact it, download external images, or copy reviews.
- Reference-matched counts: birthday 33, kids 29, sculpted 16, wedding 12, baby 9, cupcakes 7,
  holiday 3, corporate 2, graduation 1. Final counts include the filename-only SpongeBob kids fallback:
  **birthday 33, kids 30, sculpted 16, wedding 12, baby 9, cupcakes 7, holiday 3, corporate 2,
  graduation 1, other 7** (anniversary 0). All eight unmatched files remain for owner confirmation.
  Weak reference titles are retained; carousel frames remain distinct files and rows.
- Deploy the original source directory, not just frontend `dist`. `GALLERY_SOURCE_DIR` defaults to
  `../frontend/src/assets/gallery` relative to backend; an absolute directory on the server or the
  `--source-dir` option can override it. All 120 named sources must exist, be readable and nonempty.
  Missing/incomplete sources abort before seed database mutations, including in full-seed mode.
- `UPLOAD_FOLDER` is the existing customer-inspiration storage root. Its default is
  `backend/app/static/uploads/inspiration`; a relative override resolves from backend. Mount this
  **whole directory on persistent storage**, including its new `gallery/` subdirectory, and back it up
  with the database. Newly imported gallery originals keep their exact filenames under `gallery/`;
  new admin photo uploads also go there. Customer uploads and older imported files are not moved.
- Public URLs for new gallery media are `/static/uploads/gallery/filename`; legacy URLs remain
  `/static/uploads/inspiration/filename`. Flask serves both from configured storage, even outside its
  static tree. A reverse proxy must forward both routes to Flask (or map them to the corresponding
  persistent directories). MP4 serving must retain Content-Type and byte-range support. Do not point
  `UPLOAD_FOLDER` at a new empty directory and expect existing customer media to move automatically.
- Import checks complete copies before a single gallery transaction. It never deletes originals or
  overwrites existing files. A failed DB commit can leave verified media copies for a safe retry;
  a failed final filesystem write can leave an incomplete destination that causes an explicit conflict
  on retry. Inspect that destination against backups before repair; do not clear the media directory.
  Run one importer at a time, with admin writes paused during the first legacy curation.
- Existing rows are matched by original/sanitized filename suffix, not title or SQL wildcard matching.
  IDs, media paths, and order associations are retained. Only the fully untouched legacy generated
  title/category/empty-description tuple receives curated metadata once. Any custom tuple is retained.
  The catalog identity then prevents all future reseed metadata changes, even if an admin chooses the
  old generated values. Historical edits identical to that old tuple cannot be distinguished before
  this first import. Ambiguous duplicate legacy rows abort for manual review rather than deletion.
- The trusted catalog MP4 is rendered with native controls and metadata preload, never autoplay.
  Administrative uploads remain limited to the existing accepted image extensions; this does not
  introduce general video uploads. Browser codec playback still needs browser verification.
- Fifteen mistakenly removed unique source assets were recovered at their original paths. They were
  not moved to an archive because safe binary preservation took priority; proven duplicates remain
  removed. None of the 120 gallery originals were removed or renamed.

### Frontend Setup
1. Navigate to the `frontend/` directory.
2. Install Node.js dependencies:
   ```bash
   npm install
   ```
3. No frontend environment file is required for local development: Vite proxies `/api` and `/static`
   to `http://127.0.0.1:5000`. The backend must be started separately; the proxy does not launch it.
   `VITE_API_URL` remains an optional API-origin override. For a separate-origin production frontend,
   set it to the deployed backend's HTTPS origin before building (no `/api` suffix or trailing slash),
   and allow the frontend's origin in backend `CORS_ORIGINS`:
   ```
   VITE_API_URL=https://api.example.com
   ```
   Vite's development proxy is not part of a production build. Same-origin production hosting must
   route `/api` and `/static` to the backend itself.
4. Start the Vite development server:
   ```bash
   npm run dev
   ```

## Verification handoff (not executed during implementation)

From `backend/`, run the durable isolated SQLite tests, including the unchanged Task13 suite:
```powershell
.\venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_*.py" -v
```
The gallery suite checks all reference mappings and inventory counts, idempotence, legacy curation,
admin preservation, missing sources/copy failures, media URLs/ranges, order links, and the new migration.
It mocks notifications and uses temporary uploads and SQLite, never the configured production database.
From `frontend/`, the verifier can run `npm run lint` and `npm run build` separately.

### Safe temporary SQLite browser recipe

Use a **new disposable PowerShell window**, starting in `backend/`, with dependencies already installed.
These process-only overrides keep existing `.env`, MySQL, real uploads, and real admin credentials intact.
Do not omit the SQLite or upload overrides; this recipe is for the verifier, not production deployment.
```powershell
$python = (Resolve-Path .\venv\Scripts\python.exe).Path
$scratch = & $python -c "import tempfile; print(tempfile.mkdtemp(prefix='cinderella-gallery-verify-'))"
$env:FLASK_ENV = 'development'
$env:FLASK_SKIP_DOTENV = '1'
$env:DEV_DATABASE_URL = 'sqlite:///' + ($scratch.Replace('\', '/') + '/gallery.sqlite3')
$env:DATABASE_URL = $env:DEV_DATABASE_URL
$env:UPLOAD_FOLDER = Join-Path $scratch 'media'
$env:GALLERY_SOURCE_DIR = (Resolve-Path '..\frontend\src\assets\gallery').Path
$env:SECRET_KEY = & $python -c "import secrets; print(secrets.token_urlsafe(48))"
$env:JWT_SECRET_KEY = & $python -c "import secrets; print(secrets.token_urlsafe(48))"
$env:ADMIN_INITIAL_PASSWORD = & $python -c "import secrets; print(secrets.token_urlsafe(24))"
$env:CORS_ORIGINS = 'http://127.0.0.1:5173,http://localhost:5173'
$env:SERVER_BASE_URL = 'http://127.0.0.1:5000'
& $python -m flask --app run:app db upgrade
if ($LASTEXITCODE -ne 0) { throw 'Temporary migration failed; stop here.' }
& $python seed.py --gallery-only
if ($LASTEXITCODE -ne 0) { throw 'Temporary gallery import failed; stop here.' }
& $python seed.py --gallery-only
if ($LASTEXITCODE -ne 0) { throw 'Temporary idempotence check failed; stop here.' }
# Optional: bootstrap only this disposable database for admin browser checks.
& $python seed.py
if ($LASTEXITCODE -ne 0) { throw 'Temporary bootstrap failed; stop here.' }
# Login: cinderellacakes2@gmail.com; use the ephemeral value in $env:ADMIN_INITIAL_PASSWORD.
& $python -m flask --app run:app run --host 127.0.0.1 --port 5000 --no-reload
```
The application also calls `python-dotenv` itself; explicit process values above take precedence over
any `.env` values. Mail is disabled in application configuration. Do not send real customer information
or follow WhatsApp links during these checks. Stop the temporary server and close this PowerShell
window afterward to discard its environment overrides; keep temporary data only as long as needed.

In another disposable PowerShell window, from `frontend/`:
```powershell
$env:VITE_API_URL = 'http://127.0.0.1:5000'
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```
Browse `http://127.0.0.1:5173/gallery`, confirm the 120-item count and category counts, and exercise the
birthday MP4 card, lightbox, and selected Order design. Confirm controls work without autoplay and images
still lazy-load. Place a synthetic video-linked order, check admin Gallery/editor and Orders previews,
edit a gallery title/category, rerun only the temporary importer, and confirm the edits and order ID link
survive. Rapidly switch category filters and try an invalid selected design URL. Browser rendering,
actual MySQL migration/import, and production persistence have **not** been verified or performed here.

## License
All rights reserved.