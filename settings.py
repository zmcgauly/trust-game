from os import environ


IS_PRODUCTION = bool(environ.get("OTREE_PRODUCTION"))

SESSION_CONFIGS = [
    dict(
        name="trust_game_certain_no_picture",
        display_name="Trust Game - Certain Multiplier / No Pictures",
        num_demo_participants=10,
        app_sequence=["trust_game"],
        treatment_randomization_level="session_multiplier",
        is_real_experiment=True,
        picture_condition=False,
        random_multiplier_condition=False,
        belief_prize_dollars=2.00,
        chance_of_3=0.50,
        large_multiplier=6,
    ),
    dict(
        name="trust_game_certain_picture",
        display_name="Trust Game - Certain Multiplier / Pictures",
        num_demo_participants=10,
        app_sequence=["trust_game"],
        treatment_randomization_level="session_multiplier",
        is_real_experiment=True,
        picture_condition=True,
        random_multiplier_condition=False,
        belief_prize_dollars=2.00,
        chance_of_3=0.50,
        large_multiplier=6,
    ),
    dict(
        name="trust_game_uncertain_no_picture",
        display_name="Trust Game - Uncertain Multiplier / No Pictures",
        num_demo_participants=10,
        app_sequence=["trust_game"],
        treatment_randomization_level="session_multiplier",
        is_real_experiment=True,
        picture_condition=False,
        random_multiplier_condition=True,
        belief_prize_dollars=2.00,
        chance_of_3=0.50,
        large_multiplier=6,
    ),
    dict(
        name="trust_game_uncertain_picture",
        display_name="Trust Game - Uncertain Multiplier / Pictures",
        num_demo_participants=10,
        app_sequence=["trust_game"],
        treatment_randomization_level="session_multiplier",
        is_real_experiment=True,
        picture_condition=True,
        random_multiplier_condition=True,
        belief_prize_dollars=2.00,
        chance_of_3=0.50,
        large_multiplier=6,
    ),
]

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=0.20,
    participation_fee=10.00,
    treatment_randomization_level="session_multiplier",
    picture_condition=False,
    random_multiplier_condition=False,
    belief_prize_dollars=2.00,
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
