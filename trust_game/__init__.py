import random
from urllib.parse import quote

from otree.api import *


doc = """
Two-person trust game with fixed proposer/responder roles, rotating partners,
two rounds per period, independently randomized multipliers by group and round,
and incentivized probability reports after the return is revealed.
"""


class C(BaseConstants):
    NAME_IN_URL = "trust_game"
    PLAYERS_PER_GROUP = 2
    PRACTICE_ROUNDS = 2
    ROUNDS_PER_PERIOD = 2
    MAX_PERIODS = 10
    PERIODS = MAX_PERIODS
    NUM_ROUNDS = PRACTICE_ROUNDS + (MAX_PERIODS * ROUNDS_PER_PERIOD)
    ENDOWMENT = 20
    DEFAULT_LOW_MULTIPLIER = 3.0
    DEFAULT_HIGH_MULTIPLIER = 6.0
    DEFAULT_HIGH_MULTIPLIER_PROBABILITY = 0.50
    DEFAULT_TRUST_POINT_DOLLAR_VALUE = 0.30
    DEFAULT_BELIEF_PRIZE_DOLLARS = 2.00
    INSTRUCTION_QUIZ_MAX_ATTEMPTS = 3
    MIN_AGE = 18
    MAX_AGE = 100
    GENDER_CHOICES = [
        ["Female", "Female"], ["Male", "Male"], ["Non-Binary", "Non-Binary"],
        ["Other", "Other"], ["Prefer not to say", "Prefer not to say"],
    ]
    GENDER_GUESS_CHOICES = [
        ["Female", "Female"], ["Male", "Male"], ["Non-Binary", "Non-Binary"], ["Other", "Other"],
    ]
    RACE_CHOICES = [
        ["Caucasian (white)", "Caucasian (white)"], ["African American", "African American"],
        ["Latino", "Latino"], ["Asian or Pacific Islander", "Asian or Pacific Islander"],
        ["Native American", "Native American"], ["Other", "Other"],
        ["Prefer not to say", "Prefer not to say"],
    ]
    RACE_GUESS_CHOICES = [
        ["Caucasian (white)", "Caucasian (white)"], ["African American", "African American"],
        ["Latino", "Latino"], ["Asian or Pacific Islander", "Asian or Pacific Islander"],
        ["Native American", "Native American"], ["Other", "Other"],
    ]
    ETHNICITY_CHOICES = [["Yes", "Yes"], ["No", "No"], ["Prefer not to say", "Prefer not to say"]]
    ETHNICITY_GUESS_CHOICES = [["Yes", "Yes"], ["No", "No"]]
    SEXUALITY_CHOICES = [
        ["Straight", "Straight"], ["Gay", "Gay"], ["Bi-Sexual", "Bi-Sexual"],
        ["Pansexual", "Pansexual"], ["Asexual", "Asexual"], ["Other", "Other"],
        ["Prefer not to say", "Prefer not to say"],
    ]
    SEXUALITY_GUESS_CHOICES = [
        ["Straight", "Straight"], ["Gay", "Gay"], ["Bi-Sexual", "Bi-Sexual"],
        ["Pansexual", "Pansexual"], ["Asexual", "Asexual"], ["Other", "Other"],
    ]
    CONFIDENCE_CHOICES = [
        ["Sure", "Sure"], ["Unsure", "Unsure"],
        ["Neither Sure or Unsure", "Neither Sure or Unsure"],
    ]
    CONFIDENCE_LABEL = "Confidence in Guess"
    RELATIONSHIP_CHOICES = [["No", "No"], ["Yes", "Yes"], ["Prefer not to say", "Prefer not to say"]]
    PROFILE_DESCRIPTIONS = {}


class Subsession(BaseSubsession):
    def vars_for_admin_report(self):
        rows = []
        active_periods = get_active_periods(self.session)
        for period in range(1, active_periods + 1):
            rows.append(dict(
                period=period,
                picture_text="Shown" if get_picture_condition(self.session) else "Not shown",
                written_description_text=(
                    "Shown" if get_written_description_condition(self.session) else "Not shown"
                ),
                paid_text="Yes" if period == get_paid_period(self.session) else "No",
            ))
        return dict(
            period_rows=rows,
            active_periods=active_periods,
            low_multiplier=display_number(get_low_multiplier(self.session)),
            high_multiplier=display_number(get_high_multiplier(self.session)),
            high_multiplier_probability=get_high_multiplier_probability(self.session),
            high_multiplier_probability_percent=round(get_high_multiplier_probability(self.session) * 100, 2),
            trust_point_value=f"{get_trust_point_value(self.session):.2f}",
            belief_prize=f"{get_belief_prize(self.session):.2f}",
            paid_period=get_paid_period(self.session),
        )


class Group(BaseGroup):
    treatment_code = models.StringField()
    treatment_label = models.StringField()
    treatment_picture = models.BooleanField(initial=False)
    treatment_written_description = models.BooleanField(initial=False)
    high_multiplier_probability = models.FloatField()
    low_multiplier = models.FloatField()
    high_multiplier = models.FloatField()
    realized_multiplier = models.FloatField()
    high_multiplier_applied = models.BooleanField(initial=False)

    offer = models.IntegerField(
        min=0,
        max=C.ENDOWMENT,
        label="How many of your 20 points do you send to the responder?",
    )
    intended_return = models.IntegerField(min=0, label="How many points do you send back to the proposer?")
    delivered_return = models.IntegerField(initial=0)

    def multiplied_amount(self):
        offer = self.field_maybe_none("offer")
        multiplier = self.field_maybe_none("realized_multiplier")
        if offer is None or multiplier is None:
            return 0
        return offer * multiplier

    def tripled_amount(self):
        return self.multiplied_amount()


