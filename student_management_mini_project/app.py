import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-this")

database_url = os.environ.get("DATABASE_URL", "").strip()
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

if database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///students.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    course = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<Student {self.roll_number}: {self.name}>"


with app.app_context():
    db.create_all()


@app.route("/")
def index():
    search = request.args.get("q", "").strip()
    query = Student.query
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                Student.name.ilike(like),
                Student.roll_number.ilike(like),
                Student.email.ilike(like),
                Student.course.ilike(like),
            )
        )
    students = query.order_by(Student.id.desc()).all()
    return render_template("index.html", students=students, search=search)


@app.route("/add", methods=["POST"])
def add_student():
    roll_number = request.form.get("roll_number", "").strip()
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    course = request.form.get("course", "").strip()

    if not all([roll_number, name, email, course]):
        flash("Please fill in every field.", "error")
        return redirect(url_for("index"))

    student = Student(
        roll_number=roll_number,
        name=name,
        email=email,
        course=course,
    )
    db.session.add(student)
    try:
        db.session.commit()
        flash("Student added successfully.", "success")
    except IntegrityError:
        db.session.rollback()
        flash("Roll number or email already exists. Use unique values.", "error")
    return redirect(url_for("index"))


@app.route("/edit/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == "POST":
        roll_number = request.form.get("roll_number", "").strip()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        course = request.form.get("course", "").strip()

        if not all([roll_number, name, email, course]):
            flash("Please fill in every field.", "error")
            return render_template("edit.html", student=student)

        student.roll_number = roll_number
        student.name = name
        student.email = email
        student.course = course
        try:
            db.session.commit()
            flash("Student updated successfully.", "success")
            return redirect(url_for("index"))
        except IntegrityError:
            db.session.rollback()
            flash("Roll number or email is already used by another student.", "error")
    return render_template("edit.html", student=student)


@app.route("/delete/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash("Student deleted successfully.", "success")
    return redirect(url_for("index"))


@app.route("/health")
def health():
    return jsonify(status="ok", application="Student Management System")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
