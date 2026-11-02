"""PawPal+ logic layer: backend classes for owners, pets, tasks, and scheduling."""

from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta

PRIORITY_RANK = {"low": 1, "medium": 2, "high": 3}
REPEAT_DAYS = {"once": None, "daily": 1, "weekly": 7}


def time_to_minutes(time: str) -> int | None:
    """Convert an "HH:MM" time to minutes after midnight, or None if no time is set."""
    if not time:
        return None
    parsed = datetime.strptime(time, "%H:%M")
    return parsed.hour * 60 + parsed.minute


@dataclass
class Task:
    """A single pet care task (walk, feeding, meds, etc.)."""

    description: str
    duration_minutes: int
    priority: str  # a key of PRIORITY_RANK
    time: str = ""  # preferred start time as "HH:MM", or "" for any time
    frequency: str = "daily"  # a key of REPEAT_DAYS
    pet_name: str = ""  # set by Pet.add_task
    completed: bool = False
    due_date: date = field(default_factory=date.today)

    def __post_init__(self) -> None:
        """Normalize fields and reject invalid priorities, frequencies, durations, or times."""
        self.priority = self.priority.lower()
        if self.priority not in PRIORITY_RANK:
            raise ValueError(
                f"Unknown priority {self.priority!r}; use one of {list(PRIORITY_RANK)}"
            )
        self.frequency = self.frequency.lower()
        if self.frequency not in REPEAT_DAYS:
            raise ValueError(
                f"Unknown frequency {self.frequency!r}; use one of {list(REPEAT_DAYS)}"
            )
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        self.time = self.time.strip()
        try:
            minutes = time_to_minutes(self.time)
        except ValueError:
            raise ValueError(f"Invalid time {self.time!r}; use HH:MM, for example 08:00") from None
        if minutes is not None:
            self.time = f"{minutes // 60:02d}:{minutes % 60:02d}"

    def priority_value(self) -> int:
        """Return a numeric rank for this task's priority (higher = more important)."""
        return PRIORITY_RANK[self.priority]

    def start_minutes(self) -> int | None:
        """Return the preferred start as minutes after midnight, or None if untimed."""
        return time_to_minutes(self.time)

    def mark_complete(self, on: date | None = None) -> "Task | None":
        """Mark this task as done on the given day (default today) and return its next occurrence."""
        self.completed = True
        days = REPEAT_DAYS[self.frequency]
        if days is None:
            return None
        # Count from today if the task was overdue, so a late completion doesn't
        # create a next occurrence that is already overdue.
        start = max(self.due_date, on or date.today())
        return replace(self, completed=False, due_date=start + timedelta(days=days))


@dataclass
class Pet:
    """A pet and the care tasks it needs."""

    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet and tag it with this pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, description: str) -> bool:
        """Remove the first task with the given description. Return True if one was removed."""
        for i, task in enumerate(self.tasks):
            if task.description == description:
                del self.tasks[i]
                return True
        return False

    def complete_task(self, description: str, on: date | None = None) -> Task | None:
        """Complete the earliest pending task with this description and queue its next occurrence."""
        pending = [t for t in self.tasks if t.description == description and not t.completed]
        if not pending:
            raise ValueError(f"{self.name} has no pending task named {description!r}")
        task = min(pending, key=lambda t: t.due_date)
        next_task = task.mark_complete(on)
        if next_task is not None:
            self.add_task(next_task)
        return next_task


@dataclass
class Owner:
    """A pet owner, their daily time budget, and their pets."""

    name: str
    available_minutes: int
    preferences: list[str] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]