class Player(BasePlayer):
    role_name = models.StringField()
    role_number = models.IntegerField()
    is_practice_round = models.BooleanField(initial=False)
    is_active_round = models.BooleanField(initial=True)
    period_number = models.IntegerField()
    round_in_period = models.IntegerField()
    skip_instructions = models.StringField(blank=True, initial="")

    round_points = models.FloatField(initial=0)
    trust_game_payment = models.CurrencyField(initial=0)
    is_paid_period = models.BooleanField(initial=False)

    belief_post_probability_low = models.IntegerField(
        min=0, max=100,
        label="After seeing the returned amount, what is the probability that the low multiplier was used?",
    )
    belief_selected_for_payment = models.BooleanField(initial=False)
    belief_winning_chance = models.FloatField()
    belief_bonus_draw = models.IntegerField()
    belief_bonus_awarded = models.BooleanField(initial=False)
    belief_bonus = models.CurrencyField(initial=0)

    instruction_quiz_1 = models.StringField(
        choices=[["same", "Your role stays the same for the entire session."],
                 ["changes", "Your role changes after each period."],
                 ["chosen", "You choose your role before each round."]],
        label="What happens to your role during the session?", widget=widgets.RadioSelect,
    )
    instruction_quiz_2 = models.StringField(
        choices=[["learning", "Practice rounds are only for learning and cannot be selected for payoff."],
                 ["included", "Practice rounds can be selected for payoff."],
                 ["none", "There are no practice rounds."]],
        label="How are practice rounds treated?", widget=widgets.RadioSelect,
    )
    instruction_quiz_3 = models.StringField(
        choices=[["zero_to_twenty", "The proposer chooses a whole number from 0 to 20."],
                 ["all_or_nothing", "The proposer must send either 0 or 20 points."],
                 ["responder_decides", "The responder chooses the amount sent."]],
        label="What can the proposer send in each round?", widget=widgets.RadioSelect,
    )
    instruction_quiz_4 = models.StringField(
        choices=[["sent_available", "The amount sent and the amount available after multiplication."],
                 ["only_sent", "Only the amount sent."],
                 ["nothing", "Neither amount."]],
        label="What does the responder see before choosing a return?", widget=widgets.RadioSelect,
    )
    instruction_quiz_5 = models.StringField(
        choices=[
            [
                "correct",
                (
                    r"Proposer: \(\text{proposer round points} = 20 - "
                    r"\text{points sent} + \text{points returned}\); "
                    r"Responder: \(\text{responder round points} = "
                    r"\text{points sent} \times \text{realized multiplier} - "
                    r"\text{points returned}\)."
                ),
            ],
            [
                "swapped",
                (
                    r"Proposer: \(\text{proposer round points} = "
                    r"\text{points sent} \times \text{realized multiplier} - "
                    r"\text{points returned}\); Responder: "
                    r"\(\text{responder round points} = 20 - "
                    r"\text{points sent} + \text{points returned}\)."
                ),
            ],
            [
                "same",
                (
                    r"Both receive \(\text{round points} = "
                    r"\text{points sent} \times \text{realized multiplier} - "
                    r"\text{points returned}\)."
                ),
            ],
        ],
        label="How are round points calculated?", widget=widgets.RadioSelect,
    )
    instruction_quiz_6 = models.StringField(
        choices=[["both_rounds", "One period is selected; both rounds' trust-game outcomes and both proposer belief reports determine payment."],
                 ["one_round", "Only one randomly selected round is paid."],
                 ["all_rounds", "Every real round is paid."]],
        label="Which decisions determine payment?", widget=widgets.RadioSelect,
    )
    instruction_quiz_7 = models.StringField(
        choices=[
            ["sixty", "60%"],
            ["eighty_four", "84%"],
            ["forty", "40%"],
            ["sixteen", "16%"],
        ],
        label=(
            r"Suppose the multiplier really was low and you reported \(X = 60\%\). "
            r"What is your probability of winning that round's belief prize?"
        ),
        widget=widgets.RadioSelect,
    )

    gender = models.StringField(choices=C.GENDER_CHOICES, label="What is your gender?", blank=True)
    race = models.StringField(choices=C.RACE_CHOICES, label="What is your race?", blank=True)
    ethnicity = models.StringField(choices=C.ETHNICITY_CHOICES, label="Are you Hispanic or Latino?", blank=True)
    age = models.IntegerField(label="What is your age?", min=0, max=C.MAX_AGE, blank=True)
    age_prefer_not_to_say = models.BooleanField(label="I prefer not to say", blank=True, initial=False)
    sexuality = models.StringField(choices=C.SEXUALITY_CHOICES, label="What is your sexuality?", blank=True)

    partner_1_age_guess = models.IntegerField(label="Guess this person's age.", min=0, max=C.MAX_AGE)
    partner_1_age_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_1_ethnicity_guess = models.StringField(choices=C.ETHNICITY_GUESS_CHOICES, label="Guess if this person identifies as Hispanic or Latino.")
    partner_1_ethnicity_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_1_race_guess = models.StringField(choices=C.RACE_GUESS_CHOICES, label="Guess what race this person identifies as.")
    partner_1_race_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_1_gender_guess = models.StringField(choices=C.GENDER_GUESS_CHOICES, label="Guess what gender this person identifies as.")
    partner_1_gender_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_1_sexuality_guess = models.StringField(choices=C.SEXUALITY_GUESS_CHOICES, label="Guess what sexuality this person identifies as.")
    partner_1_sexuality_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_1_existing_relationship = models.StringField(choices=C.RELATIONSHIP_CHOICES, label="Do you have an existing relationship with this person?")
    partner_1_relationship_nature = models.LongStringField(label="If so, what is the nature of the relationship?", blank=True)
    partner_2_age_guess = models.IntegerField(label="Guess this person's age.", min=0, max=C.MAX_AGE)
    partner_2_age_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_2_ethnicity_guess = models.StringField(choices=C.ETHNICITY_GUESS_CHOICES, label="Guess if this person identifies as Hispanic or Latino.")
    partner_2_ethnicity_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_2_race_guess = models.StringField(choices=C.RACE_GUESS_CHOICES, label="Guess what race this person identifies as.")
    partner_2_race_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_2_gender_guess = models.StringField(choices=C.GENDER_GUESS_CHOICES, label="Guess what gender this person identifies as.")
    partner_2_gender_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_2_sexuality_guess = models.StringField(choices=C.SEXUALITY_GUESS_CHOICES, label="Guess what sexuality this person identifies as.")
    partner_2_sexuality_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_2_existing_relationship = models.StringField(choices=C.RELATIONSHIP_CHOICES, label="Do you have an existing relationship with this person?")
    partner_2_relationship_nature = models.LongStringField(label="If so, what is the nature of the relationship?", blank=True)
    partner_3_age_guess = models.IntegerField(label="Guess this person's age.", min=0, max=C.MAX_AGE)
    partner_3_age_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_3_ethnicity_guess = models.StringField(choices=C.ETHNICITY_GUESS_CHOICES, label="Guess if this person identifies as Hispanic or Latino.")
    partner_3_ethnicity_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_3_race_guess = models.StringField(choices=C.RACE_GUESS_CHOICES, label="Guess what race this person identifies as.")
    partner_3_race_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_3_gender_guess = models.StringField(choices=C.GENDER_GUESS_CHOICES, label="Guess what gender this person identifies as.")
    partner_3_gender_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_3_sexuality_guess = models.StringField(choices=C.SEXUALITY_GUESS_CHOICES, label="Guess what sexuality this person identifies as.")
    partner_3_sexuality_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_3_existing_relationship = models.StringField(choices=C.RELATIONSHIP_CHOICES, label="Do you have an existing relationship with this person?")
    partner_3_relationship_nature = models.LongStringField(label="If so, what is the nature of the relationship?", blank=True)
    partner_4_age_guess = models.IntegerField(label="Guess this person's age.", min=0, max=C.MAX_AGE)
    partner_4_age_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_4_ethnicity_guess = models.StringField(choices=C.ETHNICITY_GUESS_CHOICES, label="Guess if this person identifies as Hispanic or Latino.")
    partner_4_ethnicity_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_4_race_guess = models.StringField(choices=C.RACE_GUESS_CHOICES, label="Guess what race this person identifies as.")
    partner_4_race_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_4_gender_guess = models.StringField(choices=C.GENDER_GUESS_CHOICES, label="Guess what gender this person identifies as.")
    partner_4_gender_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_4_sexuality_guess = models.StringField(choices=C.SEXUALITY_GUESS_CHOICES, label="Guess what sexuality this person identifies as.")
    partner_4_sexuality_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_4_existing_relationship = models.StringField(choices=C.RELATIONSHIP_CHOICES, label="Do you have an existing relationship with this person?")
    partner_4_relationship_nature = models.LongStringField(label="If so, what is the nature of the relationship?", blank=True)
    partner_5_age_guess = models.IntegerField(label="Guess this person's age.", min=0, max=C.MAX_AGE)
    partner_5_age_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_5_ethnicity_guess = models.StringField(choices=C.ETHNICITY_GUESS_CHOICES, label="Guess if this person identifies as Hispanic or Latino.")
    partner_5_ethnicity_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_5_race_guess = models.StringField(choices=C.RACE_GUESS_CHOICES, label="Guess what race this person identifies as.")
    partner_5_race_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_5_gender_guess = models.StringField(choices=C.GENDER_GUESS_CHOICES, label="Guess what gender this person identifies as.")
    partner_5_gender_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_5_sexuality_guess = models.StringField(choices=C.SEXUALITY_GUESS_CHOICES, label="Guess what sexuality this person identifies as.")
    partner_5_sexuality_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_5_existing_relationship = models.StringField(choices=C.RELATIONSHIP_CHOICES, label="Do you have an existing relationship with this person?")
    partner_5_relationship_nature = models.LongStringField(label="If so, what is the nature of the relationship?", blank=True)
    partner_6_age_guess = models.IntegerField(label="Guess this person's age.", min=0, max=C.MAX_AGE)
    partner_6_age_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_6_ethnicity_guess = models.StringField(choices=C.ETHNICITY_GUESS_CHOICES, label="Guess if this person identifies as Hispanic or Latino.")
    partner_6_ethnicity_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_6_race_guess = models.StringField(choices=C.RACE_GUESS_CHOICES, label="Guess what race this person identifies as.")
    partner_6_race_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_6_gender_guess = models.StringField(choices=C.GENDER_GUESS_CHOICES, label="Guess what gender this person identifies as.")
    partner_6_gender_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_6_sexuality_guess = models.StringField(choices=C.SEXUALITY_GUESS_CHOICES, label="Guess what sexuality this person identifies as.")
    partner_6_sexuality_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_6_existing_relationship = models.StringField(choices=C.RELATIONSHIP_CHOICES, label="Do you have an existing relationship with this person?")
    partner_6_relationship_nature = models.LongStringField(label="If so, what is the nature of the relationship?", blank=True)
    partner_7_age_guess = models.IntegerField(label="Guess this person's age.", min=0, max=C.MAX_AGE)
    partner_7_age_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_7_ethnicity_guess = models.StringField(choices=C.ETHNICITY_GUESS_CHOICES, label="Guess if this person identifies as Hispanic or Latino.")
    partner_7_ethnicity_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_7_race_guess = models.StringField(choices=C.RACE_GUESS_CHOICES, label="Guess what race this person identifies as.")
    partner_7_race_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_7_gender_guess = models.StringField(choices=C.GENDER_GUESS_CHOICES, label="Guess what gender this person identifies as.")
    partner_7_gender_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_7_sexuality_guess = models.StringField(choices=C.SEXUALITY_GUESS_CHOICES, label="Guess what sexuality this person identifies as.")
    partner_7_sexuality_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_7_existing_relationship = models.StringField(choices=C.RELATIONSHIP_CHOICES, label="Do you have an existing relationship with this person?")
    partner_7_relationship_nature = models.LongStringField(label="If so, what is the nature of the relationship?", blank=True)
    partner_8_age_guess = models.IntegerField(label="Guess this person's age.", min=0, max=C.MAX_AGE)
    partner_8_age_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_8_ethnicity_guess = models.StringField(choices=C.ETHNICITY_GUESS_CHOICES, label="Guess if this person identifies as Hispanic or Latino.")
    partner_8_ethnicity_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_8_race_guess = models.StringField(choices=C.RACE_GUESS_CHOICES, label="Guess what race this person identifies as.")
    partner_8_race_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_8_gender_guess = models.StringField(choices=C.GENDER_GUESS_CHOICES, label="Guess what gender this person identifies as.")
    partner_8_gender_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_8_sexuality_guess = models.StringField(choices=C.SEXUALITY_GUESS_CHOICES, label="Guess what sexuality this person identifies as.")
    partner_8_sexuality_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_8_existing_relationship = models.StringField(choices=C.RELATIONSHIP_CHOICES, label="Do you have an existing relationship with this person?")
    partner_8_relationship_nature = models.LongStringField(label="If so, what is the nature of the relationship?", blank=True)
    partner_9_age_guess = models.IntegerField(label="Guess this person's age.", min=0, max=C.MAX_AGE)
    partner_9_age_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_9_ethnicity_guess = models.StringField(choices=C.ETHNICITY_GUESS_CHOICES, label="Guess if this person identifies as Hispanic or Latino.")
    partner_9_ethnicity_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_9_race_guess = models.StringField(choices=C.RACE_GUESS_CHOICES, label="Guess what race this person identifies as.")
    partner_9_race_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_9_gender_guess = models.StringField(choices=C.GENDER_GUESS_CHOICES, label="Guess what gender this person identifies as.")
    partner_9_gender_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_9_sexuality_guess = models.StringField(choices=C.SEXUALITY_GUESS_CHOICES, label="Guess what sexuality this person identifies as.")
    partner_9_sexuality_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_9_existing_relationship = models.StringField(choices=C.RELATIONSHIP_CHOICES, label="Do you have an existing relationship with this person?")
    partner_9_relationship_nature = models.LongStringField(label="If so, what is the nature of the relationship?", blank=True)
    partner_10_age_guess = models.IntegerField(label="Guess this person's age.", min=0, max=C.MAX_AGE)
    partner_10_age_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_10_ethnicity_guess = models.StringField(choices=C.ETHNICITY_GUESS_CHOICES, label="Guess if this person identifies as Hispanic or Latino.")
    partner_10_ethnicity_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_10_race_guess = models.StringField(choices=C.RACE_GUESS_CHOICES, label="Guess what race this person identifies as.")
    partner_10_race_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_10_gender_guess = models.StringField(choices=C.GENDER_GUESS_CHOICES, label="Guess what gender this person identifies as.")
    partner_10_gender_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_10_sexuality_guess = models.StringField(choices=C.SEXUALITY_GUESS_CHOICES, label="Guess what sexuality this person identifies as.")
    partner_10_sexuality_confidence = models.StringField(choices=C.CONFIDENCE_CHOICES, label=C.CONFIDENCE_LABEL)
    partner_10_existing_relationship = models.StringField(choices=C.RELATIONSHIP_CHOICES, label="Do you have an existing relationship with this person?")
    partner_10_relationship_nature = models.LongStringField(label="If so, what is the nature of the relationship?", blank=True)


