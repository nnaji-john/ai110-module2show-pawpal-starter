# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

Based on the PawPal+ scenario, a busy pet owner should be able to perform three core actions:

1. **Set up an owner and pet profile.** The user enters basic information about themselves (such as their name and how much time they have for pet care each day) and about their pet (such as its name and species). This gives the app the context it needs to plan care for a specific pet within the owner's real constraints.

2. **Add and manage pet care tasks.** The user can add care tasks like a walk, a feeding, medication, enrichment, or grooming, and edit them later. Each task records at least how long it takes and how important it is (its priority), so the app knows what has to happen and what can be skipped if time runs short.

3. **Generate and view today's care plan.** The user asks the app to build a daily schedule. The app picks and orders tasks based on the time available, task priority, and the owner's preferences, then shows the plan clearly and explains why it chose it, for example why a high-priority medication came before an optional play session or why a task was left out.

My initial UML design uses four classes. An Owner has zero or more Pets, each Pet has zero or more Tasks, and a Scheduler plans for one Owner by working with that owner's tasks. I deliberately kept the design small, covering only what the three core actions need.

- **Task** (dataclass) represents one care activity, such as a walk or a feeding. It stores a description, a duration in minutes, a priority (low, medium, or high), an optional preferred time, how often it repeats, and whether it is completed. It can convert its priority to a number for sorting and can mark itself complete.
- **Pet** (dataclass) stores a pet's name and species and owns that pet's list of tasks. It is responsible for adding and removing tasks.
- **Owner** (dataclass) stores the owner's name, how many minutes they have for pet care each day, their preferences, and their pets. It is responsible for adding pets and for gathering every task across all pets, so other classes don't need to dig through each pet.
- **Scheduler** holds the logic. Given an Owner, it sorts tasks by priority, builds a daily plan that fits within the owner's available time, keeps track of which tasks it skipped, and explains why each task was scheduled or left out.

**b. Design changes**

Yes. After drafting the class skeleton, I asked my AI assistant to review `pawpal_system.py` for missing relationships and logic bottlenecks, and I made two changes:

1. **Added `pet_name` to Task.** Because `Owner.get_all_tasks()` combines every pet's tasks into one list, a task lost track of which pet it belonged to. With more than one pet, the plan couldn't say whose walk it was. Now `Pet.add_task()` tags each task with the pet's name, so the scheduler and its explanation can refer to the right pet.
2. **Added a shared `PRIORITY_RANK` table** (`low` = 1, `medium` = 2, `high` = 3). Priority is stored as text, so without one central mapping the ranking rule could be duplicated or a misspelled priority could slip through. `Task.priority_value()` will use this table.

The review also flagged things to handle during implementation rather than in the structure: `generate_plan()` must reset its plan and skipped lists before rebuilding, completed tasks should be left out of the plan, and owner preferences are not used by any method yet.

The design kept growing as I added the smarter scheduling features. The main changes, all reflected in `diagrams/uml_final.mmd`:

3. **Renamed `title` to `description` and added `time`, `frequency`, and `due_date` to Task.** Sorting by time, recurrence, and "only plan what's due today" all needed this information on the task itself.
4. **Added `Scheduler.mark_task_complete()`.** At first the app found the pet itself and completed the first task with a matching name, which could complete the wrong one. Routing completion through the Scheduler, which finds the right pet through the Owner, fixed that and kept the UI thin.
5. **Split conflict detection into `find_conflicts()` and `detect_conflicts()`.** The first returns the clashing pairs of tasks and the second turns them into messages. The app needed the actual tasks to mark clashing rows with ⚠️, and parsing warning text to find them would have been fragile.
6. **Added `Task.reschedule()` and a shared `normalize_time()` helper.** The conflict warning needed a real way to fix a clash, and rescheduling had to use the same time checks as creating a task.

The core structure (Owner has Pets, Pet has Tasks, Scheduler plans for one Owner through `get_all_tasks()`) never changed, which told me the initial design was a sound base.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

My scheduler considers these constraints:

- **Available time.** The owner's daily minutes are a hard limit. A task is only planned if it fits in the minutes left.
- **Priority.** Tasks are considered from high to low priority, so important tasks claim time first.
- **Due date and completion.** Only pending tasks due today or earlier are planned. Overdue tasks are included so they don't silently disappear, and completed tasks are left out.
- **Preferred time.** Times are used to break ties between tasks of the same priority, to order the plan, and to detect conflicts.

Shorter tasks win the last tie, so more small tasks can fit.

I treated time and priority as the most important constraints because they match what the scenario's busy owner actually faces: there are only so many minutes, and some care (like medication) matters more than other care (like grooming). Preferred times matter, but I made them soft. A clash produces a warning rather than blocking a task, because only the owner knows whether two tasks can be done together. Owner preferences are stored but not used yet. I left them out because "preferences" could mean many things, and I'd rather not guess at a rule that might feel arbitrary to the user.