class Scheduler:
    """Builds and explains a daily care plan for an owner."""

    def __init__(self, owner: Owner) -> None:
        """Create a scheduler for the given owner with an empty plan."""
        self.owner = owner
        self.plan: list[Task] = []
        self.skipped: list[Task] = []
        self.conflicts: list[str] = []

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by priority (high first), then preferred time, then shortest first."""
        return sorted(
            tasks,
            key=lambda t: (-t.priority_value(), t.time == "", t.time, t.duration_minutes),
        )

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks in chronological order, with untimed tasks last."""
        # Task normalizes times to zero-padded "HH:MM", so comparing the strings
        # is chronological. (t.time == "") is False for timed tasks, so they come first.
        return sorted(tasks, key=lambda t: (t.time == "", t.time))

    def filter_tasks(self, pet_name: str | None = None, completed: bool | None = None) -> list[Task]:
        """Return the owner's tasks, optionally only for one pet and/or one completion status."""
        return [
            t
            for t in self.owner.get_all_tasks()
            if (pet_name is None or t.pet_name == pet_name)
            and (completed is None or t.completed == completed)
        ]

    def mark_task_complete(self, task: Task, on: date | None = None) -> Task | None:
        """Complete a task and add its next occurrence (if any) to the same pet."""
        pet = next((p for p in self.owner.pets if p.name == task.pet_name), None)
        # Check identity ("is"), not equality: two separate tasks can have identical fields.
        if pet is None or not any(t is task for t in pet.tasks):
            raise ValueError(f"{task.description!r} doesn't belong to any of {self.owner.name}'s pets")
        next_task = task.mark_complete(on)
        if next_task is not None:
            pet.add_task(next_task)
        return next_task

    def detect_conflicts(self, tasks: list[Task]) -> list[str]:
        """Return a warning for each timed task that starts before an earlier task has ended."""
        warnings = []
        # Untimed tasks can happen whenever, so only timed tasks can clash.
        timed = self.sort_by_time([t for t in tasks if t.time])
        latest = None  # the task seen so far that ends last
        latest_end = -1  # when it ends, in minutes after midnight
        for task in timed:
            start = task.start_minutes()
            end = start + task.duration_minutes
            # Tasks are in start order, so this task overlaps an earlier one exactly when
            # it starts before the latest end so far. Touching (start == end) is fine.
            if latest is not None and start < latest_end:
                warnings.append(
                    f"{task.description} for {task.pet_name} at {task.time} overlaps "
                    f"{latest.description} for {latest.pet_name} "
                    f"({latest.time}, {latest.duration_minutes} min)."
                )
            # Track the furthest end, so one long task is checked against every task inside it.
            if end > latest_end:
                latest, latest_end = task, end
        return warnings

    def generate_plan(self, on: date | None = None) -> list[Task]:
        """Choose and order tasks due by the given day (default today) that fit in the owner's time."""
        day = on or date.today()
        self.plan = []
        self.skipped = []
        remaining = self.owner.available_minutes

        # Overdue tasks (due before today) are included so they don't silently disappear.
        due = [t for t in self.filter_tasks(completed=False) if t.due_date <= day]
        # Greedy: take tasks in priority order while they fit. A task that doesn't fit is
        # skipped, but later, shorter tasks can still use the remaining time.
        for task in self.sort_by_priority(due):
            if task.duration_minutes <= remaining:
                self.plan.append(task)
                remaining -= task.duration_minutes
            else:
                self.skipped.append(task)
        # Conflicts are warnings only: both tasks stay in the plan and the owner decides.
        self.conflicts = self.detect_conflicts(self.plan)
        return self.plan

    def explain_plan(self) -> str:
        """Describe why each task was scheduled or skipped, and warn about time conflicts."""
        if not self.plan and not self.skipped:
            return f"No pending tasks to schedule for {self.owner.name}."

        used = sum(t.duration_minutes for t in self.plan)
        lines = [
            f"Plan for {self.owner.name} "
            f"({used} of {self.owner.available_minutes} minutes used):"
        ]
        for i, task in enumerate(self.plan, start=1):
            when = f" at {task.time}" if task.time else ""
            lines.append(
                f"  {i}. {task.description} for {task.pet_name}{when} "
                f"({task.duration_minutes} min) [{task.priority}] - "
                f"scheduled in priority order and fits in the time left."
            )
        if self.skipped:
            lines.append("Skipped:")
            for task in self.skipped:
                lines.append(
                    f"  - {task.description} for {task.pet_name} "
                    f"({task.duration_minutes} min) [{task.priority}] - "
                    f"not enough time left after higher-priority tasks."
                )
        if self.conflicts:
            lines.append("Warnings:")
            lines.extend(f"  ! {warning}" for warning in self.conflicts)
        return "\n".join(lines)