def config_float(session, key, default):
    return float(session.config.get(key, default))


def config_bool(session, key, default):
    value = session.config.get(key, default)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def get_low_multiplier(session):
    return config_float(session, "low_multiplier", C.DEFAULT_LOW_MULTIPLIER)


def get_high_multiplier(session):
    return config_float(session, "high_multiplier", C.DEFAULT_HIGH_MULTIPLIER)


def get_low_multiplier_probability(session):
    if "low_multiplier_probability" in session.config:
        return config_float(
            session,
            "low_multiplier_probability",
            1 - C.DEFAULT_HIGH_MULTIPLIER_PROBABILITY,
        )
    return 1 - config_float(
        session,
        "high_multiplier_probability",
        C.DEFAULT_HIGH_MULTIPLIER_PROBABILITY,
    )


def get_high_multiplier_probability(session):
    return 1 - get_low_multiplier_probability(session)


def get_trust_point_value(session):
    return config_float(session, "trust_point_dollar_value", C.DEFAULT_TRUST_POINT_DOLLAR_VALUE)


def get_belief_prize(session):
    return config_float(session, "belief_prize_dollars", C.DEFAULT_BELIEF_PRIZE_DOLLARS)


def validate_session_parameters(session):
    low = get_low_multiplier(session)
    high = get_high_multiplier(session)
    probability = get_high_multiplier_probability(session)
    low_probability = get_low_multiplier_probability(session)
    point_value = get_trust_point_value(session)
    belief_prize = get_belief_prize(session)
    if low <= 0:
        raise ValueError("low_multiplier must be positive.")
    if high <= low:
        raise ValueError("high_multiplier must be greater than low_multiplier.")
    if not 0 <= probability <= 1:
        raise ValueError("high_multiplier_probability must be between 0 and 1.")
    if not 0 <= low_probability <= 1:
        raise ValueError("low_multiplier_probability must be between 0 and 1.")
    if point_value < 0 or belief_prize < 0:
        raise ValueError("Payment parameters cannot be negative.")


def display_number(value):
    value = float(value)
    return int(value) if value.is_integer() else value


