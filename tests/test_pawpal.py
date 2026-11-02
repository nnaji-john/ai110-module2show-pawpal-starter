from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


def test_mark_complete_changes_status():
    task = Task("Morning walk", 30, "high")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet("Mochi", "dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Breakfast", 10, "high"))

    assert len(pet.tasks) == 1


def make_owner(minutes=120):
    owner = Owner("Jordan", available_minutes=minutes)
    mochi, luna = Pet("Mochi", "dog"), Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    return owner, mochi, luna


def test_sort_by_time_is_chronological_with_untimed_last():
    owner, mochi, _ = make_owner()
    mochi.add_task(Task("Dinner", 10, "high", time="18:00"))
    mochi.add_task(Task("Anytime brush", 5, "low"))
    mochi.add_task(Task("Walk", 30, "high", time="7:30"))  # single-digit hour
    mochi.add_task(Task("Meds", 5, "high", time="10:00"))

    ordered = Scheduler(owner).sort_by_time(mochi.tasks)

    assert [t.description for t in ordered] == ["Walk", "Meds", "Dinner", "Anytime brush"]
    assert ordered[0].time == "07:30"


def test_invalid_time_is_rejected():
    with pytest.raises(ValueError):
        Task("Walk", 30, "high", time="8am")


def test_filter_tasks_by_pet_and_status():
    owner, mochi, luna = make_owner()
    mochi.add_task(Task("Walk", 30, "high"))
    luna.add_task(Task("Meds", 5, "high"))
    luna.add_task(Task("Brush", 10, "low", frequency="once"))
    luna.complete_task("Brush")
    scheduler = Scheduler(owner)

    assert {t.description for t in scheduler.filter_tasks(pet_name="Luna")} == {"Meds", "Brush"}
    assert [t.description for t in scheduler.filter_tasks(completed=True)] == ["Brush"]
    assert [t.description for t in scheduler.filter_tasks(pet_name="Luna", completed=False)] == ["Meds"]


def test_completing_daily_task_creates_next_day_occurrence():
    today = date(2026, 11, 1)
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Walk", 30, "high", due_date=today))

    next_task = pet.complete_task("Walk", on=today)

    assert pet.tasks[0].completed is True
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.completed is False
    assert next_task.pet_name == "Mochi"
    assert len(pet.tasks) == 2


def test_weekly_repeats_in_seven_days_and_once_does_not_repeat():
    today = date(2026, 11, 1)
    weekly = Task("Grooming", 45, "low", frequency="weekly", due_date=today)
    once = Task("Vet visit", 60, "high", frequency="once", due_date=today)

    assert weekly.mark_complete(on=today).due_date == today + timedelta(days=7)
    assert once.mark_complete(on=today) is None


def test_plan_only_includes_tasks_due_by_that_day():
    today = date(2026, 11, 1)
    owner, mochi, _ = make_owner()
    mochi.add_task(Task("Walk", 30, "high", due_date=today))
    mochi.complete_task("Walk", on=today)  # next walk is due tomorrow

    scheduler = Scheduler(owner)
    assert scheduler.generate_plan(on=today) == []
    assert [t.description for t in scheduler.generate_plan(on=today + timedelta(days=1))] == ["Walk"]


def test_overlapping_tasks_produce_one_warning():
    owner, mochi, luna = make_owner()
    mochi.add_task(Task("Walk", 30, "high", time="07:30"))
    luna.add_task(Task("Meds", 5, "high", time="07:45"))

    scheduler = Scheduler(owner)
    scheduler.generate_plan()

    assert len(scheduler.conflicts) == 1
    assert "Meds" in scheduler.conflicts[0] and "Walk" in scheduler.conflicts[0]
    assert len(scheduler.plan) == 2  # warning only; both tasks stay in the plan


def test_back_to_back_tasks_do_not_conflict():
    owner, mochi, _ = make_owner()
    mochi.add_task(Task("Walk", 30, "high", time="07:30"))
    mochi.add_task(Task("Breakfast", 10, "high", time="08:00"))

    assert Scheduler(owner).detect_conflicts(mochi.tasks) == []


def test_long_task_conflicts_with_each_task_inside_it():
    owner, mochi, luna = make_owner()
    mochi.add_task(Task("Hike", 120, "high", time="09:00"))
    luna.add_task(Task("Meds", 5, "high", time="09:30"))
    luna.add_task(Task("Lunch", 10, "high", time="10:00"))

    warnings = Scheduler(owner).detect_conflicts(owner.get_all_tasks())

    assert len(warnings) == 2
    assert all("Hike" in w for w in warnings)


def test_untimed_tasks_never_conflict():
    owner, mochi, _ = make_owner()
    mochi.add_task(Task("Brush", 10, "low"))
    mochi.add_task(Task("Play", 20, "low"))

    assert Scheduler(owner).detect_conflicts(mochi.tasks) == []


def test_overdue_daily_task_repeats_from_completion_day():
    today = date(2026, 11, 1)
    walk = Task("Walk", 30, "high", due_date=today - timedelta(days=4))

    assert walk.mark_complete(on=today).due_date == today + timedelta(days=1)


