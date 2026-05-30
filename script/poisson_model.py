import math
import random
from typing import Optional
from itertools import product
from team_rating import TEAMS, get_team, elo_win_probability

# ── Constants ────────────────────────────────────────────────────────────────
HOME_ADVANTAGE   = 1.10   # ~10% boost for neutral-ish host nation advantage
MAX_GOALS        = 10     # max goals per team we consider (Poisson tail is tiny beyond 8)
ELO_SCALE        = 1800    # controls how much ELO gap stretches λ (larger = softer effect)
AVG_GOALS_TOTAL  = 2.55   # world cup historical avg total goals per match (used for scaling)


# ── Core λ computation ───────────────────────────────────────────────────────
def elo_lambda(elo_a: int, elo_b: int) -> float:

    diff = elo_b - elo_a
    return 10 ** (diff / ELO_SCALE)

def compute_lambda(team_a: str, team_b: str, neutral: bool = True) -> tuple[float, float]:
     """
    Compute expected goals (λ) for both teams in a match.
 
    Args:
        team_a   : name of team A (attacking perspective)
        team_b   : name of team B
        neutral  : True for World Cup group stage (mostly neutral venues)
                   False gives team_a a home advantage multiplier
 
    Returns:
        (lambda_a, lambda_b) — expected goals for each team
    """
     a = get_team(team_a)
     b = get_team(team_b)

     factor = elo_lambda(a['elo'], b['elo'])
     lambda_a = a['attack'] * b['defense'] * factor
     lambda_b = b['attack'] * a['defense'] * (1 / factor)

     if not neutral:
            lambda_a *= HOME_ADVANTAGE
     
     return round(lambda_a, 4), round(lambda_b, 4)

# ── Poisson distribution functions ───────────────────────────────────────
def poisson_dis(lam: float, k: int) -> float:
    """P(X = k) where X ~ Poisson(λ)"""
    if lam <= 0:
        return 0.0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)

def scoreline_matrix(lambda_a: float, lambda_b: float) -> dict[tuple, float]:
     """
    Build a probability matrix for every scoreline (goals_a, goals_b).
    Keys are (goals_a, goals_b), values are probabilities.
    Probabilities sum to ~1.0 (small Poisson tail beyond MAX_GOALS is ignored).
    """
     matrix = {}
     for goals_a, goals_b in product(range(MAX_GOALS + 1), repeat=2):
         p_a = poisson_dis(lambda_a, goals_a)
         p_b = poisson_dis(lambda_b, goals_b)
         matrix[(goals_a, goals_b)] = round(p_a * p_b, 6)
     
     return matrix
# ── Match outcome probabilities ───────────────────────────────────────────────

def match_probabilities(team_a: str, team_b: str, neutral: bool = True) -> dict:
    """
    Compute probabilities of win/draw/loss for team_a against team_b.
    Returns a dict with keys 'win', 'draw', 'loss' and their probabilities.
    """
    lam_a, lam_b = compute_lambda(team_a, team_b, neutral)
    matrix = scoreline_matrix(lam_a, lam_b)
 
    prob_a_win = sum(p for (ga, gb), p in matrix.items() if ga > gb)
    prob_draw  = sum(p for (ga, gb), p in matrix.items() if ga == gb)
    prob_b_win = sum(p for (ga, gb), p in matrix.items() if ga < gb)

    # Top 5 most likely scorelines
    top = sorted(matrix.items(), key=lambda x: x[1], reverse=True)[:5]
    top_scorelines = [(f"{ga}-{gb}", round(p * 100, 2)) for (ga, gb), p in top]

    return {
        "team_a": team_a,
        "team_b": team_b,
        "lambda_a": lam_a,
        "lambda_b": lam_b,
        "prob_a_win": round(prob_a_win, 4),
        "prob_draw":  round(prob_draw,  4),
        "prob_b_win": round(prob_b_win, 4),
        "top_scorelines": top_scorelines,
        "expected_total_goals": round(lam_a + lam_b, 2),
    }

def simulate_score(lambda_a: float, lambda_b: float) -> tuple[int, int]:
    """
    Sample a single scoreline from Poisson distributions.
    Used by monte_carlo.py for each simulation run.
 
    Returns (goals_a, goals_b)
    """
    def poisson_sample(lam: float) -> int:
        """Knuth algorithm for sampling from Poisson(λ)"""
        L = math.exp(-lam)
        k, p = 0, 1.0
        while p > L:
            k += 1
            p *= random.random()
        print(k)
        return k - 1

    return poisson_sample(lambda_a), poisson_sample(lambda_b)

def penalty_winner(team_a: str, team_b: str) -> str:
    """
    In knockout rounds, draws go to penalties.
    Winner decided by ELO-weighted coin flip (stronger team wins ~55% of shootouts).
    """
    a = get_team(team_a)
    b = get_team(team_b)
    p_a = elo_win_probability(a["elo"], b["elo"])
    # Flatten toward 50/50 — penalties are mostly luck
    p_a_adjusted = 0.5 + (p_a - 0.5) * 0.2
    return team_a if random.random() < p_a_adjusted else team_b

if __name__ == "__main__":
    test_matches = [
        ("Spain",       "Morocco"),
        ("Argentina",   "France"),
        ("Brazil",      "England"),
        ("Germany",     "Japan"),
        ("USA",         "Iran"),
    ]
    for team_a, team_b in test_matches:
        r = match_probabilities(team_a, team_b)
        print(f"\n{'─'*52}")
        print(f"  {team_a:20s} vs  {team_b}")
        print(f"  λ: {r['lambda_a']} vs {r['lambda_b']}   "
              f"(expected {r['expected_total_goals']} total goals)")
        print(f"  Win:  {r['prob_a_win']*100:.1f}%  "
              f"Draw: {r['prob_draw']*100:.1f}%  "
              f"Loss: {r['prob_b_win']*100:.1f}%")
        print(f"  Top scorelines: {r['top_scorelines'][:3]}")

    # Simulate 5 random scorelines for Argentina vs France
    print(f"\n{'─'*52}")
    print("  5 sampled scorelines — Argentina vs France:")
    la, lb = compute_lambda("Argentina", "France")
    for _ in range(5):
        ga, gb = simulate_score(la, lb)
        print(f"    Argentina {ga} - {gb} France")