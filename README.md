# 🎓 UniBook - Asset Booking System
**DA3331 Business Application Development | Group 13**

A web application that allows students to book university resources 
(labs, equipment, meeting rooms) and administrators to manage availability and view usage reports.

## 👥 Team Members
- Member 1 - Lavin Dharmathilake 236029B
- Member 2 - Chenali Ranawana 236109V
- Member 3 - Omindu Perera 236097E

## ⚙️ Tech Stack
- Backend: Django (Python)
- Frontend: Bootstrap 5
- Database: SQLite
- Version Control: Git & GitHub

## 🚀 How to Run Locally

### 1. Clone the repository
git clone https://github.com/YOURUSERNAME/asset-booking-system.git
cd asset-booking-system

### 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

### 3. Install dependencies
pip install -r requirements.txt

### 4. Run migrations
python manage.py makemigrations
python manage.py migrate

### 5. Create admin account
python manage.py createsuperuser

### 6. Start server
python manage.py runserver

Visit: http://127.0.0.1:8000

## 📋 Features

### Student
- Register and login
- Browse resources by type (Lab, Equipment, Meeting Room)
- Submit booking requests
- View and cancel own bookings

### Admin
- Approve or reject booking requests with notes
- Add, edit, delete resources
- View usage reports

## 📁 Project Structure
asset_booking/
├── core/          # Django project settings
├── bookings/      # Main app (models, views, forms)
├── templates/     # HTML templates
├── static/        # CSS/JS files
└── manage.py