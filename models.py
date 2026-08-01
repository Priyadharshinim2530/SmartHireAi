# models.py
from datetime import datetime
import bcrypt
from werkzeug.security import check_password_hash
from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'company' or 'seeker'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    company_profile = db.relationship(
        "Company", backref="user", uselist=False, cascade="all, delete-orphan"
    )
    seeker_profile = db.relationship(
        "Seeker", backref="user", uselist=False, cascade="all, delete-orphan"
    )

    def set_password(self, raw_password):
        self.password_hash = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, raw_password):
        if self.password_hash.startswith('pbkdf2:'):
            return check_password_hash(self.password_hash, raw_password)
        try:
            return bcrypt.checkpw(raw_password.encode('utf-8'), self.password_hash.encode('utf-8'))
        except ValueError:
            return False


class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    company_name = db.Column(db.String(150), nullable=False)
    industry = db.Column(db.String(100))
    website = db.Column(db.String(200))
    description = db.Column(db.Text)

    jobs = db.relationship("Job", backref="company", cascade="all, delete-orphan")


class Seeker(db.Model):
    __tablename__ = "seekers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(30))
    headline = db.Column(db.String(200))
    skills = db.Column(db.Text)          # comma-separated
    experience_years = db.Column(db.Float, default=0)
    education = db.Column(db.Text)
    summary = db.Column(db.Text)
    work_history = db.Column(db.Text)    # JSON-encoded list of roles
    resume_text = db.Column(db.Text)     # flattened plain-text resume (ATS-friendly)

    applications = db.relationship(
        "Application", backref="seeker", cascade="all, delete-orphan"
    )


class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    required_skills = db.Column(db.Text)   # comma-separated
    min_experience = db.Column(db.Float, default=0)
    location = db.Column(db.String(150))
    job_type = db.Column(db.String(50), default="Full-time")
    status = db.Column(db.String(20), default="open")  # open / closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship(
        "Application", backref="job", cascade="all, delete-orphan"
    )


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    seeker_id = db.Column(db.Integer, db.ForeignKey("seekers.id"), nullable=False)
    resume_snapshot = db.Column(db.Text)
    ats_score = db.Column(db.Float, default=0)
    score_breakdown = db.Column(db.Text)  # JSON-encoded explanation
    status = db.Column(db.String(20), default="applied")  # applied/shortlisted/rejected
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("job_id", "seeker_id", name="uq_job_seeker"),
    )


class PasswordReset(db.Model):
    __tablename__ = "password_resets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    token = db.Column(db.String(128), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)

    user = db.relationship("User", backref="password_resets")