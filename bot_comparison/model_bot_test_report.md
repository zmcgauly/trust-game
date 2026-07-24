# Bot Test Report: Old and New Trust Game Multiplier Models

## Purpose

The bot testing system was built to evaluate how changes to the multiplier randomization model affect game outcomes while holding participant decisions constant. This allowed the payoff effects of the model change to be examined without introducing behavioral differences from different player choices.

The bot comparison focused on three questions:

1. Whether the game could be completed automatically from start to finish without page or validation errors.
2. Whether the same simulated decisions could be applied consistently across model variants.
3. How total and average payoffs changed when the multiplier model changed.

## How the Bot Played the Game

The bot used a fixed strategy on every run:

- Each proposer sent 10 points.
- Each responder returned one-half of the points available after multiplication.
- Proposers submitted the same multiplier belief entries.
- Instruction quiz answers were submitted correctly.
- Self-demographic questions used "Prefer not to say" where applicable.
- Partner demographic guesses used the same fixed answers and confidence ratings for every partner.

This fixed strategy was important because it isolated the model change. If payoffs changed, the difference came from the multiplier assignment, not from different bot choices.

## Test Design

The comparison script is `scripts/compare_randomization_models.py`.

The script did the following:

1. Created a timestamped output folder under `bot_comparison/`.
2. Copied the current project files into an isolated `_run_project` folder for each run.
3. Set a deterministic random seed using the `TRUST_GAME_BOT_RANDOM_SEED` environment variable.
4. Ran oTree's bot test command with export enabled.
5. Located the exported `trust_game_custom.csv` file.
6. Copied the full exported data into the comparison folder.
7. Computed summary statistics.
8. Wrote CSV files and an Excel workbook for review.

The main command used by the script was equivalent to:

```text
otree test trust_game_randomized 10 --export <output folder>
```

The default participant count was 10. With 10 players, the game creates 5 proposer-responder pairs per round.

## Data Files Produced

The comparison system produced:

- `summary.csv`: high-level totals and averages.
- `round_comparison.csv` or `round_data.csv`: round-by-round payoff data.
- `current_period_level_full_data.csv`: full custom export from the current model.
- `group_level_full_data.csv`: full custom export from the group-level comparison model, when that comparison was still present.
- `trust_game_bot_comparison.xlsx`: Excel workbook containing the same data in spreadsheet form.

The most relevant saved outputs are:

- `bot_comparison/comparison_20260715_131300/trust_game_bot_comparison.xlsx`
- `bot_comparison/comparison_20260715_132536/trust_game_bot_comparison.xlsx`
- `bot_comparison/comparison_20260715_134251/trust_game_bot_comparison.xlsx`

## Earlier Comparison: Current Period-Level Model vs Group-Level Model

The earlier comparison tested two model variants:

- `current_period_level`: the then-current model.
- `group_level`: the contrasting model where randomization was organized at the group level.

Both variants were run with:

- 10 participants.
- 60 exported rows total.
- 10 practice rows.
- 50 real-game rows.
- The same bot decisions.

The saved summary from `comparison_20260715_131300` and `comparison_20260715_132536` showed the same results:

| Metric | Current period-level | Group-level | Difference: group minus current |
|---|---:|---:|---:|
| Real game rows | 50 | 50 | 0 |
| Practice rows | 10 | 10 | 0 |
| Total proposer payoff, real rounds | 1385 | 1400 | +15 |
| Total responder payoff, real rounds | 885 | 900 | +15 |
| Average proposer payoff, real rounds | 27.7 | 28.0 | +0.3 |
| Average responder payoff, real rounds | 17.7 | 18.0 | +0.3 |
| Total points sent, real rounds | 500 | 500 | 0 |
| Total points available, real rounds | 1770 | 1800 | +30 |
| Total points returned, real rounds | 885 | 900 | +15 |
| Average realized multiplier | 3.54 | 3.60 | +0.06 |
| High multiplier rows | 9 | 10 | +1 |
| Low multiplier rows | 41 | 40 | -1 |
| Picture-condition rows | 20 | 20 | 0 |

Because the bots made the same choices, the group-level version paid slightly more in this run because it produced one additional high-multiplier real-game row. That extra high-multiplier row increased total points available by 30 points. Since responders returned half of the available points, total returned points increased by 15, proposer payoffs increased by 15, and responder payoffs increased by 15.