def role_counts_for_session(players):
    participant_count = len(players)
    if participant_count < C.PLAYERS_PER_GROUP or participant_count % C.PLAYERS_PER_GROUP:
        raise ValueError(
            "This trust-game schedule requires an even number of participants, "
            "with half assigned as proposers and half assigned as responders."
        )
    proposer_count = participant_count // 2
    responder_count = participant_count - proposer_count
    return proposer_count, responder_count


def get_active_periods(session):
    return int(session.vars.get("active_periods", 1))


def get_picture_condition(session):
    return bool(session.vars.get("picture_condition", False))


def get_written_description_condition(session):
    return bool(session.vars.get("written_description_condition", False))


def treatment_code(picture, written_description):
    picture_text = "picture" if picture else "no_picture"
    description_text = "description" if written_description else "no_description"
    return f"{picture_text}_{description_text}"


def treatment_label(picture, written_description):
    picture_text = "Picture" if picture else "No picture"
    description_text = "description" if written_description else "no description"
    return f"{picture_text} / {description_text}"


def get_paid_period(session):
    return int(session.vars.get("paid_period", 1))


def real_round_number(record):
    return record.round_number - C.PRACTICE_ROUNDS


def is_practice_round(record):
    return record.round_number <= C.PRACTICE_ROUNDS


def period_and_round(record):
    if is_practice_round(record):
        return 0, record.round_number
    real_round = real_round_number(record)
    period_index = (real_round - 1) // C.ROUNDS_PER_PERIOD
    round_in_period = ((real_round - 1) % C.ROUNDS_PER_PERIOD) + 1
    return period_index + 1, round_in_period


def last_active_round(session):
    return C.PRACTICE_ROUNDS + get_active_periods(session) * C.ROUNDS_PER_PERIOD


def choose_realized_multiplier(session):
    if random.random() < get_high_multiplier_probability(session):
        return get_high_multiplier(session)
    return get_low_multiplier(session)


def creating_session(subsession: Subsession):
    players = subsession.get_players()
    proposer_count, responder_count = role_counts_for_session(players)

    if subsession.round_number == 1:
        validate_session_parameters(subsession.session)
        # With fixed roles, each participant can meet every opposite-role participant once.
        active_periods = min(C.MAX_PERIODS, responder_count)
        subsession.session.vars["active_periods"] = active_periods
        subsession.session.vars["unique_cross_role_pairs"] = proposer_count * responder_count
        # Visual and written partner cues are between-session treatments.
        subsession.session.vars["picture_condition"] = config_bool(
            subsession.session,
            "picture_condition",
            False,
        )
        subsession.session.vars["written_description_condition"] = config_bool(
            subsession.session,
            "written_description_condition",
            False,
        )
        subsession.session.vars["paid_period"] = random.randint(1, active_periods)
        subsession.session.vars["high_multiplier_probability_percent"] = round(
            get_high_multiplier_probability(subsession.session) * 100, 2
        )

    practice = is_practice_round(subsession)
    period_number, round_in_period = period_and_round(subsession)
    active = practice or period_number <= get_active_periods(subsession.session)
    period_index_for_matching = 0 if practice else period_number - 1

    proposers = players[:proposer_count]
    responders = players[proposer_count:]
    group_matrix = []
    for index, proposer in enumerate(proposers):
        responder = responders[(index + period_index_for_matching) % responder_count]
        group_matrix.append([proposer, responder])
    subsession.set_group_matrix(group_matrix)

    picture = get_picture_condition(subsession.session)
    written_description = get_written_description_condition(subsession.session)

    for group in subsession.get_groups():
        realized_multiplier = choose_realized_multiplier(subsession.session)
        group.treatment_code = treatment_code(picture, written_description)
        group.treatment_label = treatment_label(picture, written_description)
        group.treatment_picture = picture
        group.treatment_written_description = written_description
        group.low_multiplier = get_low_multiplier(subsession.session)
        group.high_multiplier = get_high_multiplier(subsession.session)
        group.high_multiplier_probability = get_high_multiplier_probability(subsession.session)
        group.realized_multiplier = realized_multiplier
        group.high_multiplier_applied = realized_multiplier == get_high_multiplier(subsession.session)

    for player in subsession.get_players():
        is_proposer = player.id_in_subsession <= proposer_count
        role_name = "proposer" if is_proposer else "responder"
        role_number = player.id_in_subsession if is_proposer else player.id_in_subsession - proposer_count
        player.role_name = role_name
        player.role_number = role_number
        player.is_practice_round = practice
        player.is_active_round = active
        player.period_number = period_number
        player.round_in_period = round_in_period
        if subsession.round_number == 1:
            player.participant.role_name = role_name
            player.participant.role_number = role_number


def get_proposer(group: Group):
    return next(player for player in group.get_players() if player.role_name == "proposer")


def get_responder(group: Group):
    return next(player for player in group.get_players() if player.role_name == "responder")


def get_partner(player: Player):
    return get_responder(player.group) if player.role_name == "proposer" else get_proposer(player.group)


def profile_for(player: Player):
    title = f"Player {player.id_in_subsession}"
    picture_path = f"trust_game/players/{title}.jpg"
    return dict(title=title, picture_url=f"/static/{quote(picture_path)}")


def treatment_picture(player: Player):
    return get_picture_condition(player.session)


def treatment_written_description(player: Player):
    return get_written_description_condition(player.session)


def treatment_partner_cue(player: Player):
    return treatment_picture(player) or treatment_written_description(player)


def self_demographic_player(player: Player):
    return player.in_round(1)


def normalized_demographic_value(value):
    if value in {None, "", "Prefer not to say"}:
        return None
    return value


def self_demographic_description_for(player: Player):
    source = self_demographic_player(player)
    statements = []

    age = source.field_maybe_none("age")
    if age is not None and not source.field_maybe_none("age_prefer_not_to_say"):
        statements.append(f"is {age} years old")

    ethnicity = normalized_demographic_value(source.field_maybe_none("ethnicity"))
    if ethnicity is not None:
        if ethnicity == "Yes":
            statements.append("identifies as Hispanic or Latino")
        elif ethnicity == "No":
            statements.append("does not identify as Hispanic or Latino")

    race = normalized_demographic_value(source.field_maybe_none("race"))
    if race is not None:
        statements.append(f"identifies their race as {race}")

    gender = normalized_demographic_value(source.field_maybe_none("gender"))
    if gender is not None:
        statements.append(f"identifies their gender as {gender}")

    sexuality = normalized_demographic_value(source.field_maybe_none("sexuality"))
    if sexuality is not None:
        statements.append(f"identifies their sexuality as {sexuality}")

    if not statements:
        return "This participant chose not to report demographic information."
    return "This participant " + "; ".join(statements) + "."


def written_description_for(player: Player, partner: Player):
    descriptions = player.session.config.get("written_profile_descriptions", C.PROFILE_DESCRIPTIONS) or {}
    title = profile_for(partner)["title"]
    return (
        descriptions.get(title)
        or descriptions.get(str(partner.id_in_subsession))
        or self_demographic_description_for(partner)
    )


def page_common_vars(player: Player):
    return dict(
        total_periods=get_active_periods(player.session),
        picture_condition=get_picture_condition(player.session),
        written_description_condition=get_written_description_condition(player.session),
        low_multiplier=display_number(get_low_multiplier(player.session)),
        high_multiplier=display_number(get_high_multiplier(player.session)),
        high_multiplier_probability=get_high_multiplier_probability(player.session),
        high_multiplier_probability_percent=round(get_high_multiplier_probability(player.session) * 100, 2),
        low_multiplier_probability_percent=round((1 - get_high_multiplier_probability(player.session)) * 100, 2),
        trust_point_value=f"{get_trust_point_value(player.session):.2f}",
        belief_prize=f"{get_belief_prize(player.session):.2f}",
        participation_fee=f"{float(player.session.config.get('participation_fee', 10.00)):.2f}",
        example_22_point_payment=f"{22 * get_trust_point_value(player.session):.2f}",
    )


