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

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

I used Claude Code in VS Code at every stage so far. It helped me turn the README scenario into three core user actions, drafted a Mermaid UML diagram for my four classes, generated the dataclass skeletons in `pawpal_system.py`, reviewed the skeleton for missing relationships, filled in the method logic, wrote `main.py`, and drafted my first two pytest tests.

The most helpful prompts were specific review questions rather than open-ended "build it" requests. Asking it to review the UML for unnecessary complexity, and to check the skeleton for missing relationships and logic bottlenecks, surfaced real problems: tasks didn't know which pet they belonged to, and priority was free text with no single ranking rule. Giving it the exact class responsibilities from the assignment (for example, that the Scheduler must read tasks through `Owner.get_all_tasks()`) also kept its code aligned with what I needed.

**b. Judgment and verification**

I didn't accept the first UML draft as-is. It included extras like a pet's age, a task category, `remove_pet()`, `get_pet()`, and an `edit_task()` method with an awkward signature. None of these were needed for the three core actions, so I cut them and kept only what the scheduler actually uses. I also left some suggestions for later instead of building them now: owner preferences are stored but not yet used, `frequency` is stored but daily and weekly tasks are scheduled the same way, and the plan orders tasks rather than assigning real start times or checking for time conflicts.

To verify the results, I:

- ran a two-pet example to check that completed tasks were left out, that generating a plan twice didn't duplicate tasks, and that a priority typed as "High" still worked;
- ran `python main.py` and checked the schedule by hand: the four tasks that fit use 65 of 90 minutes, and the 45-minute low-priority grooming is correctly skipped because only 25 minutes were left;
- ran `python -m pytest` to confirm that `mark_complete()` changes a task's status and that `add_task()` increases a pet's task count.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
