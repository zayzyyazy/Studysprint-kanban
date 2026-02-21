from flask import Flask, render_template, abort

app = Flask(__name__)

# ---------------------------------------------------------------------------
# In-memory sample data  (Step 1 – no database)
# ---------------------------------------------------------------------------

SUBJECTS = {
    "math": {
        "id": "math",
        "name": "Mathematics",
        "color": "#4f46e5",
        "topics": [
            {"id": 1, "title": "Limits & Continuity",      "difficulty": 6,  "completion": 100, "status": "done"},
            {"id": 2, "title": "Derivatives",               "difficulty": 7,  "completion": 100, "status": "done"},
            {"id": 3, "title": "Integration Techniques",    "difficulty": 9,  "completion": 60,  "status": "in_progress"},
            {"id": 4, "title": "Sequences & Series",        "difficulty": 8,  "completion": 30,  "status": "in_progress"},
            {"id": 5, "title": "Multivariable Calculus",    "difficulty": 10, "completion": 0,   "status": "not_started"},
            {"id": 6, "title": "Differential Equations",    "difficulty": 9,  "completion": 0,   "status": "not_started"},
            {"id": 7, "title": "Linear Algebra",            "difficulty": 7,  "completion": 0,   "status": "not_started"},
        ],
    },
    "cs": {
        "id": "cs",
        "name": "Computer Science",
        "color": "#0891b2",
        "topics": [
            {"id": 101, "title": "Big-O Notation",           "difficulty": 4,  "completion": 100, "status": "done"},
            {"id": 102, "title": "Sorting Algorithms",       "difficulty": 5,  "completion": 100, "status": "done"},
            {"id": 103, "title": "Binary Search Trees",      "difficulty": 6,  "completion": 75,  "status": "in_progress"},
            {"id": 104, "title": "Graph Traversal (BFS/DFS)","difficulty": 7,  "completion": 40,  "status": "in_progress"},
            {"id": 105, "title": "Dynamic Programming",      "difficulty": 9,  "completion": 10,  "status": "in_progress"},
            {"id": 106, "title": "Greedy Algorithms",        "difficulty": 6,  "completion": 0,   "status": "not_started"},
            {"id": 107, "title": "Heaps & Priority Queues",  "difficulty": 5,  "completion": 0,   "status": "not_started"},
        ],
    },
    "physics": {
        "id": "physics",
        "name": "Physics",
        "color": "#059669",
        "topics": [
            {"id": 201, "title": "Kinematics",              "difficulty": 4,  "completion": 100, "status": "done"},
            {"id": 202, "title": "Newton's Laws",           "difficulty": 5,  "completion": 100, "status": "done"},
            {"id": 203, "title": "Work, Energy & Power",    "difficulty": 6,  "completion": 80,  "status": "in_progress"},
            {"id": 204, "title": "Momentum & Collisions",   "difficulty": 6,  "completion": 50,  "status": "in_progress"},
            {"id": 205, "title": "Rotational Motion",       "difficulty": 8,  "completion": 0,   "status": "not_started"},
            {"id": 206, "title": "Electrostatics",          "difficulty": 8,  "completion": 0,   "status": "not_started"},
            {"id": 207, "title": "Electromagnetic Waves",   "difficulty": 9,  "completion": 0,   "status": "not_started"},
        ],
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def priority_score(topic: dict) -> float:
    """Higher score → show first within a column."""
    remaining = 1 - topic["completion"] / 100
    difficulty_norm = topic["difficulty"] / 10
    return remaining * (0.6 + 0.4 * difficulty_norm)


def subject_completion(subject: dict) -> int:
    topics = subject["topics"]
    if not topics:
        return 0
    return round(sum(t["completion"] for t in topics) / len(topics))


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def dashboard():
    subjects = []
    for subj in SUBJECTS.values():
        subjects.append({
            **subj,
            "overall_completion": subject_completion(subj),
            "topic_count": len(subj["topics"]),
        })
    subjects.sort(key=lambda s: s["name"])
    return render_template("dashboard.html", subjects=subjects)


@app.route("/subjects/<subject_id>")
def subject(subject_id: str):
    subj = SUBJECTS.get(subject_id)
    if subj is None:
        abort(404)

    columns = {
        "not_started": {"label": "Not Started", "topics": []},
        "in_progress":  {"label": "In Progress", "topics": []},
        "done":         {"label": "Done",         "topics": []},
    }

    for topic in subj["topics"]:
        col_key = topic["status"]
        if col_key in columns:
            columns[col_key]["topics"].append({
                **topic,
                "priority": priority_score(topic),
            })

    # Sort each column highest priority first
    for col in columns.values():
        col["topics"].sort(key=lambda t: t["priority"], reverse=True)

    return render_template(
        "subject.html",
        subject=subj,
        columns=columns,
        overall_completion=subject_completion(subj),
    )


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