def show_part1_self_survey(player: Player):
    return player.round_number == 1 and not instruction_quiz_failed(player)


def show_part3_partner_survey(player: Player):
    return player.round_number == last_active_round(player.session)


def show_end_demographic_survey(player: Player):
    return show_part3_partner_survey(player)


def is_real_experiment_session(session):
    return config_bool(session, "is_real_experiment", True)


def instructions_skipped(player: Player):
    return bool(player.participant.vars.get("skip_instructions_and_quiz", False))


def instruction_page_is_displayed(player: Player):
    return player.round_number == 1 and not instructions_skipped(player)


def instruction_page_vars(player: Player):
    return dict(
        **page_common_vars(player),
        show_testing_skip=not is_real_experiment_session(player.session),
    )


def instruction_page_before_next(player: Player, timeout_happened):
    if (
        not is_real_experiment_session(player.session)
        and player.field_maybe_none("skip_instructions") == "1"
    ):
        player.participant.vars["skip_instructions_and_quiz"] = True


def real_round_for_period(period_number):
    return C.PRACTICE_ROUNDS + ((period_number - 1) * C.ROUNDS_PER_PERIOD) + 1


def matched_partner_for_period(player: Player, period_number):
    return get_partner(player.in_round(real_round_for_period(period_number)))


def partner_survey_form_fields(slot):
    prefix = f"partner_{slot}"
    return [
        f"{prefix}_age_guess", f"{prefix}_age_confidence",
        f"{prefix}_ethnicity_guess", f"{prefix}_ethnicity_confidence",
        f"{prefix}_race_guess", f"{prefix}_race_confidence",
        f"{prefix}_gender_guess", f"{prefix}_gender_confidence",
        f"{prefix}_sexuality_guess", f"{prefix}_sexuality_confidence",
        f"{prefix}_existing_relationship", f"{prefix}_relationship_nature",
    ]


def partner_survey_vars(player: Player, slot):
    partner = matched_partner_for_period(player, slot)
    prefix = f"partner_{slot}"
    return dict(
        **page_common_vars(player),
        partner_number=slot,
        partner_profile=profile_for(partner),
        show_profile=treatment_picture(player),
        show_written_description=treatment_written_description(player),
        partner_written_description=written_description_for(player, partner),
        age_guess_field=f"{prefix}_age_guess", age_confidence_field=f"{prefix}_age_confidence",
        ethnicity_guess_field=f"{prefix}_ethnicity_guess", ethnicity_confidence_field=f"{prefix}_ethnicity_confidence",
        race_guess_field=f"{prefix}_race_guess", race_confidence_field=f"{prefix}_race_confidence",
        gender_guess_field=f"{prefix}_gender_guess", gender_confidence_field=f"{prefix}_gender_confidence",
        sexuality_guess_field=f"{prefix}_sexuality_guess", sexuality_confidence_field=f"{prefix}_sexuality_confidence",
        relationship_field=f"{prefix}_existing_relationship",
        relationship_nature_field=f"{prefix}_relationship_nature",
    )


def partner_survey_error_message(values, slot):
    prefix = f"partner_{slot}"
    required_fields = [
        f"{prefix}_age_guess",
        f"{prefix}_age_confidence",
        f"{prefix}_ethnicity_guess",
        f"{prefix}_ethnicity_confidence",
        f"{prefix}_race_guess",
        f"{prefix}_race_confidence",
        f"{prefix}_gender_guess",
        f"{prefix}_gender_confidence",
        f"{prefix}_sexuality_guess",
        f"{prefix}_sexuality_confidence",
        f"{prefix}_existing_relationship",
    ]
    for field in required_fields:
        if values[field] in {None, ""}:
            return {field: "Please answer this question before continuing."}
    age = values[f"{prefix}_age_guess"]
    if age is not None and age < C.MIN_AGE:
        return {f"{prefix}_age_guess": "Please guess an age of 18 or older."}
    relationship = values[f"{prefix}_existing_relationship"]
    relationship_nature = values[f"{prefix}_relationship_nature"] or ""
    if relationship == "Yes" and not relationship_nature.strip():
        return {f"{prefix}_relationship_nature": "Please describe the nature of the relationship."}


def proposer_round_points(group: Group):
    return C.ENDOWMENT - group.offer + group.delivered_return


def responder_round_points(group: Group):
    return group.multiplied_amount() - group.intended_return


def round_summary_vars(player: Player):
    group = player.group
    offer = group.field_maybe_none("offer") or 0
    returned = group.field_maybe_none("delivered_return") or 0
    multiplied_amount = group.multiplied_amount()
    low_multiplier = get_low_multiplier(player.session)
    high_multiplier = get_high_multiplier(player.session)
    low_available = offer * low_multiplier
    high_available = offer * high_multiplier

    if player.role_name == "proposer":
        received_label = "Points you received back"
        received_amount = returned
        final_payoff = C.ENDOWMENT - offer + returned
    else:
        received_label = "Points available to you"
        received_amount = multiplied_amount
        final_payoff = multiplied_amount - returned

    return dict(
        summary_offer=display_number(offer),
        summary_returned=display_number(returned),
        summary_received_label=received_label,
        summary_received_amount=display_number(received_amount),
        summary_payoff=display_number(final_payoff),
        summary_low_multiplier=display_number(low_multiplier),
        summary_high_multiplier=display_number(high_multiplier),
        summary_offer_number=display_number(offer),
        summary_low_available_number=display_number(low_available),
        summary_high_available_number=display_number(high_available),
    )


def set_round_outcomes(group: Group):
    proposer = get_proposer(group)
    responder = get_responder(group)
    group.delivered_return = group.intended_return or 0
    proposer_points = float(proposer_round_points(group))
    responder_points = float(responder_round_points(group))
    proposer.round_points = proposer_points
    responder.round_points = responder_points

    paid = (
        not proposer.is_practice_round
        and proposer.is_active_round
        and proposer.period_number == get_paid_period(group.session)
    )
    proposer.is_paid_period = paid
    responder.is_paid_period = paid
    rate = get_trust_point_value(group.session)
    proposer.trust_game_payment = cu(proposer_points * rate) if paid else cu(0)
    responder.trust_game_payment = cu(responder_points * rate) if paid else cu(0)
    proposer.payoff = proposer.trust_game_payment
    responder.payoff = responder.trust_game_payment


def intended_return_error_message(group: Group, value):
    if value is None:
        return
    max_return = group.multiplied_amount()
    if value > max_return:
        return f"You cannot send back more than {display_number(max_return)} points."


def selected_belief_report(player: Player):
    return (
        not player.is_practice_round
        and player.period_number == get_paid_period(player.session)
    )


def quadratic_winning_chance(probability_low_percent, realized_multiplier, low_multiplier):
    if realized_multiplier == low_multiplier:
        return 100 - ((100 - probability_low_percent) ** 2 / 100)
    return 100 - (probability_low_percent ** 2 / 100)


def record_belief(player: Player):
    if selected_belief_report(player):
        reported_probability = player.belief_post_probability_low
        winning_chance = quadratic_winning_chance(
            reported_probability,
            player.group.realized_multiplier,
            get_low_multiplier(player.session),
        )
        bonus_draw = random.randint(0, 100)
        player.belief_selected_for_payment = True
        player.belief_winning_chance = winning_chance
        player.belief_bonus_draw = bonus_draw
        player.belief_bonus_awarded = bonus_draw <= winning_chance
        player.belief_bonus = cu(get_belief_prize(player.session) if player.belief_bonus_awarded else 0)
        player.payoff += player.belief_bonus


