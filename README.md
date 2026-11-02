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

Output from running `python main.py` (one owner with 90 minutes, two pets, five tasks; Luna's medication is set to overlap Mochi's walk on purpose):

```
All tasks in the order they were added:
  Time   Task            Pet       Min  Priority Due
  --------------------------------------------------------
  08:00  Breakfast       Mochi      10  high     2026-11-01
  07:30  Morning walk    Mochi      30  high     2026-11-01
  16:00  Grooming        Mochi      45  low      2026-11-01
  18:00  Play session    Luna       20  medium   2026-11-01
  07:45  Medication      Luna        5  high     2026-11-01

All tasks sorted by time:
  Time   Task            Pet       Min  Priority Due
  --------------------------------------------------------
  07:30  Morning walk    Mochi      30  high     2026-11-01
  07:45  Medication      Luna        5  high     2026-11-01
  08:00  Breakfast       Mochi      10  high     2026-11-01
  16:00  Grooming        Mochi      45  low      2026-11-01
  18:00  Play session    Luna       20  medium   2026-11-01

==========================================================
  Today's Schedule for Jordan
==========================================================
  Time   Task            Pet       Min  Priority Due
  --------------------------------------------------------
  07:30  Morning walk    Mochi      30  high     2026-11-01
  07:45  Medication      Luna        5  high     2026-11-01
  08:00  Breakfast       Mochi      10  high     2026-11-01
  18:00  Play session    Luna       20  medium   2026-11-01

Plan for Jordan (65 of 90 minutes used):
  1. Morning walk for Mochi at 07:30 (30 min) [high] - scheduled in priority order and fits in the time left.
  2. Medication for Luna at 07:45 (5 min) [high] - scheduled in priority order and fits in the time left.
  3. Breakfast for Mochi at 08:00 (10 min) [high] - scheduled in priority order and fits in the time left.
  4. Play session for Luna at 18:00 (20 min) [medium] - scheduled in priority order and fits in the time left.
Skipped:
  - Grooming for Mochi (45 min) [low] - not enough time left after higher-priority tasks.
Warnings:
  ! Medication for Luna at 07:45 overlaps Morning walk for Mochi (07:30, 30 min).

Luna's tasks only:
  Time   Task            Pet       Min  Priority Due
  --------------------------------------------------------
  07:45  Medication      Luna        5  high     2026-11-01
  18:00  Play session    Luna       20  medium   2026-11-01

Completed Morning walk; next one is due 2026-11-02.
Pending tasks after completing the walk:
  Time   Task            Pet       Min  Priority Due
  --------------------------------------------------------
  07:30  Morning walk    Mochi      30  high     2026-11-02
  07:45  Medication      Luna        5  high     2026-11-01
  08:00  Breakfast       Mochi      10  high     2026-11-01
  16:00  Grooming        Mochi      45  low      2026-11-01
  18:00  Play session    Luna       20  medium   2026-11-01

Completed tasks:
  Time   Task            Pet       Min  Priority Due
  --------------------------------------------------------
  07:30  Morning walk    Mochi      30  high     2026-11-01
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
collected 16 items
tests\test_pawpal.py ................                                    [100%]
============================= 16 passed in 0.09s ==============================
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_priority()`, `Scheduler.sort_by_time()` | The plan is chosen by priority (then preferred time, then shortest first). `sort_by_time()` uses `sorted()` with a lambda key on the `HH:MM` string (times are zero-padded when a task is created, so `7:30` becomes `07:30` and string order is time order), with untimed tasks last. |
| Filtering | `Scheduler.filter_tasks(pet_name, completed)`, `Scheduler.generate_plan(on)` | Filter by pet, by completion status, or both. The plan only includes pending tasks due by that day, and tasks that don't fit in the owner's remaining time are skipped. |
| Conflict handling | `Scheduler.detect_conflicts()` | Sorts timed tasks by start and flags any task that starts before an earlier one has ended. Tasks that only touch (08:00 end, 08:00 start) are fine. Conflicts are **warnings only**: both tasks stay in the plan and the owner decides. |
| Recurring tasks | `Task.mark_complete()`, `Scheduler.mark_task_complete()`, `Pet.complete_task()` | Completing a `daily` task adds a new copy to the same pet due one day later (`timedelta(days=1)`); `weekly` adds 7 days, and `once` doesn't repeat. The next date counts from the later of the old due date and today, so an overdue task doesn't come back already overdue and an early completion doesn't shift the schedule. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
