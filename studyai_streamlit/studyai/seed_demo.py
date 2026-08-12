"""
Seed the abhi@gmail.com demo account with a realistic, self-contained
showcase: two indexed documents, quiz history, flashcards, chat history and
a week of activity — so the app has something to demo on the very first
visit, without touching any other account.

Run once, from this directory, against whichever database backend your
``.env`` points at. Point it at the SAME Turso credentials Streamlit Cloud
uses (Settings → Secrets) so the seeded account shows up on the deployed
app too — running it against local SQLite only seeds your own machine.

    cd studyai_streamlit/studyai
    venv\\Scripts\\python.exe seed_demo.py      (Windows)
    venv/bin/python seed_demo.py                (macOS/Linux)

Idempotent: if abhi@gmail.com already has documents indexed, it does
nothing and exits.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import VECTORSTORE_DIR  # noqa: E402
from database.db import Database, RemoteVectorBackend  # noqa: E402
from models.schemas import Document  # noqa: E402
from services.auth import hash_password  # noqa: E402
from services.document_processor import DocumentProcessor  # noqa: E402
from services.vectorstore import VectorStore  # noqa: E402

DEMO_EMAIL = "abhi@gmail.com"
DEMO_NAME = "Abhishek Kumar"
DEMO_PASSWORD = "StudyAI@Demo1"
DEMO_SEMESTER = "Semester 5"

OS_NOTES = """Process Scheduling in Operating Systems

A process scheduler decides which of the ready processes gets the CPU next.
The three broad categories of schedulers are the long-term scheduler, which
controls the degree of multiprogramming by deciding which jobs are admitted
to the ready queue; the short-term scheduler (CPU scheduler), which picks
the next process to run and is invoked very frequently, on the order of
milliseconds; and the medium-term scheduler, which handles swapping
processes in and out of main memory to manage the multiprogramming level.

First-Come, First-Served (FCFS) is the simplest scheduling algorithm: the
process that requests the CPU first is allocated it first, implemented with
a plain FIFO queue. Its major drawback is the convoy effect, where a long
process at the front makes every short process behind it wait, dragging
down average waiting time.

Shortest Job First (SJF) schedules the process with the smallest next CPU
burst. SJF is provably optimal for minimizing average waiting time among
non-preemptive algorithms, but it requires predicting burst length, which
is generally estimated using an exponential average of past bursts. Its
preemptive variant is called Shortest Remaining Time First (SRTF).

Round Robin (RR) assigns each process a fixed time quantum in a circular
queue; if a process doesn't finish within its quantum, it is preempted and
sent to the back of the queue. RR is designed for time-sharing systems.
A very small quantum increases context-switch overhead, while a very large
quantum makes RR degenerate into FCFS.

Priority Scheduling assigns each process a priority number and dispatches
the highest-priority ready process first. It risks starvation, where a
low-priority process may never run; the standard fix is aging, which
gradually increases the priority of processes that wait a long time.

Multilevel Queue Scheduling partitions the ready queue into several
separate queues (for example, foreground/interactive and
background/batch), each with its own scheduling algorithm, and schedules
between queues with a fixed priority or time-slicing scheme.

Deadlocks

A deadlock is a state in which a set of processes are each waiting for a
resource held by another process in the same set, so none of them can ever
proceed. Four conditions must hold simultaneously for a deadlock to occur,
known as the Coffman conditions: mutual exclusion (a resource can be held
by only one process at a time), hold and wait (a process holding at least
one resource is waiting to acquire additional resources held by others),
no preemption (a resource can only be released voluntarily by the process
holding it), and circular wait (a closed chain of processes exists, each
waiting for a resource held by the next).

Deadlock handling strategies fall into three families. Prevention negates
one of the four Coffman conditions outright, for example by requiring all
resources to be requested at once (removing hold-and-wait) or imposing a
total ordering on resource acquisition (removing circular wait). Avoidance
allows the conditions to hold but only grants requests that keep the system
in a "safe state" — the Banker's Algorithm is the classic example, checking
whether a request could still leave every process able to finish given
some future ordering. Detection and recovery lets deadlocks occur, detects
them with a resource-allocation-graph or wait-for-graph cycle check, and
then recovers by process termination or resource preemption.

