from os import environ


IS_PRODUCTION = bool(environ.get("OTREE_PRODUCTION"))

SESSION_CONFIGS = [
    dict(
        name="trust_game_no_picture_no_description",
        display_name="Trust Game - No Picture / No Description",
        num_demo_participants=10,
        app_sequence=["trust_game"],
        # Session-level design parameters. These can be changed for a session
        # configuration without changing the app's decision logic.
        low_multiplier=3.0,
        high_multiplier=6.0,
        low_multiplier_probability=0.50,
        high_multiplier_probability=0.50,
        trust_point_dollar_value=0.30,
        belief_prize_dollars=2.00,
        is_real_experiment=True,
        # Between-session treatments.
        picture_condition=False,
        written_description_condition=False,
    ),
    dict(
        name="trust_game_no_picture_description",
        display_name="Trust Game - No Picture / Description",
        num_demo_participants=10,
        app_sequence=["trust_game"],
        low_multiplier=3.0,
        high_multiplier=6.0,
        low_multiplier_probability=0.50,
        high_multiplier_probability=0.50,
        trust_point_dollar_value=0.30,
        belief_prize_dollars=2.00,
        is_real_experiment=True,
        picture_condition=False,
        written_description_condition=True,
    ),
    dict(
        name="trust_game_picture_no_description",
        display_name="Trust Game - Picture / No Description",
        num_demo_participants=10,
        app_sequence=["trust_game"],
        low_multiplier=3.0,
        high_multiplier=6.0,
        low_multiplier_probability=0.50,
        high_multiplier_probability=0.50,
        trust_point_dollar_value=0.30,
        belief_prize_dollars=2.00,
        is_real_experiment=True,
        picture_condition=True,
        written_description_condition=False,
    ),
    dict(
        name="trust_game_picture_description",
        display_name="Trust Game - Picture / Description",
        num_demo_participants=10,
        app_sequence=["trust_game"],
        low_multiplier=3.0,
        high_multiplier=6.0,
        low_multiplier_probability=0.50,
        high_multiplier_probability=0.50,
        trust_point_dollar_value=0.30,
        belief_prize_dollars=2.00,
        is_real_experiment=True,
        picture_condition=True,
        written_description_condition=True,
    ),
]

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00,
    participation_fee=10.00,
    low_multiplier=3.0,
    high_multiplier=6.0,
    low_multiplier_probability=0.50,
    high_multiplier_probability=0.50,
    trust_point_dollar_value=0.30,
    belief_prize_dollars=2.00,
    is_real_experiment=True,
    picture_condition=False,
    written_description_condition=False,
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
