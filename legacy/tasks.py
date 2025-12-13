# tasks.py
import datetime

# Base in-game date; day_index = 0 corresponds to this
BASE_DATE = datetime.date(2025, 1, 1)


def day_to_date(day_index: int) -> datetime.date:
    return BASE_DATE + datetime.timedelta(days=day_index)


class Task:
    """
    Generic timed task assigned to one member of staff.
    """

    def __init__(
        self,
        name,
        assignee,
        start_day,
        duration_days,
        description="",
        task_type="generic",
        payload=None,
    ):
        self.name = name
        self.assignee = assignee
        self.start_day = start_day
        self.duration_days = duration_days
        self.end_day = start_day + duration_days
        self.description = description
        self.status = "Active"  # Active / Completed

        # Extra info so we can react differently to different tasks
        self.task_type = task_type   # e.g. "generic", "facility_build"
        self.payload = payload or {} # free-form dict

    def remaining_days(self, current_day: int) -> int:
        return max(0, self.end_day - current_day)


class TaskManager:
    def __init__(self):
        self.tasks: list[Task] = []

    # ---- creation / querying ----

    def create_task(
        self,
        name,
        assignee,
        start_day,
        duration_days,
        description="",
        task_type="generic",
        payload=None,
    ):
        task = Task(
            name,
            assignee,
            start_day,
            duration_days,
            description=description,
            task_type=task_type,
            payload=payload,
        )
        self.tasks.append(task)

        # mark personnel as busy
        assignee.current_task = task
        assignee.busy_until_day = task.end_day
        return task

    def active_tasks(self, current_day: int):
        return [
            t for t in self.tasks
            if t.status == "Active" and t.end_day > current_day
        ]

    def tasks_ending_on(self, day_index: int):
        """Tasks that complete exactly on this day."""
        return [t for t in self.tasks if t.status == "Active" and t.end_day == day_index]

    # ---- time control (Football Manager style "Continue") ----

    def advance_to_next_event(self, current_day: int):
        """
        Advance time to the next 'event day'.

        If there are active tasks, we jump to the earliest completion day.
        If there are no tasks, we just go forward one day.

        Returns: (new_day, finished_tasks_list)
        """
        active = self.active_tasks(current_day)
        if not active:
            return current_day + 1, []

        next_end = min(t.end_day for t in active)
        new_day = next_end
        finished = []

        for t in active:
            if t.end_day == next_end:
                t.status = "Completed"
                finished.append(t)
                # free the assignee
                if t.assignee.current_task is t:
                    t.assignee.current_task = None
                if getattr(t.assignee, "busy_until_day", 0) <= new_day:
                    t.assignee.busy_until_day = new_day

        return new_day, finished


# ---- Role classification & role-specific tasks ----

def _classify_position(position: str) -> str:
    """Roughly map concrete positions to a role."""
    p = position.lower()
    if "research" in p or "scientist" in p:
        return "research"
    if "security" in p or "guard" in p or "officer" in p:
        return "security"
    if "medic" in p or "medical" in p or "doctor" in p or "surgeon" in p:
        return "medical"
    if "director" in p or "administrator" in p or "coordinator" in p or "chief" in p:
        return "administration"
    return "general"


def get_tasks_for_person(person):
    """
    Return a list of task definitions suitable for this person.

    Each item is a dict:
        {"name": str, "duration": int, "description": str}
    """
    role = _classify_position(getattr(person, "position", ""))

    if role == "research":
        return [
            {
                "name": "Study Assigned Anomaly",
                "duration": 3,
                "description": "Laboratory research on currently contained anomalies; "
                               "update threat profiles and containment procedures.",
            },
            {
                "name": "Analyze Containment Logs",
                "duration": 2,
                "description": "Review incident logs and experiment data for emerging patterns.",
            },
        ]
    elif role == "security":
        return [
            {
                "name": "High-Risk Site Patrol",
                "duration": 1,
                "description": "Routine patrol of high-priority containment sectors.",
            },
            {
                "name": "Tactical Response Drills",
                "duration": 3,
                "description": "Live-fire and breach response exercises with security teams.",
            },
        ]
    elif role == "medical":
        return [
            {
                "name": "Medical Check-Ups",
                "duration": 1,
                "description": "Scheduled physical examinations for on-site personnel.",
            },
            {
                "name": "Psychological Evaluations",
                "duration": 2,
                "description": "Assess mental stability of staff exposed to anomalies.",
            },
        ]
    elif role == "administration":
        return [
            {
                "name": "Strategic Briefings",
                "duration": 1,
                "description": "High-level planning meetings with department heads.",
            },
            {
                "name": "Policy & Protocol Review",
                "duration": 3,
                "description": "Audit of containment procedures and emergency protocols.",
            },
        ]
    else:  # general / fallback
        return [
            {
                "name": "General Site Duty",
                "duration": 1,
                "description": "Routine assistance with administrative and logistic tasks.",
            },
            {
                "name": "Cross-Department Training",
                "duration": 2,
                "description": "Multi-disciplinary training to improve overall site readiness.",
            },
        ]
