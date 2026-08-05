# Cinderella Cakes

Cinderella Cakes is a modern, responsive web application for a boutique bakery based in Kampala, Uganda. It features a public-facing website for customers to explore cakes, view galleries, and place custom orders, alongside a secure administrative backend for managing content, galleries, and incoming orders.

## Tech Stack
* **Frontend:** React, React Router, Vite
* **Backend:** Python, Flask, SQLAlchemy, Flask-Migrate
* **Database:** MySQL
* **Authentication:** JWT (JSON Web Tokens)

## Key Features
* **Public Site:** Landing page, About Us, Contact information, interactive Gallery, and Order placement with WhatsApp integration.
* **Admin Dashboard:** Secure login, order management (pending, approved, rejected), gallery management, and content management (hero, navigation, pages).
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
4. Set up your `.env` file with `SECRET_KEY`, `JWT_SECRET_KEY`, and `SQLALCHEMY_DATABASE_URI`.
5. Run database migrations:
   ```bash
   flask db upgrade
   ```
6. Start the Flask server:
   ```bash
   python run.py
   ```

### Frontend Setup
1. Navigate to the `frontend/` directory.
2. Install Node.js dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```

## License
All rights reserved.