**b. Tradeoffs**

**Conflicts are warnings, not fixes.** When two timed tasks overlap (for example, Luna's 07:45 medication during Mochi's 07:30 to 08:00 walk), the scheduler keeps both tasks in the plan and adds a warning instead of moving or dropping one. This means the plan the app shows can contain two things the owner can't do at once, and the scheduler doesn't decide how to resolve it.

This is reasonable for a pet owner because the right fix depends on things the app doesn't know. Giving a cat a pill takes a minute and might fit in the middle of a walk, or another person in the household might handle it. Automatically dropping the lower-priority task could hide something important, like medication, without the owner noticing. A clear warning keeps the owner in control and keeps the scheduler simple and predictable.

**Readability over speed in conflict detection.** I asked my AI assistant how to simplify `detect_conflicts()`. My original version sorted the tasks and made one pass, tracking the latest end time seen so far. It was fast, but the logic was hard to follow. The assistant suggested two shorter versions:

- **Compare each task only with the next one** (`itertools.pairwise`). This was the most compact, but it failed one of my tests: a two-hour hike from 09:00 overlaps both a 09:30 task and a 10:00 task, and comparing only neighbors missed the second clash.
- **Compare every pair of tasks** (`itertools.combinations`). This passed all the tests and is much easier to read. It is slower in theory, because the work grows with the square of the number of tasks, but a pet owner has at most a few dozen tasks a day, so the difference is too small to notice.

I kept the every-pair version, and wrote it as a plain loop rather than a one-line list comprehension so it stays easy to read. It also reports every clashing pair, which is more useful to the owner than my original version.

---

## 3. AI Collaboration

**a. How you used AI**

I used Claude Code in VS Code at every stage. It helped me:

- turn the README scenario into three core user actions
- draft and trim a Mermaid UML diagram, and generate the dataclass skeletons
- review the skeleton for missing relationships and implement the classes
- write the `main.py` demo
- build the sorting, filtering, recurrence, and conflict features
- connect everything to the Streamlit UI with `st.session_state`
- plan and write a 47-test suite
- update the UML and README to match the final code

The most helpful prompts were specific review questions rather than open-ended "build it" requests. Asking it to review the UML for unnecessary complexity, and to check the skeleton for missing relationships and logic bottlenecks, surfaced real problems: tasks didn't know which pet they belonged to, and priority was free text with no single ranking rule. Giving it the exact class responsibilities from the assignment (for example, that the Scheduler must read tasks through `Owner.get_all_tasks()`) also kept its code aligned with what I needed.

**b. Judgment and verification**

I didn't accept the first UML draft as-is. It included extras like a pet's age, a task category, `remove_pet()`, `get_pet()`, and an `edit_task()` method with an awkward signature. None of these were needed for the three core actions, so I cut them and kept only what the scheduler actually uses. I also deferred features until they were actually needed. For example, `frequency` was stored for a while before recurrence was built, and owner preferences are still unused.

To verify what the AI produced, I:

- **checked results by hand.** Running `python main.py`, I confirmed the numbers. For example, five planned tasks use 70 of 90 minutes, and the 45-minute grooming is skipped because only 20 minutes are left.
- **relied on automated tests.** The test suite grew from 2 tests to 47 as features were added, and every change was followed by a full `python -m pytest` run.
- **tested the tests.** I deliberately broke the code (for example, changing `<=` to `<` in the time check) and confirmed that a test failed each time.
- **ran the UI.** I clicked through the Streamlit app with Streamlit's test runner and by hand, following the README's example workflow, to check that it matched what the README claims.

**c. AI strategy**

**Most effective features.** Three Claude Code features helped most:

- **Agent mode with access to the whole project.** Many changes touched several files at once. Adding recurrence, for example, meant changing `pawpal_system.py`, `app.py`, `main.py`, the tests, the UML, and the README together, and the assistant kept them consistent in one step.
- **Running code and tests in the terminal.** The assistant didn't just write code; it ran `main.py`, `pytest`, and Streamlit's test runner and showed me the output, so I could see evidence instead of trusting claims.
- **Targeted review questions.** Asking it to review a specific file for a specific problem worked better than "build it" prompts. Examples: "missing relationships or logic bottlenecks", or "how could this algorithm be simplified?"

**A suggestion I rejected or modified.** When we planned conflict detection, the assistant laid out two options: automatically drop the lower-priority task, or only warn. Dropping is more "automatic," but I chose warnings. Silently dropping a task could hide something important like medication, and only the owner knows whether two tasks can be done together. That choice shaped the rest of the design: the scheduler stays simple and never changes the owner's tasks behind their back, and the UI focuses on making the warning clear and fixable.

