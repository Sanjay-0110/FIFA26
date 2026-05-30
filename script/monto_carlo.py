"""
monte_carlo.py — Full tournament Monte Carlo simulator for FIFA 26 World Cup
 
Architecture
------------
TournamentSimulator.run(n)
  └─ simulate_tournament()          x N
       ├─ simulate_group_stage()    → standings per group, 8 best 3rd-place teams
       └─ simulate_knockout()       → R32 → R16 → QF → SF → Final
 
Output (from run())
-------------------
Per-team dict with probabilities:
  {
    "Argentina": {
      "group_advance": 0.87,
      "r32":          0.87,
      "r16":          0.71,
      "quarterfinal": 0.52,
      "semifinal":    0.38,
      "finalist":     0.26,
      "winner":       0.17,
    },
    ...
  }
 
Notes
-----
- Group tiebreakers: points → GD → GF → head-to-head points → head-to-head GD → random
- 3rd-place qualification: FIFA 2026 takes 8 best 3rd-placed teams from 12 groups.
  Comparison criteria: points → GD → GF → confederation (not implemented; random used).
- Knockout draws are deterministic per the FIFA 26 bracket seeding (see BRACKET below).
  In a full implementation, swap BRACKET for the real drawn fixture list.
- ELO ratings are NOT updated between simulated matches within a single tournament run.
  Phase 2 (live retraining) will add post-match ELO mutation.
"""

import random
from collections import defaultdict
from typing import Optional
from itertools import combinations
 
from FIFA26.script.poisson_model import simulate_score, penalty_winner, compute_lambda
from team_rating import TEAMS, get_group

GROUP: dict[str, list[str]] = {
    group: list(get_group(group).keys())
    for group in "ABCDEFGHIJKL"
}

# print(GROUP)
# Format: list of (slot_a, slot_b) where each slot is a string key into
# the `slots` dict built by simulate_group_stage():
#   "W_A"  = winner of group A
#   "RU_B" = runner-up of group B
#   "T3_X" = one of the 8 best third-place teams (assigned after group stage)
PLACEHOLDER_R32 = [
    ("W_A",  "RU_B"),
    ("W_C",  "RU_D"),
    ("W_E",  "RU_F"),
    ("W_G",  "RU_H"),
    ("W_I",  "RU_J"),
    ("W_K",  "RU_L"),
    ("W_B",  "RU_A"),
    ("W_D",  "RU_C"),
    ("W_F",  "RU_E"),
    ("W_H",  "RU_G"),
    ("W_J",  "RU_I"),
    ("W_L",  "RU_K"),
    # 8 best 3rd-place teams fill slots T3_0 … T3_7 vs remaining R32 spots.
    # Simplified: pair them against the next available group winner/runner-up.
    # In production, replace with the official seeding table.
    ("T3_0", "W_A"),   # placeholder — overwritten by real bracket
    ("T3_1", "W_C"),
    ("T3_2", "W_E"),
    ("T3_3", "W_G"),
    ("T3_4", "W_I"),
    ("T3_5", "W_K"),
    ("T3_6", "RU_A"),
    ("T3_7", "RU_C"),
]

def simulate_match_group(team_a: str, team_b:str)-> tuple[int, int]:
     """Simulate a group-stage match. Returns (goals_a, goals_b)."""
     lam_a, lam_b = compute_lambda(team_a, team_b, neutral=True)
     return simulate_score(lam_a, lam_b)
def _simulate_match_knockout(team_a: str, team_b: str) -> str:
    """
    Simulate a knockout match. Draws go to penalties.
    Returns the name of the winning team.
    """
    lam_a, lam_b = compute_lambda(team_a, team_b, neutral=True)
    ga, gb = simulate_score(lam_a, lam_b)
    if ga > gb:
        return team_a
    elif gb > ga:
        return team_b
    else:
        return penalty_winner(team_a, team_b)

def _sort_group(standings: dict[str, dict], h2h: dict) -> list[str]:
    """
    Sort group standings by:
      1. Points
      2. Goal difference
      3. Goals for
      4. Head-to-head points (among tied teams)
      5. Head-to-head goal difference (among tied teams)
      6. Random (coin flip)
    Returns ordered list of team names (best → worst).
    """

    teams = list(standings.keys())

    def sort_key(team: str):
        s = standings[team]
        return(
            s["pts"], s['gd'], s['gf']
        )
    
     # Group into tiers by (pts, gd, gf) then apply h2h within ties
    teams.sort(key=sort_key, reverse=True)
    # Simple tiebreaker: shuffle within equal (pts, gd, gf) blocks
    # A full implementation would recurse on h2h sub-tables — sufficient for Monte Carlo

    result = []
    i = 0
    while i < len(teams):
        j = i + 1
        while j < len(teams) and sort_key(teams[j]) == sort_key(teams[i]):
            j += 1
        block = teams[i:j]
        if len(block) > 1:
            random.shuffle(block)   # random tiebreak — acceptably close for simulation
        result.extend(block)
        i = j
 
    return result

