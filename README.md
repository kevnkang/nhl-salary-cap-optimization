# NHL Salary Cap Optimization Project

## Project Overview

In this project I build the best possible 20-player NHL roster that fits under the salary cap. Each player gets a **Custom Performance Score (CPS)** based on their stats, and a linear program built with **PuLP** picks the roster with the highest total CPS while staying under the cap and filling every position.

### Data Vintage
- **Performance stats:** 2023–24 regular season
- **Contracts:** 2024–25 cap hits, scraped from Spotrac on 2024-09-19
- **Salary cap:** $83.5M (2024–25 upper limit)

---

## Steps and Process

### 1. Data Collection
I collected salary and performance data from these sources:
- **Spotrac**: cap hit and contract details, scraped by `get_data.py`.
- **Natural Stat Trick**: 2023–24 skater and goalie stats, exported as CSV files.
- **nhl.com/stats**: 2023–24 skater plus/minus and goalie wins, exported as CSV files.

### 2. Cleaning and Name Matching
Player names and team codes differ between sources (e.g. `Mitch Marner` vs. `Mitchell Marner`, `TBL` vs. `T.B`). All name corrections live in one place, `src/name_map.py`, which both `clean_data.py` and `merge_data.py` import.

Names alone are not unique. For example, there are two Sebastian Ahos: a Carolina forward and an Islanders defenseman. I therefore match in two passes, both when adding plus/minus to the stats (`clean_data.py`) and when adding contracts to CPS (`merge_data.py`):

1. **Name + team:** match rows that have the same name and at least one team in common (team codes are converted to one format first).
2. **Unique name:** for rows still unmatched, usually players who changed teams between seasons, match on name only, and only when that name appears once on each side.

Both passes compare a **normalized name key**, not the raw name. The key strips accents (`Hakanpää` → `hakanpaa`), lowercases the name, and maps common first-name variants (Charles→Charlie, Zachary→Zach, Alexander→Alex, Joshua→Josh, Matthew→Matt, Nicholas→Nick, Mitchell→Mitch, Jacob→Jake, Christopher→Chris, Michael→Mike). It is only used for matching; the stats spelling is kept as the display name.

Both scripts print how many players matched in each pass and how many were left unmatched. For anything still unmatched, they print fuzzy-match candidates with scores (using rapidfuzz). These are **never applied automatically**: I review them and add the correct ones to `name_corrections` in `name_map.py` by hand.

With these steps, **713 of 730 contracts are matched** (565 on name + team, 148 on unique name). The **17 contracts left unmatched belong to players with no 2023–24 NHL stats**, such as Carey Price, Shea Weber, Gabriel Landeskog, and 2024–25 rookies like Macklin Celebrini and Matvei Michkov.

### 3. Custom Performance Score (CPS)
`integrate_data.py` min-max scales every metric to 0–1 across all skaters (or all goalies) and then combines them with position-specific weights. **The weights for every position sum to 1.** Players listed at two positions are scored at the second one.

| Metric | C | L / R | D |
|---|---|---|---|
| Goals | 0.25 | 0.30 | – |
| Time on ice (TOI) | 0.20 | 0.25 | 0.25 |
| Total assists | 0.15 | 0.20 | – |
| Individual expected goals (ixG) | 0.10 | 0.10 | – |
| Individual Corsi for (iCF) | – | 0.10 | 0.10 |
| Plus/minus | 0.10 | 0.05 | 0.20 |
| Takeaways | 0.10 | – | 0.10 |
| Faceoff % | 0.10 | – | – |
| Shots blocked | – | – | 0.20 |
| Hits | – | – | 0.15 |

| Goalie metric | Weight |
|---|---|
| Save % (SV%) | 0.30 |
| Goals against average (GAA, inverted) | 0.20 |
| Goals saved above average (GSAA) | 0.15 |
| High-danger save % (HDSV%) | 0.15 |
| Expected goals against (inverted) | 0.10 |
| Rebound attempts against (inverted) | 0.05 |
| Scaled win % | 0.05 |

For goalies, "inverted" means `1 − scaled value`, because lower is better. Scaled win % multiplies a goalie's win percentage by `GP / 10` when they played fewer than 10 games, using raw games played. This keeps a 1–0 goalie from getting a 100% win rate.

### 4. Optimization
`analyze_data.py` builds a binary integer program with PuLP:

- **Objective:** maximize total CPS.
- **Salary cap:** total cap hit ≤ $83.5M.
- **Roster:** exactly 12 forwards (C/L/R), 6 defensemen, and 2 goalies.
- **Minimum games played:** before optimizing, I remove goalies with fewer than **15 GP** and skaters with fewer than **20 GP** (`min_goalie_games_played` and `min_skater_games_played` at the top of the file). Without these filters, a goalie with two great games looks like an elite bargain. Players with a missing cap hit or CPS are also dropped instead of being treated as free.

The script prints the solver status and stops if no optimal solution is found.

---

## Results

Solver status: **Optimal**. Cap used: **$83,475,000** of $83.5M (99.97%). Total CPS: **12.11**.

