from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Database configuration
# ---------------------------------------------------------------------------

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///studysprint.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Subject(db.Model):
    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)

    topics = db.relationship("Topic", backref="subject", lazy=True)

    def __repr__(self):
        return f"<Subject {self.id}: {self.name}>"


class Topic(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subject.id"), nullable=False)
    title      = db.Column(db.String(200), nullable=False)
    difficulty = db.Column(db.Integer, nullable=False, default=5)   # 1–10
    completion = db.Column(db.Integer, nullable=False, default=0)   # 0–100
    status     = db.Column(db.String(20), nullable=False, default="Not Started")

    def __repr__(self):
        return f"<Topic {self.id}: {self.title}>"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Maps DB status values → kanban column keys (used as CSS class suffixes)
STATUS_COLUMN = {
    "Not Started": "not_started",
    "In Progress": "in_progress",
    "Done":        "done",
}

VALID_STATUSES = list(STATUS_COLUMN.keys())  # ["Not Started", "In Progress", "Done"]


def priority_score(topic) -> float:
    """Higher score → shown first within a column."""
    remaining       = 1 - topic.completion / 100
    difficulty_norm = topic.difficulty / 10
    return remaining * (0.6 + 0.4 * difficulty_norm)


def subject_completion(subject) -> int:
    """Average completion of all topics, rounded to nearest int."""
    if not subject.topics:
        return 0
    return round(sum(t.completion for t in subject.topics) / len(subject.topics))


def parse_topic_form(form) -> tuple:
    """Extract, validate, and clamp topic fields from a POST form."""
    title = form.get("title", "").strip()

    try:
        difficulty = max(1, min(10, int(form.get("difficulty", 5))))
    except (ValueError, TypeError):
        difficulty = 5

    try:
        completion = max(0, min(100, int(form.get("completion", 0))))
    except (ValueError, TypeError):
        completion = 0

    status = form.get("status", "Not Started")
    if status not in VALID_STATUSES:
        status = "Not Started"

    if status == "Done":        # Done always means 100 %
        completion = 100

    return title, difficulty, completion, status


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def dashboard():
    subjects = Subject.query.order_by(Subject.name).all()
    subject_data = [
        {
            "id":                 s.id,
            "name":               s.name,
            "overall_completion": subject_completion(s),
            "topic_count":        len(s.topics),
        }
        for s in subjects
    ]

    incomplete = Topic.query.filter(Topic.completion < 100).all()
    incomplete.sort(key=priority_score, reverse=True)
    focus_topics = [
        {
            "title":       t.title,
            "subject_name": t.subject.name,
            "completion":  t.completion,
        }
        for t in incomplete[:5]
    ]

    return render_template("dashboard.html", subjects=subject_data,
                           focus_topics=focus_topics)


@app.route("/subjects", methods=["POST"])
def add_subject():
    name = request.form.get("name", "").strip()
    if name:
        db.session.add(Subject(name=name))
        db.session.commit()
    return redirect(url_for("dashboard"))


@app.route("/subjects/<int:subject_id>")
def subject(subject_id: int):
    subj = db.get_or_404(Subject, subject_id)

    columns = {
        "not_started": {"label": "Not Started", "topics": []},
        "in_progress": {"label": "In Progress", "topics": []},
        "done":        {"label": "Done",         "topics": []},
    }

    for t in subj.topics:
        col_key = STATUS_COLUMN.get(t.status, "not_started")
        columns[col_key]["topics"].append({
            "id":         t.id,
            "title":      t.title,
            "difficulty": t.difficulty,
            "completion": t.completion,
            "status":     t.status,
            "priority":   priority_score(t),
        })

    for col in columns.values():
        col["topics"].sort(key=lambda t: t["priority"], reverse=True)

    return render_template(
        "subject.html",
        subject=subj,
        columns=columns,
        overall_completion=subject_completion(subj),
        valid_statuses=VALID_STATUSES,
    )


@app.route("/subjects/<int:subject_id>/topics", methods=["POST"])
def add_topic(subject_id: int):
    db.get_or_404(Subject, subject_id)  # 404 if subject doesn't exist
    title, difficulty, completion, status = parse_topic_form(request.form)
    if title:
        db.session.add(Topic(
            subject_id=subject_id,
            title=title,
            difficulty=difficulty,
            completion=completion,
            status=status,
        ))
        db.session.commit()
    return redirect(url_for("subject", subject_id=subject_id))


@app.route("/topics/<int:topic_id>/update", methods=["POST"])
def update_topic(topic_id: int):
    topic = db.get_or_404(Topic, topic_id)
    title, difficulty, completion, status = parse_topic_form(request.form)
    if title:
        topic.title      = title
        topic.difficulty = difficulty
        topic.completion = completion
        topic.status     = status
        db.session.commit()
    return redirect(url_for("subject", subject_id=topic.subject_id))


@app.route("/topics/<int:topic_id>/delete", methods=["POST"])
def delete_topic(topic_id: int):
    topic = db.get_or_404(Topic, topic_id)
    subject_id = topic.subject_id
    db.session.delete(topic)
    db.session.commit()
    return redirect(url_for("subject", subject_id=subject_id))


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5001, debug=True)
