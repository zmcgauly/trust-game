# Trust Game Experiment

An oTree 6 experiment with fixed proposer and responder roles, rotating partners, randomized multipliers, incentivized probability reports, and an optional picture treatment.

## Experimental design

- Participants are divided evenly between proposers and responders.
- Roles remain fixed throughout the session.
- The session begins with two unpaid practice rounds.
- Each real period consists of two rounds with the same partner.
- Partners rotate after each period.
- A participant is not matched with the same partner in two different real periods.
- The number of real periods is the smaller of 10 and the number of participants in the opposite role.

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

## Picture treatment

Picture exposure is a between-session treatment controlled by `picture_condition`.

The experimenter chooses one of two session configurations:

- `trust_game_randomized`: no pictures;
- `trust_game_randomized_pictures`: pictures.

All participants answer demographic questions about themselves.

Only participants in picture-treatment sessions make demographic guesses about their matched partners.

The relevant partner's picture is displayed while each set of guesses is made.

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

Open the oTree administrator interface and create either the picture or no-picture session configuration.

## Data export

The custom export contains one row for each active proposer-responder round, including:

- session configuration and treatment condition;
- period and round identifiers;
- partner identities;
- realized multiplier;
- sent, multiplied, intended-return, and delivered-return amounts;
- trust-game points and payments;
- belief reports, quadratic winning chances, random draws, and bonuses;
- self-demographic responses;
- partner-demographic guesses in picture-treatment sessions.

Partner-demographic export fields are empty in no-picture sessions.

## Production settings

Set `OTREE_ADMIN_PASSWORD` and `SECRET_KEY` before running in production.

The development defaults in `settings.py` must not be used for a production deployment.