A second example came from simplifying `detect_conflicts()`. The most compact suggestion, comparing each task only with the next one, failed my long-task test, so I rejected it. Instead I kept a slightly longer version that checks every pair and is easier to read.

**Chat sessions and staying organized.** The instructions suggested separate chat sessions for planning, implementation, and testing. In practice, I kept the whole project in one continuous session. What kept it organized was working in clear phases with a commit at the end of each one (class skeletons, core logic, smarter scheduling, tests), and asking for a plan before building in the bigger phases. For the algorithm and testing phases, the assistant first listed the gaps and proposed what to build, and I chose before any code was written. One long session had a real advantage: the assistant remembered earlier decisions, like conflicts being warnings. The downside is that the history gets long, and an early assumption can carry forward unquestioned. Next time I would start a fresh session for testing, so the tests are designed from the code and requirements rather than from the same reasoning that wrote the code.

**Being the lead architect.** The AI can write correct code quickly, but it doesn't decide what the system should be. My job was to:

- set the scope (four classes, only what the core actions need)
- make the judgment calls (warnings, not automatic fixes; readable code over clever code)
- insist on evidence (tests, running the demo, breaking the code on purpose)

The assistant was most useful when I gave it a clear goal and constraints and then reviewed its output critically. When a suggestion was more "Pythonic" or more automatic but less clear or less safe for the user, it was my call to say no. The quality of the final system came from those decisions as much as from the code.

---

## 4. Testing and Verification

**a. What you tested**

My 47 tests in `tests/test_pawpal.py` cover five areas:

- **Building the plan.** High priority wins when time is short. A skipped task doesn't block smaller tasks after it, and a task that exactly fills the remaining time is kept. Completed and not-yet-due tasks are left out, overdue tasks are included, and regenerating doesn't duplicate anything. Also covers an owner with no pets, a pet with no tasks, and every task being too long.
- **Sorting.** Tasks come back in time order (including `7:30` before `10:00`), untimed tasks go last, ties keep their order, and the input list isn't changed.
- **Recurring tasks.** Daily repeats the next day, weekly in 7 days, and once never. Covers overdue and early completion, month-end, year-end, and leap-day rollover, and the next copy going to the right pet.
- **Conflict detection.** Same time for one pet or different pets, partial overlaps, three tasks at once, back-to-back tasks (not a conflict), untimed tasks, and a long task overlapping several others. Rescheduling clears a conflict.
- **Input checks.** Invalid priorities, frequencies, durations, and times are rejected.

These tests matter because the scheduler's mistakes would be quiet ones. A wrong comparison or a missed overlap doesn't crash anything; it just gives the owner a wrong plan, like a skipped medication or a missing conflict warning. The tests pin down the exact boundaries where bugs hide, such as `<=` vs `<`, back-to-back vs overlapping, and December 31 to January 1.

**b. Confidence**

I'm fairly confident: about 4 out of 5. All 47 tests pass, they cover the edge cases I could think of, and they caught every bug I deliberately introduced. I'm not at 5 because the Streamlit UI isn't part of the automated test suite (I checked it by running it), and some parts of the problem aren't modeled yet.

Next, I would test:

- **Tasks that cross midnight**, like a 23:30 task lasting an hour. The scheduler currently treats each day separately.
- **The UI flows as automated tests**, using Streamlit's `AppTest`: adding pets and tasks, rescheduling, and completing tasks.
- **Two tasks with the same name for the same pet**, when removing or completing by name.
- **The date changing while the app is open**, since "today" is read when the plan is generated.

---

## 5. Reflection

**a. What went well**

I'm most satisfied with conflict handling from end to end. The scheduler finds every clash across all pets, the warning explains it in plain language, the app marks the clashing rows, and the owner can fix it with **Change a task's time** without anything being silently dropped. I'm also happy that the logic layer stayed separate from the UI. `app.py` only calls methods on `Owner`, `Pet`, `Task`, and `Scheduler`, so the same logic powers the app, the command-line demo, and the tests.

**b. What you would improve**

With another iteration I would:

- **save data between sessions.** Right now everything disappears when the browser tab closes. I'd save the owner, pets, and tasks to a JSON file.
- **let users edit and remove tasks and pets in the UI**, not just add, complete, and reschedule them.
- **assign real start times.** Tasks without a set time could be placed into free gaps, so the plan becomes a true timeline.
- **use owner preferences**, for example "no walks after 20:00" or "prefer morning tasks".

**c. Key takeaway**

Design decisions are the part that can't be delegated. The AI could write any version of the scheduler I asked for, but it was up to me to decide what the scheduler should do in the cases that matter to a real pet owner: what happens when time runs out, when tasks clash, or when a task is finished late. Settling those rules first, and writing tests that lock them in, made every later AI-generated change easier to check and trust.
