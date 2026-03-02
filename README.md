# LMS Project

A role-based Academic Learning Management System built with Flask for students and instructors.

##  Features

###  Teacher Features
- Create, edit, and delete courses
- Add lessons with:
  - Text content
  - File uploads (PDF, DOC, images)
- Edit and delete lessons
- View enrolled students per course
- Role-based access control (teachers only)

###  Student Features
- View all available courses
- Enroll and unenroll from courses
- View enrolled courses in dashboard
- Access lessons and download files
- Enrollment-based lesson access

###  Authentication & Security
- User signup & login
- Passwords stored using secure hashing (pbkdf2:sha256)
- Session-based authentication
- Role-based authorization (student / teacher)

##  Tech Stack
- **Backend:** Flask (Python)
- **Database:** SQLite + SQLAlchemy ORM
- **Frontend:** HTML, CSS (Jinja templates)
- **Authentication:** Werkzeug password hashing
- **File Uploads:** Flask file handling

##  Getting Started

### Prerequisites
- Python 3.10+

### Installation

```bash
# Clone the repository
git clone https://github.com/Rubai106/lms-project.git
cd lms-project

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The app will be available at **http://127.0.0.1:5000**