def payment_summary_vars(player: Player):
    paid_period = get_paid_period(player.session)
    paid_rounds = [
        player.in_round(real_round_for_period(paid_period)),
        player.in_round(real_round_for_period(paid_period) + 1),
    ]
    trust_points = sum(p.round_points for p in paid_rounds)
    trust_payment = sum((p.trust_game_payment for p in paid_rounds), cu(0))
    result = {
        **page_common_vars(player),
        "paid_period": paid_period,
        "trust_points": display_number(trust_points),
        "trust_payment": trust_payment,
        "participation_fee": cu(float(player.session.config.get("participation_fee", 10.00))),
        "decision_payment": player.participant.payoff,
        "total_payment": player.participant.payoff_plus_participation_fee(),
        "is_proposer": player.role_name == "proposer",
    }
    if player.role_name == "proposer":
        belief_rows = []
        for belief_player in paid_rounds:
            belief_rows.append(dict(
                round_in_period=belief_player.round_in_period,
                selected_belief_probability=belief_player.belief_post_probability_low,
                realized_multiplier=display_number(belief_player.group.realized_multiplier),
                belief_winning_chance=round(belief_player.belief_winning_chance, 2),
                belief_bonus_draw=belief_player.belief_bonus_draw,
                belief_bonus=belief_player.belief_bonus,
            ))
        result.update(
            belief_rows=belief_rows,
            total_belief_bonus=sum((p.belief_bonus for p in paid_rounds), cu(0)),
        )
    return result


INSTRUCTION_QUIZ_FIELDS = [f"instruction_quiz_{i}" for i in range(1, 8)]
INSTRUCTION_QUIZ_CORRECT_ANSWERS = dict(
    instruction_quiz_1="same", instruction_quiz_2="learning",
    instruction_quiz_3="zero_to_twenty", instruction_quiz_4="sent_available",
    instruction_quiz_5="correct", instruction_quiz_6="both_rounds",
    instruction_quiz_7="eighty_four",
)


def randomized_instruction_quiz_fields():
    fields = INSTRUCTION_QUIZ_FIELDS.copy()
    random.shuffle(fields)
    return fields


def instruction_quiz_failed(player: Player):
    return bool(player.participant.vars.get("instruction_quiz_failed", False))


def instruction_quiz_wrong_attempts(player: Player):
    return int(player.participant.vars.get("instruction_quiz_wrong_attempts", 0))


class RoleNotice(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.is_active_round and player.round_in_period == 1

    @staticmethod
    def vars_for_template(player: Player):
        return dict(**page_common_vars(player), role_label=player.role_name.title(),
                    player_profile=profile_for(player), show_profile=treatment_picture(player))


class InstructionsIntro(Page):
    form_model = "player"
    form_fields = ["skip_instructions"]

    @staticmethod
    def is_displayed(player: Player):
        return instruction_page_is_displayed(player)

    @staticmethod
    def vars_for_template(player: Player):
        return instruction_page_vars(player)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        instruction_page_before_next(player, timeout_happened)


class Instructions(Page):
    form_model = "player"
    form_fields = ["skip_instructions"]

    @staticmethod
    def is_displayed(player: Player):
        return instruction_page_is_displayed(player)

    @staticmethod
    def vars_for_template(player: Player):
        return instruction_page_vars(player)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        instruction_page_before_next(player, timeout_happened)


class Instructions2(Page):
    form_model = "player"
    form_fields = ["skip_instructions"]

    @staticmethod
    def is_displayed(player: Player):
        return instruction_page_is_displayed(player)

    @staticmethod
    def vars_for_template(player: Player):
        return instruction_page_vars(player)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        instruction_page_before_next(player, timeout_happened)


class Instructions3(Page):
    form_model = "player"
    form_fields = ["skip_instructions"]

    @staticmethod
    def is_displayed(player: Player):
        return instruction_page_is_displayed(player)

    @staticmethod
    def vars_for_template(player: Player):
        return instruction_page_vars(player)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        instruction_page_before_next(player, timeout_happened)


class Instructions4(Page):
    form_model = "player"
    form_fields = ["skip_instructions"]

    @staticmethod
    def is_displayed(player: Player):
        return instruction_page_is_displayed(player)

    @staticmethod
    def vars_for_template(player: Player):
        return instruction_page_vars(player)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        instruction_page_before_next(player, timeout_happened)


class Instructions5(Page):
    form_model = "player"
    form_fields = ["skip_instructions"]

    @staticmethod
    def is_displayed(player: Player):
        return instruction_page_is_displayed(player)

    @staticmethod
    def vars_for_template(player: Player):
        return instruction_page_vars(player)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        instruction_page_before_next(player, timeout_happened)


class InstructionQuiz(Page):
    form_model = "player"
    form_fields = INSTRUCTION_QUIZ_FIELDS

    @staticmethod
    def is_displayed(player: Player):
        return (
            player.round_number == 1
            and is_real_experiment_session(player.session)
            and not instruction_quiz_failed(player)
            and not instructions_skipped(player)
        )

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            **page_common_vars(player),
            attempts_remaining=C.INSTRUCTION_QUIZ_MAX_ATTEMPTS - instruction_quiz_wrong_attempts(player),
            quiz_fields=randomized_instruction_quiz_fields(),
            randomize_quiz_answers=is_real_experiment_session(player.session),
        )

    @staticmethod
    def error_message(player: Player, values):
        wrong = [field for field, answer in INSTRUCTION_QUIZ_CORRECT_ANSWERS.items() if values[field] != answer]
        if not wrong:
            return
        attempt = instruction_quiz_wrong_attempts(player) + 1
        player.participant.vars["instruction_quiz_wrong_attempts"] = attempt
        if attempt >= C.INSTRUCTION_QUIZ_MAX_ATTEMPTS:
            player.participant.vars["instruction_quiz_failed"] = True
            return
        message = "This answer is incorrect. Please try again."
        if attempt >= 2:
            message += " You can review the instructions using the button in the upper-right corner."
        return {field: message for field in wrong}


class InstructionQuizFailed(Page):
    @staticmethod
    def is_displayed(player: Player):
        return (
            player.round_number == 1
            and is_real_experiment_session(player.session)
            and instruction_quiz_failed(player)
        )

    @staticmethod
    def vars_for_template(player: Player):
        return page_common_vars(player)


class ProposerDecision(Page):
    form_model = "group"
    form_fields = ["offer"]

    @staticmethod
    def is_displayed(player: Player):
        return player.is_active_round and player.role_name == "proposer"

    @staticmethod
    def vars_for_template(player: Player):
        partner = get_partner(player)
        return dict(**page_common_vars(player), partner=partner, player_profile=profile_for(player),
                    partner_profile=profile_for(partner), show_profile=treatment_picture(player),
                    show_written_description=treatment_written_description(player),
                    partner_written_description=written_description_for(player, partner),
                    is_practice=player.is_practice_round, endowment=C.ENDOWMENT)


class WaitForProposer(WaitPage):
    title_text = "Waiting for proposer"
    body_text = "Please wait for the proposer to make a decision."

    @staticmethod
    def is_displayed(player: Player):
        return player.is_active_round


class ResponderDecision(Page):
    form_model = "group"
    form_fields = ["intended_return"]

    @staticmethod
    def is_displayed(player: Player):
        return player.is_active_round and player.role_name == "responder"

    @staticmethod
    def vars_for_template(player: Player):
        partner = get_partner(player)
        return dict(**page_common_vars(player), partner=partner, player_profile=profile_for(player),
                    partner_profile=profile_for(partner), show_profile=treatment_picture(player),
                    show_written_description=treatment_written_description(player),
                    partner_written_description=written_description_for(player, partner),
                    is_practice=player.is_practice_round, offer=player.group.offer,
                    multiplied_amount=display_number(player.group.multiplied_amount()),
                    realized_multiplier=display_number(player.group.realized_multiplier))

    @staticmethod
    def error_message(player: Player, values):
        return intended_return_error_message(player.group, values["intended_return"])


