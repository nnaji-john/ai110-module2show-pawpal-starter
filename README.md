# 🐾 PawPal+

PawPal+ is a Streamlit app that helps a busy pet owner plan each day's pet care. You add your pets and their care tasks, and PawPal+ picks the most important tasks that fit in the time you have, puts them in order, warns you about anything scheduled at the same time, and explains its choices.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

## ✨ Features

- **Owner and pet profiles.** One owner can have several pets, plus a daily budget of minutes for pet care.
- **Task tracking with input checks.** Each task has a description, duration, priority (low, medium, high), optional preferred time, and how often it repeats. Times like `7:30` are saved as `07:30`; invalid priorities, durations, or times such as `25:00` are rejected with a clear message.
- **Priority-based daily plan.** The scheduler takes every pending task that's due today (including overdue ones) and goes through them from highest to lowest priority, keeping each task that still fits in the owner's remaining minutes. A long task that doesn't fit doesn't block shorter tasks after it. Tasks that don't fit are listed as skipped.
- **Sorting by time.** Task lists and the plan are shown in time order, using `sorted()` with a lambda key on the `HH:MM` time. Tasks with no set time go last.
- **Filtering by pet or status.** Show one pet's tasks, only pending or only completed tasks, or both filters together.
- **Daily and weekly recurrence.** Completing a daily task creates the next one due the following day (`timedelta(days=1)`); weekly tasks repeat 7 days later, and one-time tasks don't repeat. A late completion doesn't create a task that is already overdue, and finishing early doesn't shift the schedule.
- **Conflict warnings.** The scheduler checks every pair of timed tasks across all pets and flags tasks at the same time or overlapping (for example, a 07:45 task during a 07:30 to 08:00 walk). Back-to-back tasks are fine. Conflicts are warnings, not errors: both tasks stay in the plan and the owner decides.
- **Rescheduling.** Change a task's time from the app to resolve a conflict.
- **Plan explanations.** Every planned, skipped, or conflicting task comes with a plain-language reason.

## Implementation summary

The scheduling logic lives in [`pawpal_system.py`](pawpal_system.py) and is built from four classes:

- **`Task`** (dataclass) is one care activity: description, duration, priority, optional preferred time, frequency, due date, and completion status. It checks its own fields when created, can be rescheduled, and creates its next occurrence when a recurring task is completed.
- **`Pet`** (dataclass) stores a pet's name, species, and tasks. When a task is added, the pet tags it with its own name.
- **`Owner`** (dataclass) stores the owner's name, daily minutes available, preferences, and pets. `get_all_tasks()` returns every pet's tasks in one list.
- **`Scheduler`** is the brain. It reads all tasks through `Owner.get_all_tasks()` and sorts, filters, builds the daily plan, detects conflicts, completes tasks, and explains the plan.

The class diagram is in [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd). [`app.py`](app.py) is the Streamlit interface, [`main.py`](main.py) is a command-line demo, and [`tests/test_pawpal.py`](tests/test_pawpal.py) holds the automated tests.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run

```bash
streamlit run app.py   # the app, in your browser
python main.py         # the command-line demo
python -m pytest       # the tests
```

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

Run the test suite from the project folder:

```bash
python -m pytest
```

The tests are in [`tests/test_pawpal.py`](tests/test_pawpal.py) and cover the scheduling logic in `pawpal_system.py`:

- **Building the plan:** high-priority tasks win when time is short, a skipped task doesn't block smaller ones after it, a task that exactly fills the remaining time is kept, completed and not-yet-due tasks are left out, overdue tasks are included, and regenerating doesn't duplicate tasks. Also covers an owner with no pets, a pet with no tasks, and every task being too long.
- **Sorting:** tasks come back in time order (including `7:30` before `10:00`), untimed tasks go last, tasks at the same time keep the order they were added, and the input list isn't changed.
- **Recurring tasks:** completing a daily task creates the next one for the following day, weekly adds 7 days, and once doesn't repeat. Covers overdue and early completion, month-end, year-end and leap-day rollover, and adding the next copy to the right pet.
- **Conflict detection:** flags tasks at the same time for the same pet or different pets, and partial overlaps. Back-to-back and untimed tasks are not conflicts, and conflicts never stop the plan from being built.
- **Filtering and input checks:** filtering by pet and status, and rejecting invalid priorities, frequencies, durations, and times.

Test output:

```
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\johnp\CodePath\AI110\ai110-module2show-pawpal-starter
plugins: anyio-4.16.0
collected 47 items

tests\test_pawpal.py ...............................................     [100%]

============================= 47 passed in 0.12s ==============================
```

**Confidence level: ★★★★☆ (4/5)**

All 47 tests pass, including edge cases like empty owners, same-time tasks, and date rollovers. I also checked that the tests catch real bugs by breaking the code on purpose (for example, changing `<=` to `<` in the time check); each change made at least one test fail. I'm not giving 5 stars because the Streamlit UI isn't part of the automated tests (I checked it by running it), owner preferences aren't used by the scheduler yet, and the plan orders tasks rather than assigning exact start times.

## 📐 Smarter Scheduling

All scheduling logic is in [`pawpal_system.py`](pawpal_system.py). The `Scheduler` always reads tasks through `Owner.get_all_tasks()`, so every feature works across all of the owner's pets.