The total combined payoff difference was therefore 30 points in favor of the group-level model for this seeded test run.

## Latest Current Model: All Real Rounds Have 50 Percent Chance of Multiplier 3 or 6

After later changes, the active model was simplified so the saved current run no longer compared two treatment schedules. Instead, all real pair-rounds used the random multiplier condition, with a 50 percent chance of multiplier 3 and a 50 percent chance of multiplier 6.

The latest saved run is `comparison_20260715_134251`.

Its summary was:

| Metric | Latest current model |
|---|---:|
| All exported rows | 60 |
| Real game rows | 50 |
| Practice rows | 10 |
| Total proposer payoff, real rounds | 1565 |
| Total responder payoff, real rounds | 1065 |
| Average proposer payoff, real rounds | 31.3 |
| Average responder payoff, real rounds | 21.3 |
| Total points sent, real rounds | 500 |
| Total points available, real rounds | 2130 |
| Total points returned, real rounds | 1065 |
| Average realized multiplier | 4.26 |
| High multiplier rows | 21 |
| Low multiplier rows | 29 |
| Random multiplier condition rows | 50 |
| Fixed multiplier condition rows | 0 |
| Picture-condition rows | 20 |

This confirms that, in the latest run, every real-game row was treated as a random multiplier row. There were no fixed-multiplier real-game rows.

## Payoff Logic Behind the Results

The bot always sent 10 points. Therefore:

- If the multiplier was 3, the responder had 30 points available.
- If the multiplier was 6, the responder had 60 points available.
- The responder returned half of the available points.

That means:

| Multiplier | Points available to responder | Points returned | Proposer payoff | Responder payoff |
|---:|---:|---:|---:|---:|
| 3 | 30 | 15 | 25 | 15 |
| 6 | 60 | 30 | 40 | 30 |

The latest current model had 21 high-multiplier rows and 29 low-multiplier rows across the 50 real-game rows. This explains the totals:

- Proposer payoff: `(29 * 25) + (21 * 40) = 1565`
- Responder payoff: `(29 * 15) + (21 * 30) = 1065`
- Points available: `(29 * 30) + (21 * 60) = 2130`
- Points returned: half of available points, or `1065`

## Interpretation

The bot tests show that the new all-random multiplier model increases expected payouts relative to the earlier mixed fixed/random model because every real pair-round is now eligible for the multiplier 6 draw.

In the earlier comparison, only some real-game rows were in the random multiplier condition. In the latest current model, all 50 real-game rows were in the random multiplier condition. As a result, the latest run had:

- More high-multiplier rows: 21 high rows in the latest current model versus 9 high rows in the earlier period-level comparison.
- Higher average realized multiplier: 4.26 versus 3.54.
- Higher total proposer payoff: 1565 versus 1385.
- Higher total responder payoff: 1065 versus 885.

Compared with the earlier period-level test, the latest current model increased total real-round payments by:

- Proposers: +180 points.
- Responders: +180 points.
- Combined: +360 points.

If 1 point equals 1 dollar and all real rounds are eligible for payoff selection, this seeded bot run implies a substantially higher potential payout exposure under the all-random model. If only one real round is randomly selected for payment, the expected cost impact should be evaluated on the selected-round rule rather than the full-session total.

## Limitations

The tests are deterministic bot simulations, not human behavior. They verify game flow and mechanical payoff consequences under fixed decisions. They do not estimate how real participants will change their decisions under the new model.

The old group-level comparison was saved from an earlier version of the script. The current script now runs only the active `trust_game_randomized` configuration, because the separate group-level model was removed from the demo/session configuration.

The multiplier draws are random but seeded for reproducibility. A different seed can produce a different number of high-multiplier rows, although with enough runs the average should move toward the configured 50 percent chance.

## Bottom Line

The bot system successfully evaluated both the earlier model comparison and the latest current model. It held player decisions constant, exported full row-level data, generated spreadsheet summaries, and made the payoff effect of the multiplier changes visible.

The most important finding is that the latest all-random model produced higher total payoffs in the saved bot run because more rounds received the multiplier 6 outcome. The effect was mechanical: with the bot sending 10 points and responders returning half, every multiplier 6 row paid 15 more points to the proposer and 15 more points to the responder than a multiplier 3 row.
