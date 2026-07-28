# Implementation Notes

## Payment calibration

The default payment formula is:

```text
$10 show-up payment
+ $0.30 × total trust-game points from both rounds of one selected period
+ a possible $2 belief prize in each of the selected period's two rounds
```

Using the planning benchmark of 23.75 trust-game points per round:

```text
Expected trust payment = 2 × 23.75 × $0.30 = $14.25
Illustrative expected belief payment across all participants at a 50% report ≈ 0.5 × 2 rounds × 0.75 × $2 = $1.50
Illustrative expected total = $10 + $14.25 + $1.50 = $25.75
```

Only proposers complete the belief reports, so realized average payments can differ by role.

## Period-count interpretation

Roles remain fixed. If there are `N/2` proposers and `N/2` responders, each participant has `N/2` possible opposite-role partners. The app therefore uses:

```text
active_periods = min(10, N/2)
```

This is the maximum number of periods that guarantees no proposer-responder pair repeats. Across those periods, every possible cross-role pair is used once when `N/2 <= 10`.

## Randomization

One period is selected once per session and hidden until the payment summary. Both rounds' trust-game outcomes and both proposer belief reports from that period determine payment.

For each post-return belief report in the selected period, the app calculates the quadratic winning chance \(W\) from the reported low-multiplier probability \(X\) and the realized multiplier. It then draws \(Y\), with every integer from 0 through 100 equally likely, and awards the bonus when \(Y\leq W\). Each report, winning chance, draw, and outcome is stored for auditing.

Every group's multiplier is independently drawn in every round using the session-level `high_multiplier_probability`.

## Validation performed here

- Python syntax compilation for the project files
- lightweight import smoke test with a stubbed oTree API
- quadratic winning-chance and bonus-draw checks
- simulated 10-participant pairing schedule confirming five unique opposite-role partners
- simulated independent multiplier support and selected-period payoff flags

A full `otree test` run should still be performed in the RA's oTree environment before piloting.
