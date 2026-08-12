"""
Seed the abhi@gmail.com demo account with a realistic, self-contained
showcase: four indexed documents (full subject coverage), a month of quiz
history tuned to land around 80% exam readiness, flashcards across every
subject, a 30-day activity streak touching every agent, and a sample chat
— so the app looks like it's been in real use, without touching any other
account.

Run once, from this directory, against whichever database backend your
``.env`` points at. Point it at the SAME Turso credentials Streamlit Cloud
uses (Settings → Secrets) so the seeded account shows up on the deployed
app too — running it against local SQLite only seeds your own machine.

    cd studyai_streamlit/studyai
    venv\\Scripts\\python.exe seed_demo.py      (Windows)
    venv/bin/python seed_demo.py                (macOS/Linux)

Always resets the demo account's data to this exact canonical state first,
so it's safe (and expected) to re-run whenever you want the showcase back
to a known-good baseline — e.g. after someone's played around with it.
"""

from __future__ import annotations

import json
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

CN_NOTES = """The OSI Model

The OSI (Open Systems Interconnection) reference model divides network
communication into seven layers, each responsible for a specific part of
getting data from one device to another: Physical (raw bit transmission
over a medium), Data Link (framing, MAC addressing and error detection on
a single link, e.g. Ethernet), Network (logical addressing and routing
between networks, e.g. IP), Transport (end-to-end delivery, e.g. TCP and
UDP), Session (establishing, managing and tearing down sessions),
Presentation (data translation, encryption and compression), and
Application (the interface end-user software actually talks to, e.g.
HTTP, FTP, DNS).

The practical TCP/IP model used on the real Internet collapses this into
four layers — Link, Internet, Transport, Application — but the OSI model
remains the standard reference for discussing where a given protocol or
problem sits. A common way to reason about failures is layer by layer: a
cable fault is Physical, a switching loop is Data Link, an unreachable
subnet is Network, a refused connection is Transport, and a malformed
request is Application.

Encapsulation is how data moves down the stack on the sender: each layer
wraps the data from the layer above with its own header (and sometimes
trailer), producing progressively larger units — segments (Transport)
become packets (Network) become frames (Data Link) become bits (Physical).
The receiver reverses this, stripping headers layer by layer
(decapsulation) as data moves back up its own stack.

TCP Congestion Control

TCP treats congestion control as essential to prevent a shared network
from collapsing under too much traffic — every TCP sender maintains a
congestion window (cwnd) that caps how much unacknowledged data it can
have in flight, independent of the receiver's advertised window (which
caps for receiver buffer capacity instead).

Slow start begins each connection (or restarts after a timeout) with a
small cwnd and doubles it every round-trip time as ACKs arrive, growing
exponentially until it hits a threshold (ssthresh) or a loss is detected.

Congestion avoidance takes over once cwnd passes ssthresh: instead of
doubling, cwnd grows by roughly one segment per round-trip time (additive
increase), a much more conservative linear growth meant to probe for
extra capacity without overshooting badly.

On packet loss, classic TCP treats it as a congestion signal and reacts
one of two ways. A retransmission timeout is treated as severe: ssthresh
is set to half the current cwnd, and cwnd collapses back to slow start's
starting point. Three duplicate ACKs (fast retransmit) are treated as a
milder signal: the lost segment is retransmitted immediately without
waiting for a timeout, ssthresh is halved, and cwnd is set to the new
ssthresh rather than collapsing all the way (fast recovery) — this whole
additive-increase/multiplicative-decrease pattern is what gives TCP
throughput its characteristic sawtooth graph over time.
"""