class WaitForResponder(WaitPage):
    title_text = "Waiting for responder"
    body_text = "Please wait for the responder to make a decision."
    after_all_players_arrive = set_round_outcomes

    @staticmethod
    def is_displayed(player: Player):
        return player.is_active_round


class ProposerReceipt(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.is_active_round and player.role_name == "proposer"

    @staticmethod
    def vars_for_template(player: Player):
        partner = get_partner(player)
        return dict(**page_common_vars(player), partner=partner, partner_profile=profile_for(partner),
                    show_profile=treatment_picture(player),
                    show_written_description=treatment_written_description(player),
                    partner_written_description=written_description_for(player, partner),
                    is_practice=player.is_practice_round,
                    offer=player.group.offer, delivered_return=player.group.delivered_return,
                    proposer_round_points=display_number(proposer_round_points(player.group)))


class ProposerBeliefPost(Page):
    form_model = "player"
    form_fields = ["belief_post_probability_low"]

    @staticmethod
    def is_displayed(player: Player):
        return player.is_active_round and player.role_name == "proposer"

    @staticmethod
    def vars_for_template(player: Player):
        return dict(**page_common_vars(player), is_practice=player.is_practice_round,
                    offer=player.group.offer, delivered_return=player.group.delivered_return,
                    initial_probability=round((1 - get_high_multiplier_probability(player.session)) * 100),
                    **round_summary_vars(player))

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        record_belief(player)


class WaitForPostBelief(WaitPage):
    title_text = "Waiting"
    body_text = "Please wait while the proposer completes the second belief report."

    @staticmethod
    def is_displayed(player: Player):
        return player.is_active_round


class ResponderReceipt(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.is_active_round and player.role_name == "responder"

    @staticmethod
    def vars_for_template(player: Player):
        partner = get_partner(player)
        return dict(**page_common_vars(player), partner=partner, partner_profile=profile_for(partner),
                    show_profile=treatment_picture(player),
                    show_written_description=treatment_written_description(player),
                    partner_written_description=written_description_for(player, partner),
                    is_practice=player.is_practice_round,
                    offer=player.group.offer, multiplied_amount=display_number(player.group.multiplied_amount()),
                    intended_return=player.group.intended_return,
                    responder_round_points=display_number(responder_round_points(player.group)))


class RoundComplete(WaitPage):
    title_text = "Waiting for the round to finish"
    body_text = "Please wait for your partner."

    @staticmethod
    def is_displayed(player: Player):
        return player.is_active_round


class Part1Instructions(Page):
    template_name = "trust_game/QuestionnaireInstructions.html"

    @staticmethod
    def is_displayed(player: Player):
        return show_part1_self_survey(player)

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            **page_common_vars(player),
            is_part1_self_survey=True,
            is_part3_partner_survey=False,
        )


class Part3Instructions(Page):
    template_name = "trust_game/QuestionnaireInstructions.html"

    @staticmethod
    def is_displayed(player: Player):
        return show_part3_partner_survey(player)

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            **page_common_vars(player),
            is_part1_self_survey=False,
            is_part3_partner_survey=True,
        )


class SelfIdentification(Page):
    form_model = "player"
    form_fields = ["age", "age_prefer_not_to_say", "ethnicity", "race", "gender", "sexuality"]

    @staticmethod
    def is_displayed(player: Player):
        return show_part1_self_survey(player)

    @staticmethod
    def vars_for_template(player: Player):
        return page_common_vars(player)

    @staticmethod
    def error_message(player: Player, values):
        required_fields = ["ethnicity", "race", "gender", "sexuality"]
        missing = {
            field: "Please answer this question before continuing."
            for field in required_fields
            if values[field] in {None, ""}
        }
        if not values["age_prefer_not_to_say"] and values["age"] is None:
            missing["age"] = "Please enter your age or select prefer not to say."
        if missing:
            return missing
        if not values["age_prefer_not_to_say"] and values["age"] is not None and values["age"] < C.MIN_AGE:
            return dict(age="You must be 18 or older")

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if player.age_prefer_not_to_say or player.field_maybe_none("age") is None:
            player.age = None
            player.age_prefer_not_to_say = True


class WaitForSelfIdentification(WaitPage):
    wait_for_all_groups = True
    title_text = "Waiting for Part 1 to finish"
    body_text = "Please wait for the other participants to finish Part 1."

    @staticmethod
    def is_displayed(player: Player):
        return show_part1_self_survey(player)


class PartnerIdentification1(Page):
    template_name = "trust_game/PartnerIdentification.html"
    form_model = "player"
    form_fields = partner_survey_form_fields(1)

    @staticmethod
    def is_displayed(player: Player):
        return show_part3_partner_survey(player) and 1 <= get_active_periods(player.session)

    @staticmethod
    def error_message(player: Player, values):
        return partner_survey_error_message(values, 1)

    @staticmethod
    def vars_for_template(player: Player):
        return partner_survey_vars(player, 1)

class PartnerIdentification2(Page):
    template_name = "trust_game/PartnerIdentification.html"
    form_model = "player"
    form_fields = partner_survey_form_fields(2)

    @staticmethod
    def is_displayed(player: Player):
        return show_part3_partner_survey(player) and 2 <= get_active_periods(player.session)

    @staticmethod
    def error_message(player: Player, values):
        return partner_survey_error_message(values, 2)

    @staticmethod
    def vars_for_template(player: Player):
        return partner_survey_vars(player, 2)

class PartnerIdentification3(Page):
    template_name = "trust_game/PartnerIdentification.html"
    form_model = "player"
    form_fields = partner_survey_form_fields(3)

    @staticmethod
    def is_displayed(player: Player):
        return show_part3_partner_survey(player) and 3 <= get_active_periods(player.session)

    @staticmethod
    def error_message(player: Player, values):
        return partner_survey_error_message(values, 3)

    @staticmethod
    def vars_for_template(player: Player):
        return partner_survey_vars(player, 3)

class PartnerIdentification4(Page):
    template_name = "trust_game/PartnerIdentification.html"
    form_model = "player"
    form_fields = partner_survey_form_fields(4)

    @staticmethod
    def is_displayed(player: Player):
        return show_part3_partner_survey(player) and 4 <= get_active_periods(player.session)

    @staticmethod
    def error_message(player: Player, values):
        return partner_survey_error_message(values, 4)

    @staticmethod
    def vars_for_template(player: Player):
        return partner_survey_vars(player, 4)

class PartnerIdentification5(Page):
    template_name = "trust_game/PartnerIdentification.html"
    form_model = "player"
    form_fields = partner_survey_form_fields(5)

    @staticmethod
    def is_displayed(player: Player):
        return show_part3_partner_survey(player) and 5 <= get_active_periods(player.session)

    @staticmethod
    def error_message(player: Player, values):
        return partner_survey_error_message(values, 5)

    @staticmethod
    def vars_for_template(player: Player):
        return partner_survey_vars(player, 5)

class PartnerIdentification6(Page):
    template_name = "trust_game/PartnerIdentification.html"
    form_model = "player"
    form_fields = partner_survey_form_fields(6)

    @staticmethod
    def is_displayed(player: Player):
        return show_part3_partner_survey(player) and 6 <= get_active_periods(player.session)

    @staticmethod
    def error_message(player: Player, values):
        return partner_survey_error_message(values, 6)

    @staticmethod
    def vars_for_template(player: Player):
        return partner_survey_vars(player, 6)

