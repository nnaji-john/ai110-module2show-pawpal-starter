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
