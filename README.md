# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Implementation summary

The scheduling logic lives in [`pawpal_system.py`](pawpal_system.py) and is built from four classes:

- **`Task`** is one care activity, with a description, duration, priority (low, medium, or high), an optional preferred time, a frequency, and a completion flag. It rejects unknown priorities and non-positive durations.
- **`Pet`** stores a pet's name, species, and its tasks. When a task is added, the pet tags it with its own name.
- **`Owner`** stores the owner's name, daily minutes available, preferences, and pets. `get_all_tasks()` returns every pet's tasks in one list.
- **`Scheduler`** is the brain. It reads all tasks through `Owner.get_all_tasks()`, drops completed ones, sorts the rest by priority (then preferred time, then shortest first), and adds tasks to the plan while they fit in the owner's available time. Tasks that don't fit are recorded as skipped, and `explain_plan()` says why each task was scheduled or skipped.

`main.py` builds a sample owner with two pets and prints today's schedule. Tests are in `tests/test_pawpal.py` and run with `python -m pytest`.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Output from running `python main.py` (one owner with 90 minutes, two pets, five tasks):

```
====================================================
  Today's Schedule for Jordan
====================================================
  Time   Task            Pet       Min  Priority
  ------------------------------------------------
  07:30  Morning walk    Mochi      30  high
  08:00  Breakfast       Mochi      10  high
  09:00  Medication      Luna        5  high
  18:00  Play session    Luna       20  medium
  ------------------------------------------------
  65 of 90 minutes scheduled

Plan for Jordan (65 of 90 minutes used):
  1. Morning walk for Mochi at 07:30 (30 min) [high] - scheduled in priority order and fits in the time left.
  2. Breakfast for Mochi at 08:00 (10 min) [high] - scheduled in priority order and fits in the time left.
  3. Medication for Luna at 09:00 (5 min) [high] - scheduled in priority order and fits in the time left.
  4. Play session for Luna at 18:00 (20 min) [medium] - scheduled in priority order and fits in the time left.
Skipped:
  - Grooming for Mochi (45 min) [low] - not enough time left after higher-priority tasks.
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