def test_early_completion_keeps_the_schedule():
    today = date(2026, 11, 1)
    grooming = Task("Grooming", 45, "low", frequency="weekly", due_date=today + timedelta(days=2))

    assert grooming.mark_complete(on=today).due_date == today + timedelta(days=9)


def test_scheduler_mark_task_complete_adds_next_occurrence_to_pet():
    today = date(2026, 11, 1)
    owner, mochi, luna = make_owner()
    walk = Task("Walk", 30, "high", due_date=today)
    mochi.add_task(walk)
    luna.add_task(Task("Walk", 15, "low", due_date=today))  # same name, other pet

    next_walk = Scheduler(owner).mark_task_complete(walk, on=today)

    assert walk.completed is True
    assert next_walk.due_date == today + timedelta(days=1)
    assert next_walk in mochi.tasks and len(mochi.tasks) == 2
    assert len(luna.tasks) == 1 and luna.tasks[0].completed is False


def test_scheduler_rejects_task_from_another_owner():
    owner, _, _ = make_owner()
    stray = Task("Walk", 30, "high")

    with pytest.raises(ValueError):
        Scheduler(owner).mark_task_complete(stray)


def test_same_time_for_different_pets_is_flagged():
    owner, mochi, luna = make_owner()
    mochi.add_task(Task("Breakfast", 10, "high", time="08:00"))
    luna.add_task(Task("Breakfast", 5, "high", time="08:00"))

    scheduler = Scheduler(owner)
    scheduler.generate_plan()

    assert len(scheduler.conflicts) == 1
    assert "same time" in scheduler.conflicts[0]
    assert "Mochi" in scheduler.conflicts[0] and "Luna" in scheduler.conflicts[0]


def test_same_time_for_same_pet_is_flagged():
    owner, mochi, _ = make_owner()
    mochi.add_task(Task("Walk", 30, "high", time="07:30"))
    mochi.add_task(Task("Meds", 5, "high", time="07:30"))

    warnings = Scheduler(owner).detect_conflicts(mochi.tasks)

    assert len(warnings) == 1
    assert "same time" in warnings[0]


def test_conflicts_do_not_crash_explain_plan():
    owner, mochi, luna = make_owner()
    mochi.add_task(Task("Walk", 30, "high", time="07:30"))
    luna.add_task(Task("Meds", 5, "high", time="07:30"))

    scheduler = Scheduler(owner)
    scheduler.generate_plan()
    text = scheduler.explain_plan()

    assert "Warnings:" in text
    assert len(scheduler.plan) == 2


# --- Building the plan ---


def test_high_priority_wins_when_time_is_short():
    owner, mochi, _ = make_owner(minutes=30)
    mochi.add_task(Task("Grooming", 30, "low"))
    mochi.add_task(Task("Walk", 30, "high"))

    scheduler = Scheduler(owner)
    scheduler.generate_plan()

    assert [t.description for t in scheduler.plan] == ["Walk"]
    assert [t.description for t in scheduler.skipped] == ["Grooming"]


def test_skipped_task_does_not_block_smaller_later_tasks():
    owner, mochi, _ = make_owner(minutes=40)
    mochi.add_task(Task("Walk", 30, "high"))
    mochi.add_task(Task("Bath", 20, "medium"))  # only 10 min left, so skipped
    mochi.add_task(Task("Brush", 10, "low"))  # still fits after the bath is skipped

    scheduler = Scheduler(owner)
    scheduler.generate_plan()

    assert [t.description for t in scheduler.plan] == ["Walk", "Brush"]
    assert [t.description for t in scheduler.skipped] == ["Bath"]


def test_task_that_exactly_fills_remaining_time_is_kept():
    owner, mochi, _ = make_owner(minutes=30)
    mochi.add_task(Task("Walk", 30, "high"))

    assert len(Scheduler(owner).generate_plan()) == 1


def test_owner_with_no_pets_gets_empty_plan():
    owner = Owner("Jordan", available_minutes=60)
    scheduler = Scheduler(owner)

    assert scheduler.generate_plan() == []
    assert scheduler.conflicts == []
    assert "No pending tasks" in scheduler.explain_plan()


def test_pet_with_no_tasks_does_not_affect_plan():
    owner, mochi, _ = make_owner()  # Luna has no tasks
    mochi.add_task(Task("Walk", 30, "high"))

    assert [t.pet_name for t in Scheduler(owner).generate_plan()] == ["Mochi"]


def test_every_task_too_long_means_empty_plan():
    owner, mochi, _ = make_owner(minutes=10)
    mochi.add_task(Task("Hike", 120, "high"))

    scheduler = Scheduler(owner)

    assert scheduler.generate_plan() == []
    assert len(scheduler.skipped) == 1


def test_completed_tasks_are_left_out_of_plan():
    owner, mochi, _ = make_owner()
    done = Task("Breakfast", 10, "high", frequency="once")
    mochi.add_task(done)
    mochi.add_task(Task("Walk", 30, "high"))
    done.mark_complete()

    assert [t.description for t in Scheduler(owner).generate_plan()] == ["Walk"]