AI_NOTES = """Search Algorithms

Uninformed (blind) search explores a state space with no domain knowledge
beyond the problem definition. Breadth-First Search (BFS) expands nodes
level by level using a FIFO queue, guaranteeing the shallowest goal is
found first and that the solution is optimal when all step costs are
equal, but its memory use grows exponentially with depth. Depth-First
Search (DFS) expands as deep as possible along a branch before
backtracking, using a LIFO stack (or recursion); it uses far less memory
than BFS but is neither complete (it can loop forever in infinite or
cyclic spaces without cycle checking) nor optimal. Uniform-Cost Search
generalizes BFS to weighted edges by always expanding the lowest
cumulative-cost node next (effectively Dijkstra's algorithm), which is
both complete and optimal whenever costs are non-negative.

Informed (heuristic) search uses a heuristic function h(n) estimating the
cost from node n to the goal, to search more efficiently than blind
search. Greedy Best-First Search always expands the node with the lowest
h(n), which is fast but neither complete nor optimal, since it can be
misled by a heuristic that looks good locally. A* Search expands the node
with the lowest f(n) = g(n) + h(n), where g(n) is the actual cost so far
and h(n) is the heuristic estimate to the goal; A* is guaranteed optimal
provided h(n) is admissible (never overestimates the true remaining
cost), which is why choosing a good admissible heuristic matters so much
in practice.

Types of Machine Learning

Supervised learning trains on labeled examples — each input paired with
the correct output — and the model learns a mapping to predict labels for
new, unseen inputs. Classification predicts a discrete category;
regression predicts a continuous value. Common algorithms include
linear/logistic regression, decision trees, support vector machines and
neural networks, all evaluated against a held-out test set to estimate
how well they generalize rather than merely memorize the training data
(overfitting).

Unsupervised learning works on unlabeled data, looking for structure
without being told the "right answer." Clustering (e.g. k-means,
hierarchical clustering) groups similar points together; dimensionality
reduction (e.g. PCA) compresses many correlated features into fewer
components while preserving as much variance as possible.

Reinforcement learning trains an agent to choose actions in an
environment to maximize cumulative reward through trial and error, rather
than from a fixed labeled dataset. The agent observes a state, takes an
action, receives a reward and a new state, and gradually learns a policy
that improves long-term reward — the classic exploration-vs-exploitation
trade-off is central here: trying new actions to discover better rewards
versus repeating actions already known to work well.

The bias-variance trade-off cuts across all three: a model with high bias
is too simple to capture the underlying pattern (underfitting), while a
model with high variance fits the training data's noise too closely to
generalize (overfitting).
"""

# (filename, subject, text, days_ago it was "uploaded")
DOCUMENTS = [
    ("OS_Process_Scheduling_and_Deadlocks.txt", "Operating Systems", OS_NOTES, 29),
    ("DBMS_Normalization_and_Indexing.txt", "Database Management", DBMS_NOTES, 27),
    ("CN_OSI_Model_and_TCP_Congestion_Control.txt", "Computer Networks", CN_NOTES, 24),
    ("AI_Search_Algorithms_and_Types_of_ML.txt", "Artificial Intelligence", AI_NOTES, 21),
]

# (topic, subject, sample missed-question bank)
TOPICS = [
    ("Process Scheduling", "Operating Systems",
     ["What is the convoy effect?", "Define SRTF."]),
    ("Deadlocks", "Operating Systems",
     ["State the four Coffman conditions.", "What does the Banker's Algorithm check?"]),
    ("Normalization", "Database Management",
     ["What does BCNF require beyond 3NF?", "Give an example of a transitive dependency."]),
    ("Indexing", "Database Management",
     ["Why can't a hash index serve range queries?", "What is the leftmost-prefix rule?"]),
    ("OSI Model", "Computer Networks",
     ["List the seven OSI layers in order.", "What is encapsulation?"]),
    ("TCP Congestion Control", "Computer Networks",
     ["What triggers fast retransmit?", "How does slow start grow cwnd?"]),
    ("Search Algorithms", "Artificial Intelligence",
     ["Why is A* optimal with an admissible heuristic?", "Is DFS complete?"]),
    ("Types of Machine Learning", "Artificial Intelligence",
     ["Classification vs. regression — what's the difference?",
      "Define the exploration-exploitation trade-off."]),
]

# (days_ago, topic_index, score, total) — 15 attempts over the last month,
# trending upward, landing overall accuracy around 75% (~80% exam
# readiness once combined with full 4-document subject coverage).
QUIZ_SCHEDULE = [
    (27, 0, 6, 10), (25, 1, 6, 10), (23, 2, 6, 10), (21, 3, 7, 10),
    (19, 4, 7, 10), (17, 5, 7, 10), (15, 6, 7, 10), (13, 7, 7, 10),
    (11, 0, 8, 10), (9, 2, 8, 10), (7, 4, 8, 10), (5, 6, 8, 10),
    (3, 1, 9, 10), (1, 3, 9, 10), (0, 5, 9, 10),
]

