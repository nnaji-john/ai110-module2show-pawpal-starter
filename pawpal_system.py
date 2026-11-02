"""PawPal+ logic layer: backend classes for owners, pets, tasks, and scheduling."""

from dataclasses import dataclass, field

PRIORITY_RANK = {"low": 1, "medium": 2, "high": 3}


@dataclass
class Task:
    """A single pet care task (walk, feeding, meds, etc.)."""

    description: str
    duration_minutes: int
    priority: str  # a key of PRIORITY_RANK
    time: str = ""  # preferred start time as "HH:MM", or "" for any time
    frequency: str = "daily"  # e.g. "daily" or "weekly"
    pet_name: str = ""  # set by Pet.add_task
    completed: bool = False

    def __post_init__(self) -> None:
        """Normalize the priority and reject invalid priorities or durations."""
        self.priority = self.priority.lower()
        if self.priority not in PRIORITY_RANK:
            raise ValueError(
                f"Unknown priority {self.priority!r}; use one of {list(PRIORITY_RANK)}"
            )
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")

    def priority_value(self) -> int:
        """Return a numeric rank for this task's priority (higher = more important)."""
        return PRIORITY_RANK[self.priority]

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True


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
        for task in self.tasks:
            if task.description == description:
                self.tasks.remove(task)
                return True
        return False


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

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by priority (high first), then preferred time, then shortest first."""
        return sorted(
            tasks,
            key=lambda t: (-t.priority_value(), t.time or "99:99", t.duration_minutes),
        )

    def generate_plan(self) -> list[Task]:
        """Choose and order tasks that fit within the owner's available time."""
        self.plan = []
        self.skipped = []
        remaining = self.owner.available_minutes

        pending = [t for t in self.owner.get_all_tasks() if not t.completed]
        for task in self.sort_by_priority(pending):
            if task.duration_minutes <= remaining:
                self.plan.append(task)
                remaining -= task.duration_minutes
            else:
                self.skipped.append(task)
        return self.plan

    def explain_plan(self) -> str:
        """Describe why each task was scheduled or skipped."""
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
        return "\n".join(lines)