| Feature | Method(s) |
|---------|-----------|
| Sorting | `Scheduler.sort_by_time()`, `Scheduler.sort_by_priority()` |
| Filtering | `Scheduler.filter_tasks()`, `Scheduler.generate_plan()` |
| Conflict detection | `Scheduler.find_conflicts()`, `Scheduler.detect_conflicts()`, `Task.reschedule()` |
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

- **`Scheduler.find_conflicts(tasks)`** checks every pair of timed tasks and returns the pairs that clash. Two tasks clash if the later one starts before the earlier one ends. **`Scheduler.detect_conflicts(tasks)`** turns those pairs into readable warning messages.
- This catches tasks at the exact same time, for the same pet or different pets, and partial overlaps such as a 07:45 task during a 07:30 to 08:00 walk.
- Tasks that only touch (one ends at 08:00, the next starts at 08:00) and tasks with no time are not conflicts.
- Conflicts are **warnings only**. The method returns readable messages instead of raising an error, both tasks stay in the plan, and `explain_plan()` lists them under "Warnings:". The app shows all conflicts together in one yellow warning box above the schedule, marks the clashing rows with ⚠️, and offers a **Change a task's time** form that uses **`Task.reschedule()`** to fix a clash.

### Recurring tasks

- Each task has a `frequency` (`daily`, `weekly`, or `once`) and a `due_date`.
- **`Scheduler.mark_task_complete(task)`** marks the task done and adds its next occurrence to the same pet. **`Pet.complete_task(description)`** does the same by task name.
- **`Task.mark_complete()`** calculates the next due date with `timedelta`: 1 day for `daily`, 7 days for `weekly`, and no repeat for `once`.
- The next date counts from whichever is later, the old due date or today. An overdue task doesn't come back already overdue, and finishing a task early doesn't shift its schedule.
- The completed task stays in the list, marked done, as a history.

## 📸 Demo Walkthrough

### What you can do in the app

The app (`streamlit run app.py`) is one page with four sections:

- **Owner:** enter your name and how many minutes you have for pet care today.
- **Pets:** add pets by name and species. A table lists each pet with its number of pending tasks. Blank and duplicate names are rejected.
- **Tasks:**
  - **Add a task** for a pet with a description, duration, priority, optional time (`HH:MM`), and frequency (daily, weekly, or once).
  - **Mark a task complete.** If it repeats, the app confirms when the next one is due.
  - **Change a task's time**, for example to fix a conflict.
  - **Browse tasks** in a table sorted by time, filtered by pet and by status (pending, completed, or all).
- **Today's Schedule:** click **Generate schedule** to see:
  - tasks planned, minutes used out of available, and number of time conflicts, with a bar showing how much of your time is used
  - a yellow box listing every time conflict with a suggested fix, or a green "No time conflicts" message
  - the plan as a table sorted by time, with ⚠️ next to clashing tasks and ✅ next to the rest
  - a note listing tasks that didn't fit today
  - a **Why this plan?** section with the full explanation

Everything you enter stays in place while the browser tab is open (it is kept in `st.session_state`).

### Example workflow

1. In **Owner**, enter `Jordan` with `60` minutes available.
2. In **Pets**, add **Mochi** (dog) and **Luna** (cat).
3. In **Tasks**, add:
   - Mochi: Morning walk, 30 min, high, `07:30`
   - Luna: Medication, 5 min, high, `07:45`
   - Mochi: Breakfast, 10 min, high, `08:00`
   - Luna: Breakfast, 5 min, high, `08:00`
   - Mochi: Grooming, 45 min, low, `16:00`
4. Click **Generate schedule**. Four tasks are planned (50 of 60 minutes). Grooming is listed as not fitting today. A yellow box reports **2 time conflicts**: Luna's 07:45 medication runs into Mochi's 07:30 walk, and the two breakfasts are both at 08:00. Those rows are marked ⚠️.
5. Under **Change a task's time**, move Luna's Medication to `08:15` and generate again. Now only the breakfast conflict remains, which is fine if you feed both pets together.
6. Under **Mark a task complete**, complete Mochi's Morning walk. The app confirms that the next walk is due tomorrow.
7. In the task table, set the filters to **Mochi** and **All** to see the completed walk alongside tomorrow's new one.

### Scheduler behaviors shown

| Behavior | Where you see it |
|----------|------------------|
| Priority-based plan within the time budget | Step 4: high-priority tasks are planned and the low-priority grooming doesn't fit |
| Sorting by time | Every task table and the plan, ordered by time with untimed tasks last |
| Conflict warnings (same time and overlaps, across pets) | Step 4: the yellow warning box and ⚠️ rows |
| Rescheduling | Step 5: moving the medication clears that conflict |
| Daily recurrence | Step 6: completing the walk creates tomorrow's walk |
| Filtering by pet and status | Step 7: the task table filters |

### Command-line demo

`python main.py` runs the same scenario without the UI, with 90 minutes available. It shows tasks added out of order and then sorted, today's schedule with conflict warnings, filtering by pet and by status, and daily recurrence. The schedule part of the output:

```
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
```

The full output is in the Sample Output section above.

**Screenshot or video** *(optional)*: not included. Run `streamlit run app.py` to try the app.