# Rotates through every agent so a month of activity shows the whole app
# in use, not just Quiz. {topic}/{subject} get filled in per day.
FILLER_TEMPLATES = [
    ("CH", "chat", "Asked about {topic} in Chat with Docs", 2),
    ("NT", "notes", "Generated notes on {topic}", 6),
    ("FC", "review", "Reviewed flashcards on {topic}", 4),
    ("PL", "planner", "Built a study plan for {subject}", 5),
    ("RV", "revision", "Generated a revision sheet on {topic}", 8),
    ("WT", "analysis", "Analysed weak topics in {subject}", 4),
    ("IV", "interview", "Practiced Interview Mode on {subject}", 7),
    ("CS", "analysis", "Ran a cross-subject analysis", 6),
]

FLASHCARDS = [
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
    ("List the seven OSI layers, bottom to top.",
     "Physical, Data Link, Network, Transport, Session, Presentation, "
     "Application.", "OSI Model", 4, 3),
    ("What's the difference between encapsulation and decapsulation?",
     "Encapsulation wraps data with each layer's header going down the "
     "stack; decapsulation strips them going back up on the receiver.",
     "OSI Model", 3, 2),
    ("What does TCP do differently after a timeout vs. three duplicate "
     "ACKs?",
     "A timeout collapses cwnd back to slow start; duplicate ACKs "
     "trigger fast retransmit/recovery, a milder cwnd cut.",
     "TCP Congestion Control", 3, 2),
    ("Why does cwnd grow exponentially in slow start but linearly in "
     "congestion avoidance?",
     "Slow start probes capacity fast by doubling each RTT; congestion "
     "avoidance is more cautious once near the known threshold.",
     "TCP Congestion Control", 2, 1),
    ("Is Breadth-First Search optimal?",
     "Yes, when all step costs are equal — it always finds the "
     "shallowest goal first.", "Search Algorithms", 4, 3),
    ("What makes a heuristic 'admissible' for A*?",
     "It never overestimates the true remaining cost to the goal.",
     "Search Algorithms", 3, 2),
    ("Classification vs. regression: what's the core difference?",
     "Classification predicts a discrete category; regression predicts "
     "a continuous value.", "Types of Machine Learning", 3, 2),
    ("What is the bias-variance trade-off?",
     "High bias underfits (too simple); high variance overfits (fits "
     "noise). Good models balance the two.", "Types of Machine Learning",
     2, 1),
]


def _reset_demo_data(db: Database, user_id: int) -> None:
    """Wipe this user's rows from every per-user table, so re-seeding
    always lands on the exact same canonical showcase state."""
    with db.connect() as connection:
        for table in ("documents", "conversations", "quiz_attempts",
                      "flashcards", "activity"):
            connection.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))


