# Trust Game Experiment

This repository contains an oTree-compatible implementation of a 2x2 trust-game design.
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
- Sent points are tripled for the responder.
- Responders choose how many whole points to send back.
- After each round result, proposers answer how many points they think the responder sent back.
- At the start of each period, the app independently randomizes one of the four treatment cells with equal 1-in-4 probability.
- The two rounds in the same period use the same treatment cell.
- Players are told their fixed role and whether pictures are visible at the start of each period.
- Players are never asked to upload pictures.
- If pictures are visible in a period, self-identification and partner-identification pages appear after the second round of that period.
- In error periods, each pair-round has a hidden error draw.
- By default, the error occurs with probability `0.50`.
- By default, when the error occurs, the points delivered back to the proposer are multiplied by `0.50`.
- Participants are not told whether the hidden error occurred; exports include the private audit fields.

## Treatment Cells

| Picture condition | Error condition | Box label |
| --- | --- | --- |
| No picture | No error | No error / No picture |
| No picture | Error active | Error / No picture |
| Picture | No error | No error / Picture |
| Picture | Error active | Error / Picture |

The oTree demo page shows one session config, `trust_game_randomized`. The treatment
box is drawn separately for each period, not each round. The two rounds in a period
always use the same box.

## Running with oTree

Use the same Python environment where oTree is installed. This project targets oTree 6.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\otree.exe devserver
```

Then open the local oTree URL printed by the server and create the randomized trust-game
session config.

Available oTree session config:

- `trust_game_randomized`

Error parameters are set in `settings.py`:

```python
error_probability=0.50
error_return_multiplier=0.50
```

For example, changing `error_return_multiplier` to `0.25` means the proposer receives
25% of the responder's intended point return when the error occurs.

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

When a period is assigned to a picture condition, oTree displays the matching image
automatically. When pictures are not visible, participants only see anonymous partner labels.

## Standalone Prototype

You can still open `index.html` directly in a browser to view the earlier local prototype.
Use the oTree app for actual oTree sessions.

## Data Export

Use oTree's admin data export. The app defines a custom export with one row per
proposer-responder round. The export includes:

- treatment box
- error probability and return multiplier
- period, round, and pair number
- proposer and responder IDs/names
- offer
- tripled points
- responder's intended return
- whether the hidden error applied
- points delivered back to the proposer
- proposer's belief about how many points the responder sent back
- final proposer and responder points