# ── Group stage ───────────────────────────────────────────────────────────────
def simulate_group_stage() -> tuple[dict[str, str], list[str]]:
    """
    Simulate all 12 groups. Returns:
      slots     : dict mapping slot strings ("W_A", "RU_A", …) → team name
      third_place_teams : list of all 12 third-placed teams (unsorted)

    """
    slots: dict[str, str] = {}
    third_place_entries: list[dict] = []

    for group_id, teams in GROUP.items():
        # Initialise standings
        standings: dict[str, dict] = {
            t: {"pts": 0, "gd": 0, "gf": 0, "ga": 0} for t in teams
        }
        h2h: dict[tuple, dict] = {}   # (ta, tb) → {pts_a, gd_a}
 
        # Play every pair
        for team_a, team_b in combinations(teams, 2):
            ga, gb = simulate_match_group(team_a, team_b)
 
            # Update standings
            standings[team_a]["gf"] += ga
            standings[team_a]["ga"] += gb
            standings[team_a]["gd"] += ga - gb
            standings[team_b]["gf"] += gb
            standings[team_b]["ga"] += ga
            standings[team_b]["gd"] += gb - ga
 
            if ga > gb:
                standings[team_a]["pts"] += 3
            elif gb > ga:
                standings[team_b]["pts"] += 3
            else:
                standings[team_a]["pts"] += 1
                standings[team_b]["pts"] += 1
 
            # Store h2h
            h2h[(team_a, team_b)] = {"ga": ga, "gb": gb}
 
        ordered = _sort_group(standings, h2h)
        slots[f"W_{group_id}"]  = ordered[0]
        slots[f"RU_{group_id}"] = ordered[1]

        s = standings[ordered[2]]
        third_place_entries.append({
            "team":  ordered[2],
            "pts":   s["pts"],
            "gd":    s["gd"],
            "gf":    s["gf"],
            "group": group_id,
        })
    
    # Pick 8 best third-place teams (pts → gd → gf → random)
    third_place_entries.sort(
        key=lambda x: (x["pts"], x["gd"], x["gf"]),
        reverse=True
    )
    best8 = third_place_entries[:8]
    random.shuffle(best8)   # randomise seeding order within equal records
 
    for i, entry in enumerate(best8):
        slots[f"T3_{i}"] = entry["team"]
 
    all_thirds = [e["team"] for e in third_place_entries]
    return slots, all_thirds

def simulate_knockout(slots: dict[str, str]) -> dict[str, int]:
    """
    Simulate the knockout bracket from R32 to Final.
    Returns a dict mapping team → highest round reached (as an int):
      3 = R32 exit, 4 = R16 exit, 5 = QF exit, 6 = SF exit, 7 = finalist, 8 = winner
    """

    round_reached: dict[str, int] = {t: 0 for t in TEAMS}
 
    # Resolve slot strings → team names for the R32
    bracket: list[str] = []   # flat list; pairs are [i*2], [i*2+1]
    for slot_a, slot_b in PLACEHOLDER_R32:
        ta = slots.get(slot_a)
        tb = slots.get(slot_b)
        if ta is None or tb is None:
            # Slot unfilled (can happen if placeholder bracket references
            # non-existent slots). Give a bye to the available team.
            winner = ta or tb
            bracket.append(winner)
            bracket.append(None)
        else:
            bracket.append(ta)
            bracket.append(tb)
    
    rounds = {32: 3, 16: 4, 8: 5, 4: 6, 2: 7}   # n_teams → round_label
    n = 32

    while n > 1:
        label = rounds[n]
        next_bracket = []
        for i in range(0, len(bracket), 2):
            ta = bracket[i]
            tb = bracket[i + 1] if i + 1 < len(bracket) else None
 
            if ta is None and tb is None:
                next_bracket.append(None)
                continue
            if ta is None:
                next_bracket.append(tb)
                if tb:
                    round_reached[tb] = max(round_reached[tb], label)
                continue
            if tb is None:
                next_bracket.append(ta)
                if ta:
                    round_reached[ta] = max(round_reached[ta], label)
                continue
 
            winner = _simulate_match_knockout(ta, tb)
            loser  = tb if winner == ta else ta
            round_reached[winner] = max(round_reached[winner], label + 1)
            round_reached[loser]  = max(round_reached[loser],  label)
            next_bracket.append(winner)
 
        bracket = next_bracket
        n //= 2
 
    # The last team standing
    champion = bracket[0]
    if champion:
        round_reached[champion] = 8   # winner
 
    return round_reached

