# Trust Game Experiment

An oTree 6 experiment with fixed proposer and responder roles, rotating partners, randomized multipliers, incentivized probability reports, and a 2-by-2 partner-cue treatment design.

## Experimental design

- Participants are divided evenly between proposers and responders.
- Roles remain fixed throughout the session.
- Part 1 collects participants' self-demographic information.
- Part 2 is the trust-game decision task.
- The session begins with two unpaid practice rounds.
- Each real period consists of two rounds with the same partner.
- Partners rotate after each period.
- A participant is not matched with the same partner in two different real periods.
- The number of real periods is the smaller of 10 and the number of participants in the opposite role.
- Part 3 asks participants to guess the demographics of the partners with whom they were matched.

In each round, the proposer receives 20 points and sends an integer from 0 through 20 to the responder.

The amount sent is multiplied by either the low or high multiplier.

The multiplier is drawn separately for each group in each round.

The proposer does not observe the realized multiplier.

The responder observes the amount sent, the realized multiplier, and the resulting amount available before choosing a return.

## Round payoffs

Let \(S\) be the amount sent, \(M\) the realized multiplier, and \(R\) the amount returned.

The proposer's round payoff is:

\[
\mathit{payoff}_P = 20-S+R.
\]

The responder's round payoff is:

\[
\mathit{payoff}_R = SM-R.
\]

## Payment

One real period is selected at random for payment.

Both trust-game rounds in that period are paid.

Each trust-game point is converted to dollars using `trust_point_dollar_value`.

The participation fee is added to decision-based earnings.

In every round, the proposer reports \(X\), the probability from 0% through 100% that the low multiplier was used.

Both belief reports from the selected period are evaluated for separate belief prizes.

For each evaluated report, the quadratic winning chance is:

\[
W=100-\frac{(100-X)^2}{100}
\]

when the multiplier was low, and:

\[
W=100-\frac{X^2}{100}
\]

when the multiplier was high.

The computer draws \(Y\), with every integer from 0 through 100 equally likely.

The belief prize is awarded when \(Y\leq W\).

## Partner-cue treatment design

The experiment uses a 2-by-2 between-session treatment design over partner cues.

| Treatment cell | Pictures | Written partner description |
|---|---|---|
| No picture / no description | No | No |
| No picture / description | No | Yes |
| Picture / no description | Yes | No |
| Picture / description | Yes | Yes |

The experimenter chooses one of four session configurations:

- `trust_game_no_picture_no_description`;
- `trust_game_no_picture_description`;
- `trust_game_picture_no_description`;
- `trust_game_picture_description`.

Picture exposure is controlled by `picture_condition`.

Written descriptions are controlled by `written_description_condition`.

All participants answer demographic questions about themselves in Part 1, before the trust-game decisions begin.

All participants make demographic guesses about their matched partners in Part 3, after the trust-game decisions are complete.

The relevant partner's available cues are displayed while each set of guesses is made.

Written descriptions are generated from the partner's Part 1 self-demographic survey responses. If `C.PROFILE_DESCRIPTIONS` in `trust_game/__init__.py`, or optional session config metadata, defines a description keyed by player title or player number, that predefined text overrides the generated survey-based description.

The app waits for all participants to complete Part 1 before Part 2 begins, so written partner descriptions are available during the decision task.

## Default configuration

| Parameter | Default |
|---|---:|
| Low multiplier | `3.0` |
| High multiplier | `6.0` |
| High-multiplier probability | `0.50` |
| Trust-point value | `$0.30` |
| Belief prize per evaluated report | `$2.00` |
| Participation fee | `$10.00` |

Session parameters are defined in `settings.py`.

The app requires an even number of participants and at least two participants.

## Installation and local use

Create and activate a Python virtual environment, then install the dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Start the oTree development server:

```powershell
.\.venv\Scripts\otree.exe devserver
```

Open the oTree administrator interface and create one of the four partner-cue session configurations.

## Data export

The custom export contains one row for each active proposer-responder round, including:

- session configuration and treatment condition;
- picture and written-description condition;
- period and round identifiers;
- partner identities;
- realized multiplier;
- sent, multiplied, intended-return, and delivered-return amounts;
- trust-game points and payments;
- belief reports, quadratic winning chances, random draws, and bonuses;
- Part 1 self-demographic responses;
- Part 3 partner-demographic guesses.

Partner-demographic export fields are populated for all treatment cells.

## Production settings

Set `OTREE_ADMIN_PASSWORD` and `SECRET_KEY` before running in production.

The development defaults in `settings.py` must not be used for a production deployment.
