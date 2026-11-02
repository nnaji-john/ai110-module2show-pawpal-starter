"""PawPal+ logic layer: backend classes for owners, pets, tasks, and scheduling."""

from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from itertools import combinations

PRIORITY_RANK = {"low": 1, "medium": 2, "high": 3}
REPEAT_DAYS = {"once": None, "daily": 1, "weekly": 7}


def time_to_minutes(time: str) -> int | None:
    """Convert an "HH:MM" time to minutes after midnight, or None if no time is set."""
    if not time:
        return None
    parsed = datetime.strptime(time, "%H:%M")
    return parsed.hour * 60 + parsed.minute


def normalize_time(time: str) -> str:
    """Return a time as zero-padded "HH:MM" ("7:30" -> "07:30"), or "" if blank.

    Raises:
        ValueError: if the time isn't a valid 24-hour HH:MM time.
    """
    time = time.strip()
    try:
        minutes = time_to_minutes(time)
    except ValueError:
        raise ValueError(f"Invalid time {time!r}; use HH:MM, for example 08:00") from None
    return "" if minutes is None else f"{minutes // 60:02d}:{minutes % 60:02d}"


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
        self.time = normalize_time(self.time)

    def priority_value(self) -> int:
        """Return a numeric rank for this task's priority (higher = more important)."""
        return PRIORITY_RANK[self.priority]

    def reschedule(self, time: str) -> None:
        """Change the preferred time ("" for any time), with the same checks as on creation."""
        self.time = normalize_time(time)

    def start_minutes(self) -> int | None:
        """Return the preferred start as minutes after midnight, or None if untimed."""
        return time_to_minutes(self.time)

    def mark_complete(self, on: date | None = None) -> "Task | None":
        """Mark this task as done and return its next occurrence, if it repeats.

        The next due date is counted from whichever is later, the current due date
        or the completion day, plus 1 day (daily) or 7 days (weekly). That way an
        overdue task doesn't come back already overdue, and finishing early keeps
        the schedule.

        Args:
            on: the day the task was completed. Defaults to today.

        Returns:
            A new, pending copy of this task with the next due date, or None for
            a "once" task. The caller adds it to the pet.
        """
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
        """Return tasks in chronological order, with untimed tasks last.

        Args:
            tasks: the tasks to sort. The list itself is not changed.

        Returns:
            A new list ordered by preferred time. Tasks with the same time keep
            their original order.
        """
        # Task normalizes times to zero-padded "HH:MM", so comparing the strings
        # is chronological. (t.time == "") is False for timed tasks, so they come first.
        return sorted(tasks, key=lambda t: (t.time == "", t.time))

    def filter_tasks(self, pet_name: str | None = None, completed: bool | None = None) -> list[Task]:
        """Return the owner's tasks across all pets, optionally filtered.

        Args:
            pet_name: only include this pet's tasks. None means every pet.
            completed: True for completed tasks, False for pending ones,
                None for both.

        Returns:
            The matching tasks, in pet order and then the order they were added.
        """
        return [
            t
            for t in self.owner.get_all_tasks()
            if (pet_name is None or t.pet_name == pet_name)
            and (completed is None or t.completed == completed)
        ]

    def mark_task_complete(self, task: Task, on: date | None = None) -> Task | None:
        """Complete a task and add its next occurrence (if any) to the same pet.

        Args:
            task: the exact task to complete. It must belong to one of the owner's pets.
            on: the day it was completed. Defaults to today.

        Returns:
            The newly added next occurrence, or None if the task doesn't repeat.

        Raises:
            ValueError: if the task doesn't belong to any of the owner's pets.
        """
        pet = next((p for p in self.owner.pets if p.name == task.pet_name), None)
        # Check identity ("is"), not equality: two separate tasks can have identical fields.
        if pet is None or not any(t is task for t in pet.tasks):
            raise ValueError(f"{task.description!r} doesn't belong to any of {self.owner.name}'s pets")
        next_task = task.mark_complete(on)
        if next_task is not None:
            pet.add_task(next_task)
        return next_task

    def find_conflicts(self, tasks: list[Task]) -> list[tuple[Task, Task]]:
        """Return every pair of timed tasks whose times overlap.

        Two tasks clash if the later one starts before the earlier one ends, so
        this catches tasks at the same time (for the same pet or different pets)
        and partial overlaps. Tasks that only touch, like 07:30 to 08:00 and then
        08:00, don't clash. Untimed tasks are ignored.

        Args:
            tasks: the tasks to check, from any number of pets.

        Returns:
            (earlier, later) pairs in time order, or an empty list.
        """
        pairs = []
        # Untimed tasks can happen whenever, so only timed tasks can clash.
        timed = self.sort_by_time([t for t in tasks if t.time])
        # Check every pair. A day has few tasks, so this is fast enough and easy to follow.
        # Because the list is sorted, `first` never starts after `second`.
        for first, second in combinations(timed, 2):
            first_end = first.start_minutes() + first.duration_minutes
            # Touching (second starts exactly when first ends) is not a conflict.
            if second.start_minutes() < first_end:
                pairs.append((first, second))
        return pairs

    def detect_conflicts(self, tasks: list[Task]) -> list[str]:
        """Return a readable warning for every pair of overlapping timed tasks.

        This never raises; the caller decides what to do with the warnings.

        Args:
            tasks: the tasks to check, from any number of pets.

        Returns:
            One warning message per clashing pair (see find_conflicts), or an empty list.
        """
        warnings = []
        for first, second in self.find_conflicts(tasks):
            clash = "is at the same time as" if second.time == first.time else "overlaps"
            warnings.append(
                f"{second.description} for {second.pet_name} at {second.time} {clash} "
                f"{first.description} for {first.pet_name} "
                f"({first.time}, {first.duration_minutes} min)."
            )
        return warnings

    def generate_plan(self, on: date | None = None) -> list[Task]:
        """Choose and order the tasks to do on a given day.

        Takes every pending task due on or before that day, goes through them
        in priority order, and keeps each one that still fits in the owner's
        available minutes. Tasks that don't fit go to self.skipped, and any time
        clashes in the plan are saved as warnings in self.conflicts.

        Args:
            on: the day to plan for. Defaults to today.

        Returns:
            The planned tasks in priority order (also saved in self.plan).
        """
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