| Pos | Player | CPS | Cap Hit |
|---|---|---|---|
| C | Leon Draisaitl | 0.678 | $8,500,000 |
| C | Vincent Trocheck | 0.576 | $5,625,000 |
| C | Ryan O'Reilly | 0.542 | $4,500,000 |
| C | Wyatt Johnston | 0.507 | $894,167 |
| L | Filip Forsberg | 0.683 | $8,500,000 |
| L | Zach Hyman | 0.673 | $5,500,000 |
| L | Chris Kreider | 0.593 | $6,500,000 |
| L | Alexis Lafrenière | 0.475 | $2,325,000 |
| L | Juraj Slafkovsky | 0.420 | $950,000 |
| R | Nikita Kucherov | 0.777 | $9,500,000 |
| R | Mikko Rantanen | 0.690 | $9,250,000 |
| R | JJ Peterka | 0.454 | $855,833 |
| D | Noah Dobson | 0.634 | $4,000,000 |
| D | Evan Bouchard | 0.633 | $3,900,000 |
| D | Brayden McNabb | 0.623 | $2,850,000 |
| D | Alexander Romanov | 0.614 | $2,500,000 |
| D | Jeremy Lauzon | 0.561 | $2,000,000 |
| D | Brock Faber | 0.548 | $925,000 |
| G | Frederik Andersen | 0.749 | $3,400,000 |
| G | David Rittich | 0.683 | $1,000,000 |

**Effect of the matching improvements:** name normalization added 23 contracts (e.g. Charlie McAvoy, Zach Werenski, Alex DeBrincat, Josh Morrissey), but none of them made the roster, which stayed the same. The 22 hand-approved corrections added afterward brought in JJ Peterka, a productive player on an entry-level contract ($855,833). The cap space he freed changed three spots: Chris Kreider, JJ Peterka, and Jeremy Lauzon replaced Frank Vatrano, Fabian Zetterlund, and Marcus Pettersson. Total CPS rose from 12.07 to 12.11.

The full roster is in `result/optimized_team.csv`. The charts in `result/` are made by `src/data_visualization.ipynb`.

---

## Limitations

- **Unmatched contracts:** 17 of the 730 scraped contracts have no 2023–24 NHL stats (injured, retired, or rookies), so those players can't be selected. A newly scraped contract file may bring new spellings; check the fuzzy candidates that `merge_data.py` prints.
- **Subjective weights:** the CPS weights are my own judgment, not fitted to an outcome like wins or goal differential. Different weights produce a different roster.
- **A single season:** CPS uses only 2023–24 stats. It ignores longer-term trends, aging, injuries, and one-season luck, and it assumes 2023–24 performance carries over to 2024–25 contracts.
- **Scores aren't directly comparable across positions:** each position uses its own formula, so a 0.6 center and a 0.6 defenseman aren't equally valuable. The fixed 12/6/2 roster limits keep positions from competing directly, but how the optimizer trades cap space *between* positions still depends on these scores.

---

## Files and Resources

- **`src/get_data.py`**: scrapes Spotrac contract data into `data/raw/all_player_contract_data_<date>.csv`.
- **`src/clean_data.py`**: adds plus/minus to skater stats and win % to goalie stats (`data/cleaned/`).
- **`src/integrate_data.py`**: calculates CPS (`data/processed/cps/`).
- **`src/merge_data.py`**: merges CPS with contracts (`data/processed/merged_player_goalie_cps_and_salaries.csv`).
- **`src/analyze_data.py`**: runs the optimization (`result/optimized_team.csv`).
- **`src/data_visualization.ipynb`**: charts of cap hit, CPS vs. cap hit, and cap allocation (`result/`).
- **`src/name_map.py`**: shared player name corrections, name normalization, and fuzzy-match suggestions.

---

## Tools and Libraries

- **Python**, **pandas**: data processing.
- **scikit-learn** (`MinMaxScaler`): normalizing metrics for CPS.
- **PuLP**: integer linear programming (pinned to `pulp<4`, because PuLP 4 removed `LpStatus`).
- **Requests / BeautifulSoup**: scraping Spotrac.
- **rapidfuzz**: fuzzy-match suggestions for unmatched names.
- **Matplotlib / seaborn / Plotly**: visualizations.

---

## How to Run the Project

```bash
pip install -r requirements.txt
cd src
python get_data.py          # optional: re-scrape contracts (slow, ~1 request per second)
python clean_data.py
python integrate_data.py
python merge_data.py        # uses the newest contract file, or pass a path as an argument
python analyze_data.py
jupyter nbconvert --to notebook --execute --inplace data_visualization.ipynb
```

---

## Future Improvements

- **Advanced Metrics**: add stats such as zone entries, puck possession, and more defensive metrics.
- **Multiple Seasons**: weight CPS over several seasons to reduce single-season noise.
- **Dynamic Cap Changes**: support future salary caps and trade scenarios.
- **User Interaction**: build an interface for entering different roster constraints and seeing results right away.
