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

Output from running `python main.py` (one owner with 90 minutes, two pets, six tasks; Luna's medication overlaps Mochi's walk and both pets' breakfasts are at 08:00, on purpose):

```
All tasks in the order they were added:
  Time   Task            Pet       Min  Priority Due
  --------------------------------------------------------
  08:00  Breakfast       Mochi      10  high     2026-11-01
  07:30  Morning walk    Mochi      30  high     2026-11-01
  16:00  Grooming        Mochi      45  low      2026-11-01
  18:00  Play session    Luna       20  medium   2026-11-01
  07:45  Medication      Luna        5  high     2026-11-01
  08:00  Breakfast       Luna        5  high     2026-11-01

All tasks sorted by time:
  Time   Task            Pet       Min  Priority Due
  --------------------------------------------------------
  07:30  Morning walk    Mochi      30  high     2026-11-01
  07:45  Medication      Luna        5  high     2026-11-01
  08:00  Breakfast       Mochi      10  high     2026-11-01
  08:00  Breakfast       Luna        5  high     2026-11-01
  16:00  Grooming        Mochi      45  low      2026-11-01
  18:00  Play session    Luna       20  medium   2026-11-01

==========================================================
  Today's Schedule for Jordan
==========================================================
  Time   Task            Pet       Min  Priority Due
  --------------------------------------------------------
  07:30  Morning walk    Mochi      30  high     2026-11-01
  07:45  Medication      Luna        5  high     2026-11-01
  08:00  Breakfast       Luna        5  high     2026-11-01
  08:00  Breakfast       Mochi      10  high     2026-11-01
  18:00  Play session    Luna       20  medium   2026-11-01

Plan for Jordan (70 of 90 minutes used):
  1. Morning walk for Mochi at 07:30 (30 min) [high] - scheduled in priority order and fits in the time left.
  2. Medication for Luna at 07:45 (5 min) [high] - scheduled in priority order and fits in the time left.
  3. Breakfast for Luna at 08:00 (5 min) [high] - scheduled in priority order and fits in the time left.
  4. Breakfast for Mochi at 08:00 (10 min) [high] - scheduled in priority order and fits in the time left.
  5. Play session for Luna at 18:00 (20 min) [medium] - scheduled in priority order and fits in the time left.
Skipped:
  - Grooming for Mochi (45 min) [low] - not enough time left after higher-priority tasks.
Warnings:
  ! Medication for Luna at 07:45 overlaps Morning walk for Mochi (07:30, 30 min).
  ! Breakfast for Mochi at 08:00 is at the same time as Breakfast for Luna (08:00, 5 min).

Luna's tasks only:
  Time   Task            Pet       Min  Priority Due
  --------------------------------------------------------
  07:45  Medication      Luna        5  high     2026-11-01
  08:00  Breakfast       Luna        5  high     2026-11-01
  18:00  Play session    Luna       20  medium   2026-11-01

Completed Morning walk; next one is due 2026-11-02.
Pending tasks after completing the walk:
  Time   Task            Pet       Min  Priority Due
  --------------------------------------------------------
  07:30  Morning walk    Mochi      30  high     2026-11-02
  07:45  Medication      Luna        5  high     2026-11-01
  08:00  Breakfast       Mochi      10  high     2026-11-01
  08:00  Breakfast       Luna        5  high     2026-11-01
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
collected 19 items
tests\test_pawpal.py ...................                                 [100%]
============================= 19 passed in 0.09s ==============================
```

## 📐 Smarter Scheduling

All scheduling logic is in [`pawpal_system.py`](pawpal_system.py). The `Scheduler` always reads tasks through `Owner.get_all_tasks()`, so every feature works across all of the owner's pets.

| Feature | Method(s) |
|---------|-----------|
| Sorting | `Scheduler.sort_by_time()`, `Scheduler.sort_by_priority()` |
| Filtering | `Scheduler.filter_tasks()`, `Scheduler.generate_plan()` |
| Conflict detection | `Scheduler.detect_conflicts()` |
| Recurring tasks | `Task.mark_complete()`, `Scheduler.mark_task_complete()`, `Pet.complete_task()` |

### Sorting

- **`Scheduler.sort_by_time(tasks)`** returns tasks in time order using `sorted()` with a lambda key: `key=lambda t: (t.time == "", t.time)`.
  - Times are saved as zero-padded `HH:MM` when a task is created (`7:30` becomes `07:30`), so comparing the strings gives time order.
  - Tasks with no time go last, because `t.time == ""` is `False` for timed tasks and `False` sorts before `True`.
- **`Scheduler.sort_by_priority(tasks)`** decides which tasks make the plan: high priority first, then earlier preferred time, then shorter tasks.

### Filtering

- **`Scheduler.filter_tasks(pet_name=None, completed=None)`** returns the owner's tasks for one pet, by completion status (`True` for done, `False` for pending), or both. Leaving a filter as `None` means "any".
- **`Scheduler.generate_plan(on=None)`** only plans pending tasks due on or before that day (today by default). It goes through them in priority order and keeps each one that still fits in the owner's available minutes; the rest are listed as skipped.

### Conflict detection

- **`Scheduler.detect_conflicts(tasks)`** checks every pair of timed tasks. Two tasks clash if the later one starts before the earlier one ends.
- This catches tasks at the exact same time, for the same pet or different pets, and partial overlaps such as a 07:45 task during a 07:30 to 08:00 walk.
- Tasks that only touch (one ends at 08:00, the next starts at 08:00) and tasks with no time are not conflicts.
- Conflicts are **warnings only**. The method returns readable messages instead of raising an error, both tasks stay in the plan, and `explain_plan()` lists them under "Warnings:". The app shows each one as a yellow warning.

### Recurring tasks

- Each task has a `frequency` (`daily`, `weekly`, or `once`) and a `due_date`.
- **`Scheduler.mark_task_complete(task)`** marks the task done and adds its next occurrence to the same pet. **`Pet.complete_task(description)`** does the same by task name.
- **`Task.mark_complete()`** calculates the next due date with `timedelta`: 1 day for `daily`, 7 days for `weekly`, and no repeat for `once`.
- The next date counts from whichever is later, the old due date or today. An overdue task doesn't come back already overdue, and finishing a task early doesn't shift its schedule.
- The completed task stays in the list, marked done, as a history.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
