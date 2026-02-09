A role-based Academic Learning Management System built with Flask for students and instructors.

🚀 Features
👨‍🏫 Teacher Features

Create, edit, and delete courses

Add lessons with:

Text content

File uploads (PDF, DOC, images)

Edit and delete lessons

View enrolled students per course

Role-based access control (teachers only)

👨‍🎓 Student Features

View all available courses

Enroll and unenroll from courses

View enrolled courses in dashboard

Access lessons and download files

Enrollment-based lesson access

🔐 Authentication & Security

User signup & login

Passwords stored using secure hashing (pbkdf2:sha256)

Session-based authentication

Role-based authorization (student / teacher)

🛠️ Tech Stack

Backend: Flask (Python)

Database: SQLite + SQLAlchemy ORM

Frontend: HTML, CSS (Jinja templates)

Authentication: Werkzeug password hashing

File Uploads: Flask file handling