def _seed_documents(store: VectorStore, db: Database, user_id: int) -> None:
    processor = DocumentProcessor()
    now = datetime.utcnow()
    for filename, subject, text, days_ago in DOCUMENTS:
        document = Document(
            name=filename, subject=subject, size_bytes=len(text.encode("utf-8")),
            pages=1, chunk_count=0, status="analyzing",
            uploaded_at=(now - timedelta(days=days_ago, hours=1)).isoformat(),
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


def _seed_activity_and_quizzes(db: Database, user_id: int) -> None:
    """A 30-day activity streak (every agent, not just Quiz) plus 15 quiz
    attempts tuned to land overall accuracy around 75%."""
    now = datetime.utcnow()

    with db.connect() as connection:
        # Quiz attempts + their matching activity entries.
        for days_ago, topic_index, score, total in QUIZ_SCHEDULE:
            topic, subject, wrong_bank = TOPICS[topic_index]
            when = now - timedelta(days=days_ago, hours=2)
            num_wrong = max(0, total - score)
            missed = wrong_bank[: min(num_wrong, len(wrong_bank))]
            connection.execute(
                """INSERT INTO quiz_attempts
                   (topic, subject, score, total, wrong, created_at, user_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (topic, subject, score, total, json.dumps(missed),
                 when.isoformat(), user_id),
            )
            connection.execute(
                """INSERT INTO activity
                   (icon, text, kind, minutes, day, created_at, user_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                ("QZ", f"Quiz: {topic} — {score}/{total}", "quiz", total * 2,
                 when.date().isoformat(), when.isoformat(), user_id),
            )

        # Upload activity, backdated to match each document's upload day.
        for filename, subject, _text, days_ago in DOCUMENTS:
            when = now - timedelta(days=days_ago, hours=1)
            connection.execute(
                """INSERT INTO activity
                   (icon, text, kind, minutes, day, created_at, user_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                ("UP", f"Uploaded {filename}", "upload", 2,
                 when.date().isoformat(), when.isoformat(), user_id),
            )

        # One filler entry per day for all 30 days, guaranteeing the streak
        # and rotating through every agent for variety.
        for day_offset in range(30):
            days_ago = 29 - day_offset
            topic, subject, _wrong = TOPICS[day_offset % len(TOPICS)]
            icon, kind, template, minutes = FILLER_TEMPLATES[day_offset % len(FILLER_TEMPLATES)]
            text = template.format(topic=topic, subject=subject)
            when = now - timedelta(days=days_ago, hours=5)
            connection.execute(
                """INSERT INTO activity
                   (icon, text, kind, minutes, day, created_at, user_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (icon, text, kind, minutes, when.date().isoformat(),
                 when.isoformat(), user_id),
            )


def _seed_flashcards(db: Database, user_id: int) -> None:
    now = datetime.utcnow().isoformat()
    with db.connect() as connection:
        for front, back, topic, box, reviews in FLASHCARDS:
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
                (session_id, role, content, json.dumps(sources),
                 when.isoformat(), user_id),
            )
            when += timedelta(seconds=20)


def main() -> None:
    db = Database()
    existing = db.get_user_by_email(DEMO_EMAIL)
    if existing:
        user_id = existing["id"]
        print(f"Demo account exists (id={user_id}) — resetting to the canonical showcase state...")
        _reset_demo_data(db, user_id)
    else:
        password_hash, password_salt = hash_password(DEMO_PASSWORD)
        user = db.create_user(
            DEMO_NAME, DEMO_EMAIL, password_hash, password_salt, DEMO_SEMESTER
        )
        user_id = user["id"]
        print(f"Created demo account {DEMO_EMAIL} (id={user_id}).")

    remote = RemoteVectorBackend(db, user_id)
    store = VectorStore(store_dir=VECTORSTORE_DIR / str(user_id), remote=remote)
    store.clear()  # wipe any previous local + remote vector data first

    print("Indexing 4 demo documents (downloads the embedding model on first run)...")
    _seed_documents(store, db, user_id)
    print("Seeding a 30-day activity streak and 15 quiz attempts...")
    _seed_activity_and_quizzes(db, user_id)
    print("Seeding flashcards across all 4 subjects...")
    _seed_flashcards(db, user_id)
    print("Seeding a sample chat...")
    _seed_chat(db, user_id)

    scored = sum(s for _, _, s, _ in QUIZ_SCHEDULE)
    total = sum(t for *_, t in QUIZ_SCHEDULE)
    accuracy = scored / total
    readiness = round((accuracy * 0.7 + 1.0 * 0.3) * 100)

    print()
    print("Demo account ready.")
    print(f"  Email:            {DEMO_EMAIL}")
    print(f"  Password:         {DEMO_PASSWORD}")
    print(f"  Documents:        {len(DOCUMENTS)} (full subject coverage)")
    print(f"  Quiz attempts:    {len(QUIZ_SCHEDULE)}, accuracy {accuracy:.0%}")
    print(f"  Exam readiness:   ~{readiness}% (computed by the app, not hardcoded)")
    print(f"  Activity streak:  30 days")
    print("Sign up separately with your own email for a clean account with no demo data.")


if __name__ == "__main__":
    main()