A resource-allocation graph makes deadlocks visual: processes and resources
are nodes, a request edge points from a process to a resource it wants, and
an assignment edge points from a resource to the process holding it. If the
graph has a cycle and each resource type has exactly one instance, a
deadlock exists; with multiple instances per resource type, a cycle is
necessary but not sufficient for deadlock.
"""

DBMS_NOTES = """Normalization

Normalization is the process of organizing columns and tables in a
relational database to minimize data redundancy and avoid update, insert
and delete anomalies. It proceeds through a series of normal forms, each
stricter than the last.

First Normal Form (1NF) requires that every column hold only atomic,
indivisible values and that there be no repeating groups — each row/column
intersection holds exactly one value.

Second Normal Form (2NF) requires the table to be in 1NF and additionally
that every non-key attribute be fully functionally dependent on the entire
primary key, not just part of it. This condition only matters for tables
with a composite (multi-column) primary key; a partial dependency, where a
non-key column depends on only one part of the composite key, violates 2NF.

Third Normal Form (3NF) requires 2NF plus the elimination of transitive
dependencies: no non-key attribute should depend on another non-key
attribute. If column C depends on column B, and B depends on the primary
key A, then C transitively depends on A, and C should be moved to its own
table keyed on B.

Boyce-Codd Normal Form (BCNF) is a stricter version of 3NF: for every
functional dependency X → Y, X must be a superkey. BCNF resolves certain
anomalies that can survive 3NF when a table has multiple overlapping
candidate keys.

The trade-off in normalization is redundancy versus join cost: highly
normalized schemas eliminate update anomalies but require more joins at
query time, which is why data warehouses often deliberately denormalize
for read performance.

Indexing

A database index is an auxiliary data structure that speeds up data
retrieval at the cost of extra storage and slower writes, since every
insert, update or delete must also update the index. Without an index, a
query forces a full table scan.

A B-Tree (or B+-Tree, used by most relational databases) index keeps keys
in sorted order in a balanced tree, giving O(log n) lookup, range-scan and
ordered-traversal performance. B+-Trees are especially well suited to disk-
based storage because internal nodes are wide (matching the disk block
size), which keeps the tree shallow and minimizes the number of disk reads
per lookup. Leaf nodes are typically linked together, which makes range
queries (e.g. BETWEEN, ORDER BY) efficient.

A hash index maps a key to a bucket via a hash function, giving expected
O(1) lookup for exact-match equality queries, but it cannot support range
queries or ordering, since hashing intentionally scatters similar keys
apart.

A clustered index determines the physical storage order of the table's
rows — a table can have at most one, because rows can only be physically
sorted one way. A non-clustered (secondary) index is a separate structure
that stores pointers back to the actual rows, so a table can have several.

