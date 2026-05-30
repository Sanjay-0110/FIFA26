# FIFA26

## Project Overview

This repository contains a simulation project for the FIFA 2026 World Cup, built around ELO-based team ratings, Poisson score modeling, and full tournament Monte Carlo simulation.

The project is designed to:
- model expected match outcomes using ELO ratings and team attack/defense profiles
- simulate group-stage matches and tournament progression
- estimate probabilities for advancing to each knockout round and winning the tournament
- produce reproducible predictions via Monte Carlo sampling

## Contents

- `script/team_rating.py`
  - Defines `TEAMS`, including ELO, attack, defense, confederation, and group assignment for FIFA 2026 teams.
  - Provides helper functions: `get_team()`, `get_group()`, `elo_win_probability()`, `elo_update()`, and a basic `points_changes()` formula.
  - Includes a small interactive sanity-check block when run as `__main__`.

- `script/poisson_model.py`
  - Computes expected goals (`λ`) for two teams using ELO and attack/defense coefficients.
  - Builds Poisson scoreline probability matrices.
  - Estimates match outcome probabilities for win, draw, or loss.
  - Samples scorelines and resolves knockout penalties.
  - Includes a smoke-test block for example matches when executed directly.

- `script/monto_carlo.py`
  - Runs full tournament Monte Carlo simulations.
  - Simulates 12 group-stage tables using FIFA 2026-style advancement logic.
  - Selects the 8 best third-place teams with simplified qualification logic.
  - Simulates knockout rounds from Round of 32 through the final.
  - Aggregates the probability of teams reaching each round and of winning.
  - Saves results to `monte_carlo_results.json` when executed directly.

- `monte_carlo_results.json`
  - Output file produced by the simulation runner.

- `DataCamp Challenge/`
  - A separate folder present in the repository, not required for the core FIFA26 simulation.

## How It Works

### Team Ratings

Teams are assigned static ELO ratings and per-team attack/defense multipliers in `script/team_rating.py`. These ratings are used as the foundation for expected-goal modeling.

### Match Modeling

`script/poisson_model.py` uses team strengths to compute expected goals for both sides. The model applies a Poisson distribution to generate scoreline probabilities and derive match outcome likelihoods.

### Tournament Simulation

`script/monto_carlo.py` performs the full tournament flow:
1. Simulate all group-stage matches.
2. Rank each group by points, goal difference, and goals for.
3. Choose the top two teams from each group plus 8 best third-place teams.
4. Simulate knockout matches, with draws settled by penalties.
5. Repeat across many tournament simulations to compute probabilities.

## Running the Simulation

From the `FIFA26` folder, run:

```bash
python script/monto_carlo.py
```

This executes a quick smoke-test of the Monte Carlo runner and writes results to `monte_carlo_results.json`.

### Recommended Configuration

- Increase `N` in `script/monto_carlo.py` from `5_000` to `10_000` or more for more stable probabilities.
- Optionally set a deterministic seed to reproduce results.

## Notes and Limitations

- ELO ratings are static and do not update during a tournament.
- Group third-place qualification is simplified; the confederation criterion is not fully implemented.
- Knockout bracket placement uses placeholder pairings rather than an official draw table.
- The model is intended as a forecasting prototype rather than a fully polished competition engine.

## Future Improvements

Potential enhancements include:
- updating ELO ratings after each simulated match
- implementing official FIFA draw/bracket rules for 2026
- adding more realistic match venue/home-advantage logic
- supporting user-defined team ratings and scenario analysis
- improving head-to-head tiebreakers across tied teams

## Contact

This project is maintained in the `FIFA26` directory of the workspace and is intended for exploratory World Cup prediction and simulation analysis.
