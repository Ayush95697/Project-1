## Adaptive Diagnostic Engine (1D IRT)

This project is a 1-dimensional (1D) adaptive diagnostic backend designed for an intern-level AI systems assignment. It uses **FastAPI**, **MongoDB**, and a simple **Item Response Theory (IRT)**-inspired update rule to estimate a student's ability and select questions adaptively.

### Tech Stack

- **Backend**: FastAPI (Python 3.10+)
- **Database**: MongoDB (Atlas or local) via `pymongo`
- **Config**: `python-dotenv`, Pydantic settings
- **LLM**: Groq API (for optional study plan generation)

---

## Setup Instructions

### 1. Clone and install

```bash
git clone <your-repo-url>
cd <repo-folder>

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Edit `.env`:

- **MONGODB_URI**: connection string to your MongoDB instance (Atlas or local)
- **MONGODB_DB_NAME**: database name (default `adaptive_diagnostic`)
- **GROQ_API_KEY** (optional but recommended): for AI-generated study plans
- **GROQ_MODEL**: e.g. `llama-3.1-8b-instant`

If `GROQ_API_KEY` is not set, the engine will still run; study plans will simply be omitted.

### 3. Seed the question bank

```bash
python -m seed.seed_questions
```

This seeds **20+ GRE-style questions** across:

- **Algebra**
- **Arithmetic**
- **Vocabulary**
- **Geometry**
- **Logic**

The questions are deliberately spread across difficulty bands:

- **Easy**: 0.1–0.3
- **Medium**: 0.4–0.6
- **Hard**: 0.7–0.9
- **Very hard**: ~1.0

### 4. Run the server

```bash
uvicorn app.main:app --reload
```

Server will run at `http://127.0.0.1:8000`.

---

## Data Model Overview (MongoDB)

### `questions` collection

Example document:

```json
{
  "_id": "q1",
  "question_text": "Solve for x: 2x + 3 = 11",
  "options": ["x=2", "x=3", "x=4", "x=5"],
  "correct_answer": "x=4",
  "difficulty": 0.3,
  "topic": "Algebra",
  "tags": ["linear equation", "basic algebra"]
}
```

Constraints and design:

- **`difficulty`** is always in \[0.1, 1.0\].
- Difficulties are **distributed** (easy → very hard) to enable meaningful adaptive behavior.
- Mixed **topics** and **tags** support downstream analytics.
- Indexes:
  - `difficulty` (ascending)
  - `_id` (unique)

### `user_sessions` collection

Example document:

```json
{
  "_id": "session_uuid",
  "ability_score": 0.5,
  "questions_answered": [
    {
      "question_id": "q1",
      "selected_answer": "x=4",
      "is_correct": true,
      "difficulty": 0.3,
      "topic": "Algebra"
    }
  ],
  "current_question_id": "q2",
  "status": "in_progress",
  "created_at": "2026-03-11T12:00:00Z",
  "completed_at": null,
  "study_plan": {
    "step_1": "...",
    "step_2": "...",
    "step_3": "..."
  }
}
```

Indexes:

- `_id` (unique per session)
- `status` (for potential analytics / admin views)

---

## Adaptive Algorithm Explanation

This engine implements a **1D IRT-style adaptive diagnostic**. It is not a naive “+0.1 / –0.1” rule; it uses a logistic model and a gradient-style update.

### 1. Ability Representation

- Every student has a latent **ability score** \(\theta\) in \[0.1, 1.0\].
- New sessions start with:

```text
theta_0 = 0.5
```

This is a neutral prior representing mid-level proficiency.

### 2. Logistic Probability of Correctness

For a given question with difficulty \(b\) and student ability \(\theta\), the probability of answering correctly is:

\[
P(\text{correct} \mid \theta, b) = \frac{1}{1 + e^{-(\theta - b)}}
\]

- When \(\theta = b\): \(P = 0.5\)
- When \(\theta \gg b\): \(P \to 1\)
- When \(\theta \ll b\): \(P \to 0\)

This gives a **smooth, differentiable** mapping from ability/difficulty differences to expected correctness.

### 3. Ability Update Rule (IRT-inspired)

After each answer:

1. Compute the **expected** probability of correctness under the current model:

   \[
   \text{expected} = P(\text{correct} \mid \theta, b)
   \]

2. Define **actual** as:

   \[
   \text{actual} =
   \begin{cases}
   1 & \text{if the answer is correct} \\
   0 & \text{otherwise}
   \end{cases}
   \]

3. Perform a small gradient-style update:

   ```python
   new_theta = theta + learning_rate * (actual - expected)
   new_theta = max(0.1, min(1.0, round(new_theta, 3)))
   ```

Interpretation:

- If a student answers a **hard question correctly**, `expected` is small, so `(actual - expected)` is large and positive → **ability increases more**.
- If they miss an **easy question**, `expected` is large, so `(actual - expected)` is large and negative → **ability decreases more**.
- If performance matches expectation, updates are small (model is already calibrated).

This is loosely analogous to a **stochastic gradient ascent step** on the log-likelihood of observed responses under the logistic IRT model.

### 4. Question Selection Logic

After updating ability:

1. Gather all **unanswered questions** for the session.
2. Compute the absolute difference between each question’s difficulty and the current ability:

   ```python
   remaining.sort(key=lambda q: abs(q["difficulty"] - ability))
   next_question = remaining[0]
   ```

3. Select the item with **minimum |difficulty – ability|**.

Why this works:

- The logistic curve is steepest around \(P = 0.5\), which corresponds to **difficulty ≈ ability**.
- Asking questions near the current ability gives **maximum information** about the student’s true skill, sharpening the estimate quickly.

### 5. Termination Criteria

The diagnostic ends when:

- The student has answered **10 questions**, **or**
- There are **no remaining questions** in the bank.

On termination:

- `status` is set to `"completed"`.
- `completed_at` is populated.
- A summary is computed:
  - Final ability score.
  - Overall accuracy.
  - Topic-wise breakdown (per-topic accuracy, counts).
  - Highest difficulty reached.

---

## AI Study Plan Generation

After a session completes, the backend:

1. Computes:
   - Final **ability**.
   - Overall **accuracy**.
   - **Topics with most mistakes** (weak topics).
   - **Highest difficulty** reached.
2. Constructs a **structured prompt**:

```text
A student completed an adaptive diagnostic test.

Final Ability Score: {ability}
Accuracy: {accuracy}%
Topics with most mistakes: {weak_topics}
Highest Difficulty Reached: {max_difficulty}

Generate a clear 3-step personalized learning plan.
Make it practical and concise.
```

3. Sends this to the LLM (via Groq) asking it to respond with strictly:

```json
{
  "step_1": "...",
  "step_2": "...",
  "step_3": "..."
}
```

4. Parses the JSON and stores it as:
   - `study_plan` embedded in the `user_sessions` document.
   - A structured object included in the `/result/{session_id}` API response.

If the Groq API key is missing or an error occurs:

- The error is **logged**.
- The rest of the result is still returned.
- `study_plan` is simply `null` / omitted.

---

## API Documentation

Base path: `/api/test`

### 1. `POST /api/test/start-test`

**Description**: Create a new session, initialize ability at `0.5`, and select the first question closest to difficulty `0.5`.

**Response** (`application/json`):

```json
{
  "session_id": "uuid",
  "ability_score": 0.5,
  "question": {
    "question_id": "q10",
    "question_text": "Which number is a solution to the inequality 3x - 2 > 7?",
    "options": ["x=2", "x=3", "x=4", "x=1"],
    "difficulty": 0.5,
    "topic": "Algebra"
  }
}
```

The `correct_answer` is **never** returned to the client.

---

### 2. `GET /api/test/next-question/{session_id}`

**Description**: Return the current question for a session (if still in progress).

**Success Response**:

```json
{
  "question_id": "q10",
  "question_text": "...",
  "options": ["..."],
  "difficulty": 0.5,
  "topic": "Algebra"
}
```

**Error Responses**:

- `404 Not Found`: session not found or invalid.
- `400/409`: if the test is already completed (depending on context).

---

### 3. `POST /api/test/submit-answer`

**Payload**:

```json
{
  "session_id": "uuid",
  "question_id": "q10",
  "selected_answer": "x=4"
}
```

**Flow**:

1. Validate session and question.
2. Reject if:
   - Session does not exist (`404`).
   - Session already completed (`409`).
   - Question does not match current question (`400`).
   - Question was already answered in this session (`409`).
3. Check correctness and update ability using the IRT rule.
4. Append answer to history.
5. Either:
   - Select the **next question** using |difficulty – ability|, or
   - Mark session as **completed** (>=10 questions or no remaining).

**Success Response (intermediate)**:

```json
{
  "session_id": "uuid",
  "is_correct": true,
  "ability_score": 0.56,
  "next_question": {
    "question_id": "q11",
    "question_text": "...",
    "options": ["..."],
    "difficulty": 0.6,
    "topic": "Algebra"
  },
  "completed": false,
  "result": null
}
```

**Success Response (final)**:

```json
{
  "session_id": "uuid",
  "is_correct": false,
  "ability_score": 0.62,
  "next_question": null,
  "completed": true,
  "result": {
    "ability_score": 0.62,
    "accuracy": 0.7,
    "total_answered": 10,
    "topic_breakdown": {
      "Algebra": { "total": 5, "correct": 4, "accuracy": 0.8 },
      "Geometry": { "total": 3, "correct": 2, "accuracy": 0.67 }
    },
    "highest_difficulty": 0.9,
    "study_plan": {
      "step_1": "...",
      "step_2": "...",
      "step_3": "..."
    }
  }
}
```

---

### 4. `GET /api/test/result/{session_id}`

**Description**: Fetch the final result for a completed session.

**Response**:

```json
{
  "session_id": "uuid",
  "ability_score": 0.62,
  "accuracy": 0.7,
  "total_answered": 10,
  "topic_breakdown": {
    "Algebra": { "total": 5, "correct": 4, "accuracy": 0.8 },
    "Geometry": { "total": 3, "correct": 2, "accuracy": 0.67 }
  },
  "highest_difficulty": 0.9,
  "study_plan": {
    "step_1": "...",
    "step_2": "...",
    "step_3": "..."
  }
}
```

**Error Responses**:

- `404 Not Found`: session does not exist.
- `500 Internal Server Error`: session not yet completed or database error.

---

## Error Handling Summary

The backend handles:

- **Invalid session ID** → `404 Not Found`
- **Duplicate answer submission** → `409 Conflict`
- **Question not found** → `404 Not Found`
- **Test already completed** → `409 Conflict`
- **No remaining questions** → session is gracefully completed
- **Missing API key** → study plan generation skipped (logged, no crash)
- **Database connection/index failure** → `500 Internal Server Error`

Errors are returned as FastAPI `HTTPException` responses with a structured `detail` message.

---

## Code Hygiene and Design

- **Modular architecture**:
  - `app/db.py`: Mongo client + index creation.
  - `app/models/`: Pydantic models mirroring Mongo documents.
  - `app/schemas/`: Request/response DTOs.
  - `app/services/`: Pure business logic, including:
    - `adaptive_engine.py`: IRT math and selection.
    - `question_service.py`: Question retrieval and sanitization.
    - `session_service.py`: Session lifecycle and orchestration.
    - `llm_service.py`: LLM prompt/response handling.
  - `app/routes/`: Thin FastAPI routers with no business logic.
- **Typing**: All core functions are type-annotated.
- **Config**: Centralized via Pydantic `Settings` (`app/utils/settings.py`).
- **Logging**: Used in DB and LLM layers for observability.

---

## AI Log

- **How AI tools helped**:
  - Designed the data model and indexes to support efficient difficulty-based querying.
  - Implemented the IRT-inspired ability update rule and question selection strategy.
  - Structured the LLM prompt and JSON-only contract for robust downstream parsing.
  - Organized the code into clear services, models, and routes to reflect production-style separation of concerns.
- **What remains manual / future work**:
  - Hardening for very large-scale deployments (e.g., sharding, connection pooling tuning).
  - Extending to multi-dimensional IRT (e.g., separate abilities per topic).
  - Adding detailed analytics dashboards and auth/session management on top of this core engine.

This backend is intentionally focused on **clarity of system design**, **sound adaptive logic**, and **clean AI integration**, rather than front-end features, so it can serve as a solid reference for an intern-level AI systems assignment.

