import random

def simulate(self, team):
    """
    Run the operation with the given team of Personnel.

    Updates:
        - self.status
        - self.assigned_team
        - self.result_text
        - each member.status / member.alive may change

    Returns a dict with success flag and casualty lists.
    """
    # Store team (for later display)
    self.assigned_team = list(team)

    # Scores
    team_score = self._team_effective_score(team)             # 0–100
    diff_score = self.anomaly_difficulty * 5.0                # 0–100

    # Success chance: 50% base, +/- based on score difference
    success_chance = 0.5 + (team_score - diff_score) / 100.0
    success_chance = max(0.1, min(0.9, success_chance))       # clamp

    roll = random.random()
    success = roll < success_chance

    # Casualty risk: higher when anomaly is "stronger" than team
    hazard_margin = diff_score - team_score  # positive = dangerous

    if hazard_margin <= 0:
        casualty_prob = 0.1
        death_prob = 0.0
    else:
        casualty_prob = min(0.8, 0.15 + hazard_margin / 120.0)
        death_prob = max(0.0, casualty_prob - 0.35)

    injured = []
    killed = []

    for member in team:
        r = random.random()
        if r < death_prob:
            member.status = "KIA"
            member.alive = False
            killed.append(member)
        elif r < casualty_prob:
            if getattr(member, "status", "Active") != "KIA":
                member.status = "Injured"
                injured.append(member)
        else:
            # stays Active
            pass

    if success:
        self.status = "Completed"
        outcome = "SUCCESS"
    else:
        self.status = "Failed"
        outcome = "FAILURE"

    # Build a human-readable summary
    lines = []
    lines.append(f"{outcome}: {self.anomaly_name} containment in {self.city}, {self.country}.")
    lines.append(
        f"Team score {team_score:.1f} vs anomaly difficulty {diff_score:.1f}."
    )

    if killed or injured:
        if killed:
            names = ", ".join(f"{m.fname} {m.lname}" for m in killed)
            lines.append(f"KIA: {names}.")
        if injured:
            names = ", ".join(f"{m.fname} {m.lname}" for m in injured)
            lines.append(f"Injured: {names}.")
    else:
        lines.append("No casualties reported.")

    self.result_text = " ".join(lines)

    return {
        "success": success,
        "team_score": team_score,
        "difficulty_score": diff_score,
        "injured": injured,
        "killed": killed,
        "outcome_text": self.result_text,
    }