A composite index covers more than one column; the column order matters
because a composite index on (A, B) can efficiently serve queries that
filter on A alone or on A and B together, but not queries that filter on B
alone — this is called the leftmost-prefix rule, and it's one of the most
common causes of an index silently not being used.
"""


def _seed_documents(store: VectorStore, db: Database, user_id: int) -> None:
    processor = DocumentProcessor()
    for filename, subject, text in (
        ("OS_Process_Scheduling_and_Deadlocks.txt", "Operating Systems", OS_NOTES),
        ("DBMS_Normalization_and_Indexing.txt", "Database Management", DBMS_NOTES),
    ):
        document = Document(
            name=filename, subject=subject, size_bytes=len(text.encode("utf-8")),
            pages=1, chunk_count=0, status="analyzing",
        )
        chunks = processor.chunk_pages(
            [(None, text)], source=filename, subject=subject, doc_id=document.doc_id
        )
        store.add_chunks(chunks)
        document.chunk_count = len(chunks)
        document.status = "analyzed"
        store.register_document(document.doc_id, document.to_dict())
        db.add_document(user_id, document.to_dict())
    store.save()


def _seed_quiz_and_activity(db: Database, user_id: int) -> None:
    """Backdate quiz/activity rows across the last 6 days so the streak,
    accuracy-trend and daily-minutes charts have something real to show."""
    now = datetime.utcnow()
    plan = [
        # (days_ago, topic, subject, score, total, wrong, minutes)
        (5, "Process Scheduling", "Operating Systems", 6, 10,
         ["What is the convoy effect?", "Define SRTF."], 12),
        (4, "Deadlocks", "Operating Systems", 7, 10,
         ["State the four Coffman conditions."], 14),
        (3, "Normalization", "Database Management", 8, 10,
         ["What does BCNF require beyond 3NF?"], 10),
        (2, "Indexing", "Database Management", 8, 10,
         ["Why can't a hash index serve range queries?"], 9),
        (1, "Deadlocks", "Operating Systems", 9, 10,
         ["Explain the Banker's Algorithm."], 11),
        (0, "Normalization", "Database Management", 9, 10,
         ["Give an example of a transitive dependency."], 10),
    ]
    with db.connect() as connection:
        for days_ago, topic, subject, score, total, wrong, minutes in plan:
            when = now - timedelta(days=days_ago, hours=2)
            day = when.date().isoformat()
            connection.execute(
                """INSERT INTO quiz_attempts
                   (topic, subject, score, total, wrong, created_at, user_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (topic, subject, score, total,
                 __import__("json").dumps(wrong), when.isoformat(), user_id),
            )
            connection.execute(
                """INSERT INTO activity
                   (icon, text, kind, minutes, day, created_at, user_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                ("QZ", f"Quiz: {topic} — {score}/{total}", "quiz", minutes,
                 day, when.isoformat(), user_id),
            )
        # A couple of extra activity entries (upload + flashcard review days)
        # so the recent-activity feed reads naturally, not just quizzes.
        for days_ago, text, icon, kind, minutes in [
            (5, "Uploaded OS_Process_Scheduling_and_Deadlocks.txt", "UP", "upload", 2),
            (3, "Uploaded DBMS_Normalization_and_Indexing.txt", "UP", "upload", 2),
            (1, "Reviewed 6 flashcards", "FC", "review", 6),
            (0, "Asked: What are the Coffman conditions for deadlock?", "CH", "chat", 2),
        ]:
            when = now - timedelta(days=days_ago, hours=3)
            connection.execute(
                """INSERT INTO activity
                   (icon, text, kind, minutes, day, created_at, user_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (icon, text, kind, minutes, when.date().isoformat(),
                 when.isoformat(), user_id),
            )


def _seed_flashcards(db: Database, user_id: int) -> None:
    cards = [
        ("What is the convoy effect in FCFS scheduling?",
         "Short processes queue behind one long process, inflating average "
         "waiting time.", "Process Scheduling", 5, 4),
        ("Which scheduling algorithm is provably optimal for minimizing "
         "average waiting time?",
         "Shortest Job First (SJF) — non-preemptive; SRTF is its preemptive "
         "form.", "Process Scheduling", 4, 3),
        ("What does 'aging' fix in priority scheduling?",
         "Starvation — it gradually raises the priority of processes that "
         "have waited a long time.", "Process Scheduling", 3, 2),
        ("Name the four Coffman conditions for deadlock.",
         "Mutual exclusion, hold and wait, no preemption, circular wait.",
         "Deadlocks", 5, 5),
        ("What does the Banker's Algorithm check before granting a "
         "resource request?",
         "Whether granting it still leaves the system in a safe state — "
         "every process can finish in some order.", "Deadlocks", 4, 3),
        ("What's the difference between deadlock prevention and "
         "avoidance?",
         "Prevention negates one of the four Coffman conditions outright; "
         "avoidance allows them but only grants requests that keep the "
         "system safe.", "Deadlocks", 2, 2),
        ("What does 2NF require beyond 1NF?",
         "Every non-key attribute must be fully functionally dependent on "
         "the whole primary key, not just part of a composite key.",
         "Normalization", 4, 3),
        ("What is a transitive dependency, and which normal form removes "
         "it?",
         "A non-key attribute depending on another non-key attribute "
         "instead of the key directly; 3NF removes it.", "Normalization",
         5, 4),
        ("What extra condition does BCNF add over 3NF?",
         "For every functional dependency X → Y, X must be a superkey.",
         "Normalization", 2, 1),
        ("Why are B+-Trees preferred over plain B-Trees for database "
         "indexes?",
         "Their linked, wide leaf nodes make range scans and ordered "
         "traversal efficient and match disk block sizes well.",
         "Indexing", 3, 2),
        ("Can a hash index serve a range query like BETWEEN?",
         "No — hashing scatters similar keys apart, so only exact-match "
         "lookups are supported.", "Indexing", 5, 4),
        ("What is the 'leftmost-prefix rule' for composite indexes?",
         "A composite index on (A, B) serves queries filtering on A alone "
         "or on A and B together, but not on B alone.", "Indexing", 1, 1),
    ]
    now = datetime.utcnow().isoformat()
    with db.connect() as connection:
        for front, back, topic, box, reviews in cards:
            connection.execute(
                """INSERT INTO flashcards
                   (front, back, topic, source, box, reviews, created_at, user_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (front, back, topic, "", box, reviews, now, user_id),
            )


def _seed_chat(db: Database, user_id: int) -> None:
    session_id = "demo-session-01"
    when = datetime.utcnow() - timedelta(hours=3)
    exchanges = [
        ("user", "What are the four Coffman conditions for deadlock?", []),
        ("assistant",
         "A deadlock requires all four of these to hold at once [1]: "
         "mutual exclusion, hold and wait, no preemption, and circular "
         "wait. Breaking any single one is enough to prevent deadlock.",
         [{"chunk": {"source": "OS_Process_Scheduling_and_Deadlocks.txt",
                      "page": None}, "score": 0.81}]),
        ("user", "How does the Banker's Algorithm relate to this?", []),
        ("assistant",
         "It's a deadlock *avoidance* strategy: it lets the four "
         "conditions hold, but only grants a resource request if the "
         "system stays in a 'safe state' — meaning there's still some "
         "order in which every process could finish [1].",
         [{"chunk": {"source": "OS_Process_Scheduling_and_Deadlocks.txt",
                      "page": None}, "score": 0.77}]),
    ]
    with db.connect() as connection:
        for role, content, sources in exchanges:
            connection.execute(
                """INSERT INTO conversations
                   (session_id, role, content, sources, created_at, user_id)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (session_id, role, content, __import__("json").dumps(sources),
                 when.isoformat(), user_id),
            )
            when += timedelta(seconds=20)


def main() -> None:
    db = Database()
    existing = db.get_user_by_email(DEMO_EMAIL)
    if existing:
        user_id = existing["id"]
        print(f"Demo account already exists (id={user_id}).")
    else:
        password_hash, password_salt = hash_password(DEMO_PASSWORD)
        user = db.create_user(
            DEMO_NAME, DEMO_EMAIL, password_hash, password_salt, DEMO_SEMESTER
        )
        user_id = user["id"]
        print(f"Created demo account {DEMO_EMAIL} (id={user_id}).")

    if db.list_documents(user_id):
        print("Demo account already has data indexed — nothing else to do.")
        print(f"Sign in with: {DEMO_EMAIL} / {DEMO_PASSWORD}")
        return

    remote = RemoteVectorBackend(db, user_id)
    store = VectorStore(store_dir=VECTORSTORE_DIR / str(user_id), remote=remote)
    store.load()

    print("Indexing demo documents (downloads the embedding model on first run)...")
    _seed_documents(store, db, user_id)
    print("Seeding quiz history and activity...")
    _seed_quiz_and_activity(db, user_id)
    print("Seeding flashcards...")
    _seed_flashcards(db, user_id)
    print("Seeding a sample chat...")
    _seed_chat(db, user_id)

    print()
    print("Demo account ready.")
    print(f"  Email:    {DEMO_EMAIL}")
    print(f"  Password: {DEMO_PASSWORD}")
    print("Sign up separately with your own email for a clean account with no demo data.")


if __name__ == "__main__":
    main()