def simulate_tournament() -> dict[str, int]:
    """
    Simulate one complete tournament.
    Returns round_reached dict: team → highest round int (0 if group exit).
    """
    slots, _ = simulate_group_stage()
 
    # Mark teams that advanced vs those that didn't
    advanced = set(slots.values())
    round_reached = {t: (3 if t in advanced else 0) for t in TEAMS}
 
    ko_results = simulate_knockout(slots)
 
    # Merge: knockout results override for teams that made R32
    for team, rnd in ko_results.items():
        if rnd > 0:
            round_reached[team] = rnd
 
    return round_reached

#  ── Monte Carlo runner ────────────────────────────────────────────────────────
 
ROUND_LABELS = {
    0: "group_exit",
    3: "r32",
    4: "r16",
    5: "quarterfinal",
    6: "semifinal",
    7: "finalist",
    8: "winner",
}

def run(n: int = 10_000, seed: Optional[int] = None) -> dict[str, dict[str, float]]:
    """
    Run N full tournament simulations.
 
    Args:
        n    : number of simulations (10 000 recommended for stable probabilities)
        seed : optional random seed for reproducibility
 
    Returns:
        {
          "Argentina": {
            "group_advance":  0.87,
            "r32":            0.87,
            "r16":            0.71,
            "quarterfinal":   0.52,
            "semifinal":      0.38,
            "finalist":       0.26,
            "winner":         0.17,
            "expected_round": 5.3,   # weighted average round reached
          },
          ...
        }
    """
    if seed is not None:
        random.seed(seed)
 
    # Accumulators: team → {round_int → count}
    counts: dict[str, dict[int, int]] = {
        t: defaultdict(int) for t in TEAMS
    }
 
    for i in range(n):
        if (i + 1) % 1000 == 0:
            print(f"  Simulated {i + 1:,} / {n:,} tournaments…")
 
        results = simulate_tournament()
        for team, rnd in results.items():
            counts[team][rnd] += 1
 
    # Convert to probabilities
    output: dict[str, dict[str, float]] = {}
    for team in TEAMS:
        c = counts[team]
        total = sum(c.values())
 
        # Cumulative: probability of reaching AT LEAST round r
        def prob_at_least(r: int) -> float:
            return sum(v for rnd, v in c.items() if rnd >= r) / total
 
        expected_round = sum(rnd * cnt for rnd, cnt in c.items()) / total
 
        output[team] = {
            "group_advance":  round(prob_at_least(3), 4),
            "r32":            round(prob_at_least(3), 4),
            "r16":            round(prob_at_least(4), 4),
            "quarterfinal":   round(prob_at_least(5), 4),
            "semifinal":      round(prob_at_least(6), 4),
            "finalist":       round(prob_at_least(7), 4),
            "winner":         round(prob_at_least(8), 4),
            "expected_round": round(expected_round, 2),
        }
 
    return output

if __name__ == "__main__":
    import json
 
    N = 5_000   # quick smoke-test; use 10_000+ for real predictions
    print(f"Running {N:,} tournament simulations…\n")
    results = run(n=N, seed=42)
 
    # Sort by win probability
    ranked = sorted(results.items(), key=lambda x: x[1]["winner"], reverse=True)
 
    print(f"\n{'Team':25s} {'Win%':>6}  {'Final%':>7}  {'SF%':>5}  {'QF%':>5}  {'R16%':>6}")
    print("─" * 65)
    for team, probs in ranked[:20]:
        print(
            f"  {team:23s}"
            f"  {probs['winner']*100:5.1f}%"
            f"  {probs['finalist']*100:6.1f}%"
            f"  {probs['semifinal']*100:4.1f}%"
            f"  {probs['quarterfinal']*100:4.1f}%"
            f"  {probs['r16']*100:5.1f}%"
        )
 
    print(f"\nFull results (JSON):\n{json.dumps(results, indent=2)}")
    with open("monte_carlo_results.json", "w") as f:
        json.dump(results, f, indent=2)
        