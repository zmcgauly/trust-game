# Trust Game Experiment

This repository contains an oTree-compatible implementation of the Trust Game 1.5 design:
the Trust Game 2.0 design before the written-description treatment change, with the
Trust Game 2.0 sliding-scale belief elicitation.
The original standalone browser prototype remains in `index.html`, but the oTree project
entry point is `settings.py` and the app is `trust_game`.

## Design

- Default session: 10 players.
- Roles are fixed: first half are proposers, second half are responders.
- With 10 players, the scheduler creates 5 periods.
- Each period has 5 proposer-responder pairs.
- Every proposer meets every responder exactly once.
- Each period has 2 rounds with the same partner.
- Proposers start each round with 20 points and can send whole points.
- Sent points are multiplied for the responder.
- Responders choose how many whole points to send back.
- After each round result, proposers report the probability from 0% to 100% that the low multiplier was used.
- The default show-up fee is `$10.00`.
- Each real-round proposer belief report is evaluated for a `$2.00` belief prize using the quadratic winning-chance rule.
- The session is created as one of four treatment cells: certain/no picture,
  certain/picture, uncertain/no picture, or uncertain/picture.
- The two rounds in the same period use the same multiplier condition.
- Players are told their fixed role at the start of each period, without being told the multiplier condition.
- Players are never asked to upload pictures.
- In picture sessions, both players' pictures are shown. In no-picture sessions, neither player's picture is shown.
- In uncertain-multiplier sessions, the session draws either the 3x or large multiplier once per period.
- By default, the 3x multiplier occurs with probability `0.50` and the large multiplier is `6`.
- In certain-multiplier sessions, the multiplier is always 3x.

## Session Options and Period Treatments

| Session option | Multiplier condition | Box label |
| --- | --- | --- |
| Certain multiplier / No pictures | Fixed 3x | No picture / Multiplier 3 |
| Certain multiplier / Pictures | Fixed 3x | Picture / Multiplier 3 |
| Uncertain multiplier / No pictures | Hidden 3x/large draw | No picture / Multiplier 3 or large |
| Uncertain multiplier / Pictures | Hidden 3x/large draw | Picture / Multiplier 3 or large |

The oTree demo page shows four session configs:

- `trust_game_certain_no_picture`
- `trust_game_certain_picture`
- `trust_game_uncertain_no_picture`
- `trust_game_uncertain_picture`

The picture condition and multiplier certainty condition are selected when the session
is created. In uncertain-multiplier sessions, the realized multiplier is drawn
separately for each period, not each round. The two rounds in a period always use the
same realized multiplier.

## Running with oTree

Use the same Python environment where oTree is installed. This project targets oTree 6.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\otree.exe devserver
```

Then open the local oTree URL printed by the server and create one of the four
trust-game session configs.

Available oTree session configs:

- `trust_game_certain_no_picture`
- `trust_game_certain_picture`
- `trust_game_uncertain_no_picture`
- `trust_game_uncertain_picture`

The random multiplier parameter is set in `settings.py`:

```python
chance_of_3=0.50
large_multiplier=6
belief_prize_dollars=2.00
```

The create-session form exposes `Chance of 3` as 25%, 50%, or 75%, and `Large
multiplier` as a whole-number input.

## Heroku Deployment from GitHub

This project includes Heroku deployment files:

- `Procfile` runs `otree prodserver`.
- `.python-version` pins the Heroku Python runtime.
- `requirements.txt` pins oTree and includes the PostgreSQL driver.
- `.slugignore` keeps local development artifacts out of the Heroku slug.

To deploy from GitHub:

1. Push this project to a GitHub repository.
2. In Heroku, create a new app and connect it to that GitHub repository.
3. Add a Heroku Postgres database to the app. This creates the `DATABASE_URL` config var that oTree uses in production.
4. Set these Heroku config vars:

```text
OTREE_PRODUCTION=1
OTREE_AUTH_LEVEL=STUDY
OTREE_ADMIN_PASSWORD=<strong admin password>
OTREE_SECRET_KEY=<long random secret>
```

5. Deploy the GitHub branch from Heroku.
6. On first deployment, or after changing model fields, run:

```powershell
heroku run otree resetdb --app <your-heroku-app-name>
```

Do not run `otree resetdb` after collecting real data unless you intentionally want to
erase that app's database.

## Player Pictures

Preloaded player images live in `_static/trust_game/players/`. Use the player title as
the filename:

- `Player 1.jpg`
- `Player 2.jpg`
- `Player 3.jpg`
- `Player 4.jpg`
- `Player 5.jpg`
- `Player 6.jpg`
- `Player 7.jpg`
- `Player 8.jpg`
- `Player 9.jpg`
- `Player 10.jpg`

When a picture session is created, oTree displays the matching images automatically.
When a no-picture session is created, neither the participant's own image nor the
partner's image is displayed in any period.

## Standalone Prototype

You can still open `index.html` directly in a browser to view the earlier local prototype.
Use the oTree app for actual oTree sessions.

## Data Export

Use oTree's admin data export. The app defines a custom export with one row per
proposer-responder round. The export includes:

- treatment box
- random-multiplier probability
- period, round, and pair number
- proposer and responder IDs/names
- offer
- multiplied points
- responder's intended return
- whether the 6x multiplier applied
- points delivered back to the proposer
- proposer's slider belief report about the low multiplier
- belief winning chance, random draw, and awarded belief bonus
- final proposer and responder points
