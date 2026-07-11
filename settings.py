from os import environ


IS_PRODUCTION = bool(environ.get("OTREE_PRODUCTION"))

SESSION_CONFIGS = [
    dict(
        name="trust_game_randomized",
        display_name="Trust Game - Randomized by Period",
        num_demo_participants=10,
        app_sequence=["trust_game"],
        randomize_treatment_by_period=True,
        high_multiplier_probability=0.50,
    ),
]

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00,
    participation_fee=0.00,
    doc="",
)

PARTICIPANT_FIELDS = ["role_name", "role_number"]
SESSION_FIELDS = []

LANGUAGE_CODE = "en"
REAL_WORLD_CURRENCY_CODE = "USD"
USE_POINTS = True

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