class PartnerIdentification7(Page):
    template_name = "trust_game/PartnerIdentification.html"
    form_model = "player"
    form_fields = partner_survey_form_fields(7)

    @staticmethod
    def is_displayed(player: Player):
        return show_part3_partner_survey(player) and 7 <= get_active_periods(player.session)

    @staticmethod
    def error_message(player: Player, values):
        return partner_survey_error_message(values, 7)

    @staticmethod
    def vars_for_template(player: Player):
        return partner_survey_vars(player, 7)

class PartnerIdentification8(Page):
    template_name = "trust_game/PartnerIdentification.html"
    form_model = "player"
    form_fields = partner_survey_form_fields(8)

    @staticmethod
    def is_displayed(player: Player):
        return show_part3_partner_survey(player) and 8 <= get_active_periods(player.session)

    @staticmethod
    def error_message(player: Player, values):
        return partner_survey_error_message(values, 8)

    @staticmethod
    def vars_for_template(player: Player):
        return partner_survey_vars(player, 8)

class PartnerIdentification9(Page):
    template_name = "trust_game/PartnerIdentification.html"
    form_model = "player"
    form_fields = partner_survey_form_fields(9)

    @staticmethod
    def is_displayed(player: Player):
        return show_part3_partner_survey(player) and 9 <= get_active_periods(player.session)

    @staticmethod
    def error_message(player: Player, values):
        return partner_survey_error_message(values, 9)

    @staticmethod
    def vars_for_template(player: Player):
        return partner_survey_vars(player, 9)

class PartnerIdentification10(Page):
    template_name = "trust_game/PartnerIdentification.html"
    form_model = "player"
    form_fields = partner_survey_form_fields(10)

    @staticmethod
    def is_displayed(player: Player):
        return show_part3_partner_survey(player) and 10 <= get_active_periods(player.session)

    @staticmethod
    def error_message(player: Player, values):
        return partner_survey_error_message(values, 10)

    @staticmethod
    def vars_for_template(player: Player):
        return partner_survey_vars(player, 10)


class PaymentSummary(Page):
    @staticmethod
    def is_displayed(player: Player):
        return show_end_demographic_survey(player)

    @staticmethod
    def vars_for_template(player: Player):
        return payment_summary_vars(player)


page_sequence = [
    InstructionsIntro,
    Part1Instructions, SelfIdentification, WaitForSelfIdentification,
    Instructions, Instructions2, Instructions3, Instructions4, Instructions5,
    InstructionQuiz, InstructionQuizFailed, RoleNotice,
    ProposerDecision, WaitForProposer, ResponderDecision, WaitForResponder,
    ProposerReceipt, ProposerBeliefPost,
    WaitForPostBelief, ResponderReceipt, RoundComplete,
    Part3Instructions,
    PartnerIdentification1,
    PartnerIdentification2,
    PartnerIdentification3,
    PartnerIdentification4,
    PartnerIdentification5,
    PartnerIdentification6,
    PartnerIdentification7,
    PartnerIdentification8,
    PartnerIdentification9,
    PartnerIdentification10,
    PaymentSummary,
]


SELF_DEMOGRAPHIC_EXPORT_FIELDS = ["age", "age_prefer_not_to_say", "ethnicity", "race", "gender", "sexuality"]
PARTNER_SURVEY_EXPORT_SUFFIXES = [
    "age_guess", "age_confidence", "ethnicity_guess", "ethnicity_confidence",
    "race_guess", "race_confidence", "gender_guess", "gender_confidence",
    "sexuality_guess", "sexuality_confidence", "existing_relationship", "relationship_nature",
]


def nullable_field(record, field_name):
    return record.field_maybe_none(field_name)


def final_active_player(player):
    return player.in_round(last_active_round(player.session))


def self_demographic_headers(role_prefix):
    return [f"{role_prefix}_{field}" for field in SELF_DEMOGRAPHIC_EXPORT_FIELDS]


def self_demographic_values(player):
    part1_player = self_demographic_player(player)
    return [nullable_field(part1_player, field) for field in SELF_DEMOGRAPHIC_EXPORT_FIELDS]


def partner_survey_headers(role_prefix):
    headers = []
    for slot in range(1, C.MAX_PERIODS + 1):
        headers.append(f"{role_prefix}_matched_partner_{slot}_name")
        headers.extend(f"{role_prefix}_matched_partner_{slot}_{suffix}" for suffix in PARTNER_SURVEY_EXPORT_SUFFIXES)
    return headers


def partner_survey_values(player):
    final_player = final_active_player(player)
    values = []
    active_periods = get_active_periods(player.session)
    for slot in range(1, C.MAX_PERIODS + 1):
        if slot <= active_periods:
            partner = matched_partner_for_period(final_player, slot)
            values.append(profile_for(partner)["title"])
            values.extend(nullable_field(final_player, f"partner_{slot}_{suffix}") for suffix in PARTNER_SURVEY_EXPORT_SUFFIXES)
        else:
            values.extend([None] * (1 + len(PARTNER_SURVEY_EXPORT_SUFFIXES)))
    return values


def custom_export(players):
    base_headers = [
        "session_code", "session_config", "active_periods", "unique_cross_role_pairs",
        "is_real_experiment", "picture_condition", "written_description_condition",
        "treatment_code", "treatment_label",
        "low_multiplier_probability",
        "high_multiplier_probability", "low_multiplier", "high_multiplier",
        "realized_multiplier", "high_multiplier_applied", "paid_period",
        "period", "round_in_period", "otree_round",
        "is_practice_round", "is_active_round", "proposer_code", "proposer_name",
        "responder_code", "responder_name", "offer", "multiplied_amount", "intended_return",
        "delivered_return", "proposer_round_points", "responder_round_points",
        "trust_point_dollar_value", "proposer_trust_payment", "responder_trust_payment",
        "belief_post_probability_low", "belief_selected_for_payment", "belief_winning_chance",
        "belief_bonus_draw", "belief_bonus_awarded", "belief_bonus",
        "proposer_total_round_payoff", "responder_total_round_payoff",
    ]
    yield (base_headers + self_demographic_headers("proposer") + partner_survey_headers("proposer")
           + self_demographic_headers("responder") + partner_survey_headers("responder"))

    for player in players:
        if nullable_field(player, "role_name") != "proposer" or not player.is_active_round:
            continue
        group = player.group
        proposer = get_proposer(group)
        responder = get_responder(group)
        offer = nullable_field(group, "offer")
        multiplied_amount = offer * group.realized_multiplier if offer is not None else None
        base_values = [
            player.session.code, player.session.config["name"], get_active_periods(player.session),
            player.session.vars.get("unique_cross_role_pairs"), is_real_experiment_session(player.session),
            group.treatment_picture, group.treatment_written_description,
            group.treatment_code, group.treatment_label,
            get_low_multiplier_probability(player.session),
            group.high_multiplier_probability, group.low_multiplier, group.high_multiplier,
            group.realized_multiplier, group.high_multiplier_applied, get_paid_period(player.session),
            player.period_number, player.round_in_period,
            player.round_number, player.is_practice_round, player.is_active_round,
            proposer.participant.code, profile_for(proposer)["title"], responder.participant.code,
            profile_for(responder)["title"], offer, multiplied_amount,
            nullable_field(group, "intended_return"), nullable_field(group, "delivered_return"),
            proposer.round_points, responder.round_points, get_trust_point_value(player.session),
            proposer.trust_game_payment, responder.trust_game_payment,
            nullable_field(proposer, "belief_post_probability_low"), proposer.belief_selected_for_payment,
            nullable_field(proposer, "belief_winning_chance"), nullable_field(proposer, "belief_bonus_draw"),
            proposer.belief_bonus_awarded,
            proposer.belief_bonus, proposer.payoff, responder.payoff,
        ]
        yield (base_values + self_demographic_values(proposer) + partner_survey_values(proposer)
               + self_demographic_values(responder) + partner_survey_values(responder))
