from os import environ


IS_PRODUCTION = bool(environ.get("OTREE_PRODUCTION"))

SESSION_CONFIGS = [
    dict(
        name="trust_game_randomized",
        display_name="Trust Game - No Pictures",
        num_demo_participants=10,
        app_sequence=["trust_game"],
        # Session-level design parameters. These can be changed for a session
        # configuration without changing the app's decision logic.
        low_multiplier=3.0,
        high_multiplier=6.0,
        high_multiplier_probability=0.50,
        trust_point_dollar_value=0.30,
        belief_prize_dollars=2.00,
        # Between-session treatment. Set to True for picture sessions and
        # False for sessions in which participants never see pictures.
        picture_condition=False,
    ),
    dict(
        name="trust_game_randomized_pictures",
        display_name="Trust Game - Pictures",
        num_demo_participants=10,
        app_sequence=["trust_game"],
        low_multiplier=3.0,
        high_multiplier=6.0,
        high_multiplier_probability=0.50,
        trust_point_dollar_value=0.30,
        belief_prize_dollars=2.00,
        picture_condition=True,
    ),
]

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00,
    participation_fee=10.00,
    low_multiplier=3.0,
    high_multiplier=6.0,
    high_multiplier_probability=0.50,
    trust_point_dollar_value=0.30,
    belief_prize_dollars=2.00,
    picture_condition=False,
    doc="",
)

PARTICIPANT_FIELDS = ["role_name", "role_number"]
SESSION_FIELDS = []

LANGUAGE_CODE = "en"
REAL_WORLD_CURRENCY_CODE = "USD"
# player.payoff is stored directly in dollars. Trust-game decisions remain
# denominated in experimental points and are converted explicitly in the app.
USE_POINTS = False

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = environ.get("OTREE_ADMIN_PASSWORD")
SECRET_KEY = environ.get("OTREE_SECRET_KEY")

if not IS_PRODUCTION:
    ADMIN_PASSWORD = ADMIN_PASSWORD or "admin"
    SECRET_KEY = SECRET_KEY or "trust-game-dev-secret-key"
else:
    if not ADMIN_PASSWORD:
        raise RuntimeError("Set OTREE_ADMIN_PASSWORD before running in production.")
    if not SECRET_KEY:
        raise RuntimeError("Set OTREE_SECRET_KEY before running in production.")

INSTALLED_APPS = ["otree"]
OTREE_APPS = ["trust_game"]
