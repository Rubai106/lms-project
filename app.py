import os
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, send_from_directory
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# ======================
# APP & CONFIG
# ======================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///lms.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)

# ======================
# AUTH DECORATORS
# ======================

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please login first")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def teacher_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please login first")
            return redirect(url_for("login"))
        if session.get("user_role") != "teacher":
            flash("Teachers only")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated

# ======================
# MODELS
# ======================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # student / teacher


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    teacher = db.relationship("User", backref="courses")


class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)

    student = db.relationship("User", backref="enrollments")
    course = db.relationship("Course", backref="enrollments")


class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)

    course = db.relationship("Course", backref="lessons")

class LessonFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    lesson_id = db.Column(
        db.Integer,
        db.ForeignKey("lesson.id", ondelete="CASCADE"),
        nullable=False
    )

    lesson = db.relationship(
        "Lesson",
        backref=db.backref("files", cascade="all, delete-orphan")
    )

# ======================
# AUTH ROUTES
# ======================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        if User.query.filter_by(email=request.form["email"]).first():
            flash("Email already exists")
            return redirect(url_for("signup"))

        user = User(
            name=request.form["name"],
            email=request.form["email"],
            password=generate_password_hash(request.form["password"]),
            role=request.form["role"]
        )
        db.session.add(user)
        db.session.commit()

        flash("Account created. Please login.")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"]).first()
        if not user or not check_password_hash(user.password, request.form["password"]):
            flash("Invalid credentials")
            return redirect(url_for("login"))

        session["user_id"] = user.id
        session["user_name"] = user.name
        session["user_role"] = user.role

        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# ======================
# DASHBOARD
# ======================

@app.route("/dashboard")
@login_required
def dashboard():
    if session["user_role"] == "student":
        enrollments = Enrollment.query.filter_by(student_id=session["user_id"]).all()
        courses = [e.course for e in enrollments]
        return render_template("student_dashboard.html", courses=courses)

    return render_template("teacher_dashboard.html")

# ======================
# COURSES
# ======================

@app.route("/teacher/courses")
@teacher_required
def teacher_courses():
    courses = Course.query.filter_by(teacher_id=session["user_id"]).all()
    return render_template("teacher_courses.html", courses=courses)


@app.route("/teacher/create-course", methods=["GET", "POST"])
@teacher_required
def create_course():
    if request.method == "POST":
        course = Course(
            title=request.form["title"],
            description=request.form["description"],
            teacher_id=session["user_id"]
        )
        db.session.add(course)
        db.session.commit()
        return redirect(url_for("teacher_courses"))

    return render_template("create_course.html")


@app.route("/teacher/course/<int:course_id>/edit", methods=["GET", "POST"])
@teacher_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)

    if course.teacher_id != session["user_id"]:
        flash("Not allowed")
        return redirect(url_for("teacher_courses"))

    if request.method == "POST":
        course.title = request.form["title"]
        course.description = request.form["description"]
        db.session.commit()
        return redirect(url_for("teacher_courses"))

    return render_template("edit_course.html", course=course)


@app.route("/teacher/course/<int:course_id>/delete")
@teacher_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)

    if course.teacher_id != session["user_id"]:
        flash("Not allowed")
        return redirect(url_for("teacher_courses"))

    db.session.delete(course)
    db.session.commit()
    return redirect(url_for("teacher_courses"))

# ======================
# ENROLLMENT
# ======================

@app.route("/courses")
@login_required
def all_courses():
    if session["user_role"] != "student":
        return redirect(url_for("dashboard"))

    courses = Course.query.all()
    enrollments = Enrollment.query.filter_by(student_id=session["user_id"]).all()
    enrolled_ids = [e.course_id for e in enrollments]

    return render_template(
        "all_courses.html",
        courses=courses,
        enrolled_course_ids=enrolled_ids
    )


@app.route("/enroll/<int:course_id>")
@login_required
def enroll(course_id):
    if session["user_role"] != "student":
        return redirect(url_for("dashboard"))

    if Enrollment.query.filter_by(
        student_id=session["user_id"], course_id=course_id
    ).first():
        return redirect(url_for("all_courses"))

    db.session.add(
        Enrollment(student_id=session["user_id"], course_id=course_id)
    )
    db.session.commit()
    return redirect(url_for("all_courses"))

@app.route("/unenroll/<int:course_id>")
@login_required
def unenroll(course_id):
    if session.get("user_role") != "student":
        flash("Only students can unenroll")
        return redirect(url_for("dashboard"))

    enrollment = Enrollment.query.filter_by(
        student_id=session.get("user_id"),
        course_id=course_id
    ).first()

    if not enrollment:
        flash("You are not enrolled in this course")
        return redirect(url_for("all_courses"))

    db.session.delete(enrollment)
    db.session.commit()

    flash("You have unenrolled from the course")
    return redirect(url_for("all_courses"))


# ======================
# COURSE DETAILS + LESSONS
# ======================

@app.route("/course/<int:course_id>")
@login_required
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)

    enrolled = False
    students = []

    if session["user_role"] == "student":
        enrolled = Enrollment.query.filter_by(
            student_id=session["user_id"],
            course_id=course.id
        ).first() is not None

    if session["user_role"] == "teacher":
        students = [
            e.student for e in Enrollment.query.filter_by(course_id=course.id).all()
        ]

    return render_template(
        "course_detail.html",
        course=course,
        enrolled=enrolled,
        enrolled_students=students
    )

# ======================
# LESSONS (TEXT + FILE)
# ======================

@app.route("/teacher/course/<int:course_id>/lesson/add", methods=["GET", "POST"])
@teacher_required
def add_lesson(course_id):
    course = Course.query.get_or_404(course_id)

    if course.teacher_id != session["user_id"]:
        return redirect(url_for("teacher_courses"))

    if request.method == "POST":
        lesson = Lesson(
            title=request.form["title"],
            content=request.form.get("content"),  # TEXT OPTIONAL
            course_id=course.id
        )
        db.session.add(lesson)
        db.session.commit()

        file = request.files.get("file")
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            db.session.add(
                LessonFile(filename=filename, lesson_id=lesson.id)
            )
            db.session.commit()

        return redirect(url_for("course_detail", course_id=course.id))

    return render_template("add_lesson.html", course=course)


@app.route("/teacher/lesson/<int:lesson_id>/edit", methods=["GET", "POST"])
@teacher_required
def edit_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)

    if lesson.course.teacher_id != session["user_id"]:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        lesson.title = request.form["title"]
        lesson.content = request.form.get("content")
        db.session.commit()
        return redirect(url_for("course_detail", course_id=lesson.course.id))

    return render_template("edit_lesson.html", lesson=lesson)

@app.route("/teacher/lesson/<int:lesson_id>/delete")
@teacher_required
def delete_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)

    # Security check
    if lesson.course.teacher_id != session.get("user_id"):
        flash("You cannot delete this lesson")
        return redirect(url_for("dashboard"))

    course_id = lesson.course.id

    # 1️⃣ Delete physical files
    for file in lesson.files:
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    # 2️⃣ Delete lesson (files removed via cascade)
    db.session.delete(lesson)
    db.session.commit()

    flash("Lesson deleted successfully")
    return redirect(url_for("course_detail", course_id=course_id))


# ======================
# FILE DOWNLOAD
# ======================

@app.route("/uploads/<filename>")
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# ======================
# RUN
# ======================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