def test_generating_twice_does_not_duplicate_tasks():
    owner, mochi, _ = make_owner(minutes=20)
    mochi.add_task(Task("Walk", 15, "high"))
    mochi.add_task(Task("Hike", 120, "low"))

    scheduler = Scheduler(owner)
    scheduler.generate_plan()
    scheduler.generate_plan()

    assert len(scheduler.plan) == 1
    assert len(scheduler.skipped) == 1


def test_overdue_tasks_are_included_in_plan():
    today = date(2026, 11, 1)
    owner, mochi, _ = make_owner()
    mochi.add_task(Task("Meds", 5, "high", due_date=today - timedelta(days=3)))

    assert len(Scheduler(owner).generate_plan(on=today)) == 1


# --- Sorting ---


def test_sort_by_time_keeps_added_order_for_same_time():
    owner, mochi, luna = make_owner()
    mochi.add_task(Task("Breakfast", 10, "high", time="08:00"))
    luna.add_task(Task("Breakfast", 5, "high", time="08:00"))

    ordered = Scheduler(owner).sort_by_time(owner.get_all_tasks())

    assert [t.pet_name for t in ordered] == ["Mochi", "Luna"]


def test_sort_by_time_handles_empty_list_and_does_not_change_input():
    owner, mochi, _ = make_owner()
    scheduler = Scheduler(owner)
    assert scheduler.sort_by_time([]) == []

    mochi.add_task(Task("Dinner", 10, "high", time="18:00"))
    mochi.add_task(Task("Walk", 30, "high", time="07:30"))
    original = list(mochi.tasks)
    scheduler.sort_by_time(mochi.tasks)

    assert mochi.tasks == original


# --- Recurring tasks ---


@pytest.mark.parametrize(
    "due, expected",
    [
        (date(2026, 1, 31), date(2026, 2, 1)),  # end of month
        (date(2026, 12, 31), date(2027, 1, 1)),  # end of year
        (date(2028, 2, 28), date(2028, 2, 29)),  # leap year
    ],
)
def test_daily_task_rolls_over_month_year_and_leap_day(due, expected):
    walk = Task("Walk", 30, "high", due_date=due)

    assert walk.mark_complete(on=due).due_date == expected


def test_next_occurrence_copies_the_task_details():
    today = date(2026, 11, 1)
    walk = Task("Walk", 30, "high", time="07:30", due_date=today)

    next_walk = walk.mark_complete(on=today)

    assert (next_walk.description, next_walk.duration_minutes, next_walk.priority, next_walk.time) == (
        "Walk", 30, "high", "07:30",
    )
    assert next_walk is not walk


def test_complete_task_picks_earliest_pending_copy():
    today = date(2026, 11, 1)
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Walk", 30, "high", due_date=today + timedelta(days=1)))
    pet.add_task(Task("Walk", 30, "high", due_date=today))

    pet.complete_task("Walk", on=today)

    assert pet.tasks[1].completed is True  # the one due today
    assert pet.tasks[0].completed is False


def test_completing_unknown_task_raises():
    pet = Pet("Mochi", "dog")

    with pytest.raises(ValueError):
        pet.complete_task("Walk")


# --- Conflict detection ---


def test_three_tasks_at_same_time_give_one_warning_per_pair():
    owner, mochi, luna = make_owner()
    mochi.add_task(Task("Breakfast", 10, "high", time="08:00"))
    mochi.add_task(Task("Meds", 5, "high", time="08:00"))
    luna.add_task(Task("Breakfast", 5, "high", time="08:00"))

    warnings = Scheduler(owner).detect_conflicts(owner.get_all_tasks())

    assert len(warnings) == 3
    assert all("same time" in w for w in warnings)


def test_no_tasks_or_one_task_has_no_conflicts():
    owner, _, _ = make_owner()
    scheduler = Scheduler(owner)

    assert scheduler.detect_conflicts([]) == []
    assert scheduler.detect_conflicts([Task("Walk", 30, "high", time="07:30")]) == []


# --- Filtering and input checks ---


def test_filter_by_unknown_pet_is_empty():
    owner, mochi, _ = make_owner()
    mochi.add_task(Task("Walk", 30, "high"))

    assert Scheduler(owner).filter_tasks(pet_name="Rex") == []


@pytest.mark.parametrize(
    "kwargs",
    [
        {"priority": "urgent"},
        {"frequency": "monthly"},
        {"duration_minutes": 0},
        {"time": "24:00"},
        {"time": "12:60"},
    ],
)
def test_invalid_task_fields_are_rejected(kwargs):
    fields = {"description": "Walk", "duration_minutes": 30, "priority": "high"} | kwargs

    with pytest.raises(ValueError):
        Task(**fields)


def test_priority_and_frequency_are_case_insensitive():
    task = Task("Walk", 30, "High", frequency="Daily")

    assert (task.priority, task.frequency) == ("high", "daily")
