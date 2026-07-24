import os
import random
from urllib.parse import quote

from otree.api import *


doc = """
Two-by-two trust game with fixed proposer/responder roles, rotating partners,
two rounds per period, optional picture/profile information, and either a fixed
3x multiplier or a hidden 3x/6x multiplier draw.
"""


class C(BaseConstants):
    NAME_IN_URL = "trust_game"
    PLAYERS_PER_GROUP = 2
    PRACTICE_ROUNDS = 2
    ROUNDS_PER_PERIOD = 2
    PERIODS = 5
    NUM_ROUNDS = PRACTICE_ROUNDS + (PERIODS * ROUNDS_PER_PERIOD)
    ENDOWMENT = cu(20)
    LOW_MULTIPLIER = 3
    HIGH_MULTIPLIER = 6
    MULTIPLIER = LOW_MULTIPLIER
    DEFAULT_CHANCE_OF_3 = 0.50
    DEFAULT_LARGE_MULTIPLIER = HIGH_MULTIPLIER
    INSTRUCTION_QUIZ_MAX_ATTEMPTS = 3
    MIN_AGE = 18
    MAX_AGE = 100
    GENDER_CHOICES = [
        ["Female", "Female"],
        ["Male", "Male"],
        ["Non-Binary", "Non-Binary"],
        ["Other", "Other"],
        ["Prefer not to say", "Prefer not to say"],
    ]
    GENDER_GUESS_CHOICES = [
        ["Female", "Female"],
        ["Male", "Male"],
        ["Non-Binary", "Non-Binary"],
        ["Other", "Other"],
    ]
    RACE_CHOICES = [
        ["Caucasian (white)", "Caucasian (white)"],
        ["African American", "African American"],
        ["Latino", "Latino"],
        ["Asian or Pacific Islander", "Asian or Pacific Islander"],
        ["Native American", "Native American"],
        ["Other", "Other"],
        ["Prefer not to say", "Prefer not to say"],
    ]
    RACE_GUESS_CHOICES = [
        ["Caucasian (white)", "Caucasian (white)"],
        ["African American", "African American"],
        ["Latino", "Latino"],
        ["Asian or Pacific Islander", "Asian or Pacific Islander"],
        ["Native American", "Native American"],
        ["Other", "Other"],
    ]
    ETHNICITY_CHOICES = [
        ["Yes", "Yes"],
        ["No", "No"],
        ["Prefer not to say", "Prefer not to say"],
    ]
    ETHNICITY_GUESS_CHOICES = [
        ["Yes", "Yes"],
        ["No", "No"],
    ]
    SEXUALITY_CHOICES = [
        ["Straight", "Straight"],
        ["Gay", "Gay"],
        ["Bi-Sexual", "Bi-Sexual"],
        ["Pansexual", "Pansexual"],
        ["Asexual", "Asexual"],
        ["Other", "Other"],
        ["Prefer not to say", "Prefer not to say"],
    ]
    SEXUALITY_GUESS_CHOICES = [
        ["Straight", "Straight"],
        ["Gay", "Gay"],
        ["Bi-Sexual", "Bi-Sexual"],
        ["Pansexual", "Pansexual"],
        ["Asexual", "Asexual"],
        ["Other", "Other"],
    ]
    CONFIDENCE_CHOICES = [
        ["Sure", "Sure"],
        ["Unsure", "Unsure"],
        ["Neither Sure or Unsure", "Neither Sure or Unsure"],
    ]
    CONFIDENCE_LABEL = "Confidence in Guess"
    RELATIONSHIP_CHOICES = [
        ["No", "No"],
        ["Yes", "Yes"],
        ["Prefer not to say", "Prefer not to say"],
    ]
    TREATMENTS = [
        dict(
            code="no_picture_fixed_multiplier",
            picture_label="No picture",
            picture=False,
            random_multiplier=False,
        ),
        dict(
            code="no_picture_random_multiplier",
            picture_label="No picture",
            picture=False,
            random_multiplier=True,
        ),
        dict(
            code="picture_fixed_multiplier",
            picture_label="Picture",
            picture=True,
            random_multiplier=False,
        ),
        dict(
            code="picture_random_multiplier",
            picture_label="Picture",
            picture=True,
            random_multiplier=True,
        ),
    ]


class Subsession(BaseSubsession):
    def vars_for_admin_report(self):
        rows = []
        for index, treatment in enumerate(get_period_treatments(self.session), start=1):
            rows.append(
                dict(
                    period=index,
                    label=treatment_label(self.session, treatment),
                    code=treatment["code"],
                    picture=treatment["picture"],
                    picture_text="Shown" if treatment["picture"] else "Not shown",
                    random_multiplier=treatment["random_multiplier"],
                    multiplier_text=(
                        f"{C.LOW_MULTIPLIER} or {get_large_multiplier(self.session)}"
                        if treatment["random_multiplier"]
                        else str(C.LOW_MULTIPLIER)
                    ),
                    realized_multiplier=get_period_realized_multiplier(
                        self.session,
                        index - 1,
                    ),
                )
            )
        return dict(
            period_treatments=rows,
            chance_of_3=get_chance_of_3(self.session),
            chance_of_3_percent=round(get_chance_of_3(self.session) * 100),
            large_multiplier_probability=get_large_multiplier_probability(self.session),
            large_multiplier_probability_percent=round(
                get_large_multiplier_probability(self.session) * 100
            ),
            low_multiplier=C.LOW_MULTIPLIER,
            large_multiplier=get_large_multiplier(self.session),
        )


class Group(BaseGroup):
    treatment_code = models.StringField()
    treatment_label = models.StringField()
    treatment_picture = models.BooleanField()
    treatment_error = models.BooleanField()
    error_probability = models.FloatField()
    error_return_multiplier = models.FloatField()
    realized_multiplier = models.FloatField(initial=C.LOW_MULTIPLIER)
    high_multiplier_applied = models.BooleanField(initial=False)

    offer = models.CurrencyField(
        min=0,
        max=C.ENDOWMENT,
        label="How many of your 20 points do you send to the responder?",
    )
    intended_return = models.CurrencyField(
        min=0,
        label="How many points do you send back to the proposer?",
    )
    error_applied = models.BooleanField(initial=False)
    delivered_return = models.CurrencyField(initial=0)

    def multiplied_amount(self):
        multiplier = self.field_maybe_none("realized_multiplier")
        if multiplier is None:
            multiplier = C.LOW_MULTIPLIER
        return self.offer * multiplier

    def tripled_amount(self):
        return self.multiplied_amount()


class Player(BasePlayer):
    role_name = models.StringField()
    role_number = models.IntegerField()
    is_practice_round = models.BooleanField(initial=False)
    period_number = models.IntegerField()
    round_in_period = models.IntegerField()
    skip_instructions = models.StringField(blank=True, initial="")
    instruction_quiz_1 = models.StringField(
        choices=[
            ["same", "Your role stays the same for the entire session."],
            ["changes", "Your role changes after each period."],
            ["chosen", "You choose your role before each round."],
        ],
        label="What happens to your role during the session?",
        widget=widgets.RadioSelect,
    )
    instruction_quiz_2 = models.StringField(
        choices=[
            ["included", "Practice rounds can be selected for payoff."],
            ["learning", "Practice rounds are only for learning and cannot be selected for payoff."],
            ["none", "There are no practice rounds."],
        ],
        label="How are practice rounds treated?",
        widget=widgets.RadioSelect,
    )
    instruction_quiz_3 = models.StringField(
        choices=[
            ["zero_to_twenty", "The proposer chooses a whole number from 0 to 20."],
            ["all_or_nothing", "The proposer must send either 0 points or all 20 points."],
            ["responder_decides", "The responder chooses how many of the proposer's 20 points are sent."],
        ],
        label="In each round, what can the proposer send to the responder?",
        widget=widgets.RadioSelect,
    )
    instruction_quiz_4 = models.StringField(
        choices=[
            ["sent_available", "How many points were sent and how many points are available after multiplication."],
            ["only_sent", "Only how many points were sent."],
            ["nothing", "Neither the points sent nor the points available."],
        ],
        label="What information does the responder see before deciding how much to send back?",
        widget=widgets.RadioSelect,
    )
    instruction_quiz_5 = models.StringField(
        choices=[
            [
                "correct",
                (
                    r"\(\text{proposer earnings} = 20 - "
                    r"\text{points sent by proposer} + "
                    r"\text{points returned by responder}\); "
                    r"\(\text{responder earnings} = "
                    r"\text{points available to responder} - "
                    r"\text{points returned by responder}\)."
                ),
            ],
            [
                "swapped",
                (
                    r"\(\text{proposer earnings} = "
                    r"\text{points available to responder} - "
                    r"\text{points returned by responder}\); "
                    r"\(\text{responder earnings} = 20 - "
                    r"\text{points sent by proposer} + "
                    r"\text{points returned by responder}\)."
                ),
            ],
            [
                "same",
                (
                    r"\(\text{both players' earnings} = "
                    r"\text{points available to responder} - "
                    r"\text{points returned by responder}\)."
                ),
            ],
        ],
        label="How are round points calculated?",
        widget=widgets.RadioSelect,
    )
    gender = models.StringField(
        choices=C.GENDER_CHOICES,
        label="What is your gender?",
        blank=True,
    )
    race = models.StringField(
        choices=C.RACE_CHOICES,
        label="What is your race?",
        blank=True,
    )
    ethnicity = models.StringField(
        choices=C.ETHNICITY_CHOICES,
        label="Are you Hispanic or Latino?",
        blank=True,
    )
    age = models.IntegerField(
        label="What is your age?",
        min=0,
        max=C.MAX_AGE,
        blank=True,
    )
    age_prefer_not_to_say = models.BooleanField(
        label="I prefer not to say",
        blank=True,
        initial=False,
    )
    sexuality = models.StringField(
        choices=C.SEXUALITY_CHOICES,
        label="What is your sexuality?",
        blank=True,
    )
    partner_gender_guess = models.StringField(
        choices=C.GENDER_GUESS_CHOICES,
        label="Guess what gender this person identifies as.",
    )
    partner_gender_confidence = models.StringField(
        choices=C.CONFIDENCE_CHOICES,
        label=C.CONFIDENCE_LABEL,
    )
    partner_race_guess = models.StringField(
        choices=C.RACE_GUESS_CHOICES,
        label="Guess what race this person identifies as.",
    )
    partner_race_confidence = models.StringField(
        choices=C.CONFIDENCE_CHOICES,
        label=C.CONFIDENCE_LABEL,
    )
    partner_ethnicity_guess = models.StringField(
        choices=C.ETHNICITY_GUESS_CHOICES,
        label="Guess if this person identifies as Hispanic or Latino.",
    )
    partner_ethnicity_confidence = models.StringField(
        choices=C.CONFIDENCE_CHOICES,
        label=C.CONFIDENCE_LABEL,
    )
    partner_age_guess = models.IntegerField(
        label="Guess this person's age.",
        min=0,
        max=C.MAX_AGE,
    )
    partner_age_confidence = models.StringField(
        choices=C.CONFIDENCE_CHOICES,
        label=C.CONFIDENCE_LABEL,
    )
    partner_sexuality_guess = models.StringField(
        choices=C.SEXUALITY_GUESS_CHOICES,
        label="Guess what sexuality this person identifies as.",
    )
    partner_sexuality_confidence = models.StringField(
        choices=C.CONFIDENCE_CHOICES,
        label=C.CONFIDENCE_LABEL,
    )
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
    proposer_belief_multiplier = models.IntegerField(
        label="What do you think the multiplier was?",
        min=0,
    )
    proposer_belief_low_balls = models.IntegerField(min=0, max=10, initial=5)
    proposer_belief_large_balls = models.IntegerField(min=0, max=10, initial=5)
    multiplier_belief_bonus = models.CurrencyField(initial=0)


def make_period_treatments():
    return [random.choice(C.TREATMENTS).copy() for _ in range(C.PERIODS)]


def get_period_treatments(session):
    return session.vars.get("period_treatments", [])


def get_period_treatment(session, period_index):
    return get_period_treatments(session)[period_index]


def treatment_label(session, treatment):
    if treatment["random_multiplier"]:
        multiplier_label = f"Multiplier {C.LOW_MULTIPLIER} or {get_large_multiplier(session)}"
    else:
        multiplier_label = f"Multiplier {C.LOW_MULTIPLIER}"
    return f'{treatment["picture_label"]} / {multiplier_label}'


def get_treatment_randomization_level(session):
    return session.config.get("treatment_randomization_level", "period")


def practice_treatment():
    return dict(
        code="practice",
        picture_label="Picture",
        picture=True,
        random_multiplier=True,
    )


def is_practice_round(record):
    return record.round_number <= C.PRACTICE_ROUNDS


def real_round_number(record):
    return record.round_number - C.PRACTICE_ROUNDS


def get_chance_of_3(session):
    if "chance_of_3" in session.config:
        chance = float(session.config["chance_of_3"])
    else:
        large_probability = float(session.config.get("high_multiplier_probability", 0.50))
        chance = 1 - large_probability

    if chance not in {0.25, 0.50, 0.75}:
        raise ValueError("Chance of 3 must be 25%, 50%, or 75%.")
    return chance


def get_large_multiplier(session):
    value = session.config.get("large_multiplier", C.DEFAULT_LARGE_MULTIPLIER)
    large_multiplier = int(value)
    if str(value) not in {str(large_multiplier), f"{large_multiplier}.0"}:
        raise ValueError("Large multiplier must be a whole number.")
    if large_multiplier <= C.LOW_MULTIPLIER:
        raise ValueError(
            f"Large multiplier must be greater than {C.LOW_MULTIPLIER}."
        )
    return large_multiplier


def get_large_multiplier_probability(session):
    return 1 - get_chance_of_3(session)


def get_treatment_high_multiplier_probability(session, treatment):
    if not treatment["random_multiplier"]:
        return 0.0
    return get_large_multiplier_probability(session)


def choose_realized_multiplier(session, treatment):
    if not treatment["random_multiplier"]:
        return C.LOW_MULTIPLIER
    if random.random() < get_chance_of_3(session):
        return C.LOW_MULTIPLIER
    return get_large_multiplier(session)


def make_period_realized_multipliers(session, treatments):
    return [choose_realized_multiplier(session, treatment) for treatment in treatments]


def get_period_realized_multipliers(session):
    return session.vars.get("period_realized_multipliers", [])


def get_period_realized_multiplier(session, period_index):
    return get_period_realized_multipliers(session)[period_index]


def get_group_high_multiplier_probability(group: Group):
    value = group.field_maybe_none("error_probability")
    if value is None:
        value = get_large_multiplier_probability(group.session)
        group.error_probability = value
    return float(value)


def get_group_realized_multiplier(group: Group):
    value = group.field_maybe_none("realized_multiplier")
    if value is None:
        value = C.LOW_MULTIPLIER
        group.realized_multiplier = value
    return float(value)


def nullable_field(record, field_name):
    return record.field_maybe_none(field_name)


def seed_random_for_bot_comparison():
    seed = os.environ.get("TRUST_GAME_BOT_RANDOM_SEED")
    if seed:
        random.seed(seed)


def role_counts_for_session(players):
    participant_count = len(players)
    if participant_count < C.PLAYERS_PER_GROUP or participant_count % C.PLAYERS_PER_GROUP:
        raise ValueError(
            "This trust-game schedule requires an even number of participants, "
            "with half assigned as proposers and half assigned as responders."
        )
    proposer_count = participant_count // C.PLAYERS_PER_GROUP
    responder_count = participant_count - proposer_count
    return proposer_count, responder_count


def creating_session(subsession: Subsession):
    players = subsession.get_players()
    proposer_count, responder_count = role_counts_for_session(players)

    if subsession.round_number == 1:
        seed_random_for_bot_comparison()
        period_treatments = make_period_treatments()
        subsession.session.vars["period_treatments"] = period_treatments
        subsession.session.vars["period_realized_multipliers"] = (
            make_period_realized_multipliers(subsession.session, period_treatments)
        )

    practice_round = is_practice_round(subsession)
    if practice_round:
        period_index = 0
        round_in_period = subsession.round_number
        period_treatment = practice_treatment()
    else:
        real_round = real_round_number(subsession)
        period_index = (real_round - 1) // C.ROUNDS_PER_PERIOD
        round_in_period = ((real_round - 1) % C.ROUNDS_PER_PERIOD) + 1
        period_treatment = get_period_treatment(subsession.session, period_index)

    proposers = players[:proposer_count]
    responders = players[proposer_count:]
    group_matrix = []

    for index, proposer in enumerate(proposers):
        responder = responders[(index + period_index) % responder_count]
        group_matrix.append([proposer, responder])

    subsession.set_group_matrix(group_matrix)

    for group in subsession.get_groups():
        treatment = period_treatment
        high_multiplier_probability = get_treatment_high_multiplier_probability(
            subsession.session,
            treatment,
        )
        if practice_round:
            realized_multiplier = choose_realized_multiplier(subsession.session, treatment)
        else:
            realized_multiplier = get_period_realized_multiplier(
                subsession.session,
                period_index,
            )
        group.treatment_code = treatment["code"]
        group.treatment_label = treatment_label(subsession.session, treatment)
        group.treatment_picture = treatment["picture"]
        group.treatment_error = treatment["random_multiplier"]
        group.error_probability = high_multiplier_probability
        group.error_return_multiplier = get_large_multiplier(subsession.session)
        group.realized_multiplier = realized_multiplier
        group.high_multiplier_applied = realized_multiplier == get_large_multiplier(
            subsession.session
        )

    for player in subsession.get_players():
        is_proposer = player.id_in_subsession <= proposer_count
        role_number = player.id_in_subsession if is_proposer else player.id_in_subsession - proposer_count
        role_name = "proposer" if is_proposer else "responder"

        player.role_name = role_name
        player.role_number = role_number
        player.is_practice_round = practice_round
        player.period_number = 0 if practice_round else period_index + 1
        player.round_in_period = round_in_period

        if subsession.round_number == 1:
            participant = player.participant
            participant.role_name = role_name
            participant.role_number = role_number


def get_proposer(group: Group):
    return next(player for player in group.get_players() if player.role_name == "proposer")


def get_responder(group: Group):
    return next(player for player in group.get_players() if player.role_name == "responder")


def get_partner(player: Player):
    if player.role_name == "proposer":
        return get_responder(player.group)
    return get_proposer(player.group)


def profile_for(player: Player):
    title = f"Player {player.id_in_subsession}"
    picture_path = f"trust_game/players/{title}.jpg"
    return dict(
        title=title,
        picture_url=f"/static/{quote(picture_path)}",
    )


def treatment_picture(player: Player):
    return bool(player.group.treatment_picture)


def pair_card_vars(player: Player):
    partner = get_partner(player)
    player_role = player.role_name.title()
    partner_role = partner.role_name.title()
    return dict(
        partner=partner,
        player_profile=profile_for(player),
        partner_profile=profile_for(partner),
        show_profile=treatment_picture(player),
        player_role_label=player_role,
        partner_role_label=partner_role,
        anonymous_partner_label=f"Anonymous {partner.role_name}",
    )


def point_number(value):
    numeric_value = float(value)
    if numeric_value.is_integer():
        return int(numeric_value)
    return numeric_value


def round_summary_vars(player: Player):
    group = player.group
    offer = group.field_maybe_none("offer") or cu(0)
    delivered_return = group.field_maybe_none("delivered_return") or cu(0)
    multiplied_amount = group.multiplied_amount()
    low_available = offer * C.LOW_MULTIPLIER
    large_multiplier = get_large_multiplier(player.session)
    high_available = offer * large_multiplier

    if player.role_name == "proposer":
        received_label = "Points you received back"
        received_amount = delivered_return
        final_payoff = player.field_maybe_none("payoff")
        if final_payoff is None:
            final_payoff = proposer_round_points(group)
    else:
        received_label = "Points available to you after multiplication"
        received_amount = multiplied_amount
        final_payoff = player.field_maybe_none("payoff")
        if final_payoff is None:
            final_payoff = responder_round_points(group)

    return dict(
        summary_offer=offer,
        summary_delivered_return=delivered_return,
        summary_received_label=received_label,
        summary_received_amount=received_amount,
        summary_payoff=final_payoff,
        summary_low_multiplier=C.LOW_MULTIPLIER,
        summary_high_multiplier=large_multiplier,
        summary_low_available=low_available,
        summary_high_available=high_available,
        summary_offer_number=point_number(offer),
        summary_low_available_number=point_number(low_available),
        summary_high_available_number=point_number(high_available),
    )


def show_end_demographic_survey(player: Player):
    return player.round_number == C.NUM_ROUNDS


def real_round_for_period(period_number):
    return C.PRACTICE_ROUNDS + ((period_number - 1) * C.ROUNDS_PER_PERIOD) + 1


def matched_partner_for_period(player: Player, period_number):
    player_in_period = player.in_round(real_round_for_period(period_number))
    return get_partner(player_in_period)


def partner_survey_form_fields(slot):
    prefix = f"partner_{slot}"
    return [
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
        f"{prefix}_relationship_nature",
    ]


def partner_survey_vars(player: Player, slot):
    player_in_period = player.in_round(real_round_for_period(slot))
    partner = get_partner(player_in_period)
    prefix = f"partner_{slot}"
    return dict(
        partner_number=slot,
        player_profile=profile_for(player),
        partner_profile=profile_for(partner),
        show_profile=treatment_picture(player_in_period),
        player_role_label=player_in_period.role_name.title(),
        partner_role_label=partner.role_name.title(),
        anonymous_partner_label=f"Anonymous {partner.role_name}",
        **round_summary_vars(player_in_period),
        age_guess_field=f"{prefix}_age_guess",
        age_confidence_field=f"{prefix}_age_confidence",
        ethnicity_guess_field=f"{prefix}_ethnicity_guess",
        ethnicity_confidence_field=f"{prefix}_ethnicity_confidence",
        race_guess_field=f"{prefix}_race_guess",
        race_confidence_field=f"{prefix}_race_confidence",
        gender_guess_field=f"{prefix}_gender_guess",
        gender_confidence_field=f"{prefix}_gender_confidence",
        sexuality_guess_field=f"{prefix}_sexuality_guess",
        sexuality_confidence_field=f"{prefix}_sexuality_confidence",
        relationship_field=f"{prefix}_existing_relationship",
        relationship_nature_field=f"{prefix}_relationship_nature",
    )


def partner_survey_error_message(values, slot):
    prefix = f"partner_{slot}"
    partner_age_guess = values[f"{prefix}_age_guess"]
    if partner_age_guess is not None and partner_age_guess < C.MIN_AGE:
        return {f"{prefix}_age_guess": "Please guess an age of 18 or older."}

    relationship = values[f"{prefix}_existing_relationship"]
    relationship_nature = values[f"{prefix}_relationship_nature"] or ""
    if relationship == "Yes" and not relationship_nature.strip():
        return {
            f"{prefix}_relationship_nature": "Please describe the nature of the relationship."
        }


def proposer_round_points(group: Group):
    return C.ENDOWMENT - group.offer + group.delivered_return


def responder_round_points(group: Group):
    return group.multiplied_amount() - group.intended_return


def proposer_multiplier_belief_bonus(player: Player):
    realized_multiplier = int(get_group_realized_multiplier(player.group))
    if realized_multiplier == C.LOW_MULTIPLIER:
        return cu(player.proposer_belief_low_balls)
    if realized_multiplier == get_large_multiplier(player.session):
        return cu(player.proposer_belief_large_balls)
    return cu(0)


def implied_multiplier_belief(player: Player):
    low_balls = player.proposer_belief_low_balls
    large_balls = player.proposer_belief_large_balls
    if low_balls > large_balls:
        return C.LOW_MULTIPLIER
    if large_balls > low_balls:
        return get_large_multiplier(player.session)
    return 0


def set_payoffs(group: Group):
    proposer = get_proposer(group)
    responder = get_responder(group)
    intended_return = group.intended_return or cu(0)
    group.error_applied = False
    group.delivered_return = intended_return
    if is_practice_round(group):
        proposer.payoff = cu(0)
        responder.payoff = cu(0)
    else:
        proposer.payoff = proposer_round_points(group)
        responder.payoff = responder_round_points(group)


def is_whole_point_amount(value):
    return float(value) == int(float(value))


def offer_error_message(group: Group, value):
    if not is_whole_point_amount(value):
        return "Please enter a whole-point amount."


def intended_return_max(group: Group):
    return group.multiplied_amount()


def intended_return_error_message(group: Group, value):
    if not is_whole_point_amount(value):
        return "Please enter a whole-point amount."

    max_return = intended_return_max(group)
    if value > max_return:
        return f"You cannot send back more than {max_return}."


INSTRUCTION_QUIZ_FIELDS = [
    "instruction_quiz_1",
    "instruction_quiz_2",
    "instruction_quiz_3",
    "instruction_quiz_4",
    "instruction_quiz_5",
]

INSTRUCTION_QUIZ_CORRECT_ANSWERS = dict(
    instruction_quiz_1="same",
    instruction_quiz_2="learning",
    instruction_quiz_3="zero_to_twenty",
    instruction_quiz_4="sent_available",
    instruction_quiz_5="correct",
)


def instruction_quiz_failed(player: Player):
    return bool(player.participant.vars.get("instruction_quiz_failed", False))


def instruction_quiz_wrong_attempts(player: Player):
    return int(player.participant.vars.get("instruction_quiz_wrong_attempts", 0))


def instruction_quiz_attempt_message(attempt_number):
    message = "This answer is incorrect. Please try again."
    if attempt_number >= 2:
        message += (
            " Remember you can consult the instructions by clicking the button "
            "in the upper right-hand corner labeled Instructions."
        )
    return message


def is_real_experiment_session(session):
    return bool(session.config.get("is_real_experiment", True))


def instructions_skipped(player: Player):
    return bool(player.participant.vars.get("skip_instructions_and_quiz", False))


def instruction_page_is_displayed(player: Player):
    return player.round_number == 1 and not instructions_skipped(player)


def instruction_page_vars(player: Player):
    return dict(
        show_testing_skip=not is_real_experiment_session(player.session),
        low_multiplier=C.LOW_MULTIPLIER,
        large_multiplier=get_large_multiplier(player.session),
    )


def instruction_page_before_next(player: Player, timeout_happened):
    if (
        not is_real_experiment_session(player.session)
        and player.field_maybe_none("skip_instructions") == "1"
    ):
        player.participant.vars["skip_instructions_and_quiz"] = True


def randomized_instruction_quiz_fields():
    fields = INSTRUCTION_QUIZ_FIELDS.copy()
    random.shuffle(fields)
    return fields


class RoleNotice(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            pair_card_vars(player),
            role_label=player.role_name.title(),
        )

    @staticmethod
    def is_displayed(player: Player):
        return player.round_in_period == 1


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


class Instructions6(Page):
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
            attempts_remaining=(
                C.INSTRUCTION_QUIZ_MAX_ATTEMPTS
                - instruction_quiz_wrong_attempts(player)
            ),
            quiz_fields=randomized_instruction_quiz_fields(),
            randomize_quiz_answers=is_real_experiment_session(player.session),
        )

    @staticmethod
    def error_message(player: Player, values):
        wrong_fields = [
            field
            for field, correct_answer in INSTRUCTION_QUIZ_CORRECT_ANSWERS.items()
            if values[field] != correct_answer
        ]
        if not wrong_fields:
            return

        attempt_number = instruction_quiz_wrong_attempts(player) + 1
        player.participant.vars["instruction_quiz_wrong_attempts"] = attempt_number

        if attempt_number >= C.INSTRUCTION_QUIZ_MAX_ATTEMPTS:
            player.participant.vars["instruction_quiz_failed"] = True
            return

        message = instruction_quiz_attempt_message(attempt_number)
        return {field: message for field in wrong_fields}


class InstructionQuizFailed(Page):
    @staticmethod
    def is_displayed(player: Player):
        return (
            player.round_number == 1
            and is_real_experiment_session(player.session)
            and instruction_quiz_failed(player)
        )


class ProposerDecision(Page):
    form_model = "group"
    form_fields = ["offer"]

    @staticmethod
    def is_displayed(player: Player):
        return player.role_name == "proposer"

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            pair_card_vars(player),
            is_practice=player.is_practice_round,
            endowment=C.ENDOWMENT,
            low_multiplier=C.LOW_MULTIPLIER,
            high_multiplier=get_large_multiplier(player.session),
            high_multiplier_probability=get_group_high_multiplier_probability(
                player.group
            ),
            high_multiplier_probability_percent=round(
                get_group_high_multiplier_probability(player.group) * 100
            ),
        )


class WaitForProposer(WaitPage):
    title_text = "Waiting for proposer"
    body_text = "Please wait for the proposer to make a decision."


class ResponderDecision(Page):
    form_model = "group"
    form_fields = ["intended_return"]

    @staticmethod
    def is_displayed(player: Player):
        return player.role_name == "responder"

    @staticmethod
    def vars_for_template(player: Player):
        multiplied_amount = player.group.multiplied_amount()
        return dict(
            pair_card_vars(player),
            is_practice=player.is_practice_round,
            offer=player.group.offer,
            offer_number=point_number(player.group.offer),
            multiplier_applied=get_group_realized_multiplier(player.group),
            multiplied_amount=multiplied_amount,
            multiplied_amount_number=point_number(multiplied_amount),
            low_multiplier=C.LOW_MULTIPLIER,
            large_multiplier=get_large_multiplier(player.session),
        )

    @staticmethod
    def error_message(player: Player, values):
        value = values["intended_return"]
        return intended_return_error_message(player.group, value)


class WaitForResponder(WaitPage):
    title_text = "Waiting for responder"
    body_text = "Please wait for the responder to make a decision."
    after_all_players_arrive = set_payoffs


class ProposerReceipt(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.role_name == "proposer"

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            pair_card_vars(player),
            is_practice=player.is_practice_round,
            offer=player.group.offer,
            delivered_return=player.group.delivered_return,
            proposer_payoff=proposer_round_points(player.group),
        )


class ProposerBelief(Page):
    form_model = "player"
    form_fields = ["proposer_belief_low_balls", "proposer_belief_large_balls"]

    @staticmethod
    def is_displayed(player: Player):
        return player.role_name == "proposer"

    @staticmethod
    def vars_for_template(player: Player):
        return {
            **pair_card_vars(player),
            **round_summary_vars(player),
            "is_practice": player.is_practice_round,
            "low_multiplier": C.LOW_MULTIPLIER,
            "large_multiplier": get_large_multiplier(player.session),
        }

    @staticmethod
    def error_message(player: Player, values):
        low_balls = values["proposer_belief_low_balls"]
        large_balls = values["proposer_belief_large_balls"]
        if low_balls is None or large_balls is None:
            return "Please place all 10 balls."
        if low_balls + large_balls != 10:
            return "Please place exactly 10 balls across the two multipliers."

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.proposer_belief_multiplier = implied_multiplier_belief(player)
        if player.is_practice_round:
            player.multiplier_belief_bonus = cu(0)
            player.payoff = cu(0)
            return

        player.multiplier_belief_bonus = proposer_multiplier_belief_bonus(player)
        player.payoff = proposer_round_points(player.group) + player.multiplier_belief_bonus


class ResponderReceipt(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.role_name == "responder"

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            pair_card_vars(player),
            is_practice=player.is_practice_round,
            offer=player.group.offer,
            multiplied_amount=player.group.multiplied_amount(),
            intended_return=player.group.intended_return,
            responder_payoff=responder_round_points(player.group),
        )


class QuestionnaireInstructions(Page):
    @staticmethod
    def is_displayed(player: Player):
        return show_end_demographic_survey(player)


class SelfIdentification(Page):
    form_model = "player"
    form_fields = [
        "age",
        "age_prefer_not_to_say",
        "ethnicity",
        "race",
        "gender",
        "sexuality",
    ]

    @staticmethod
    def is_displayed(player: Player):
        return show_end_demographic_survey(player)

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            player_profile=profile_for(player),
            player_role_label=player.role_name.title(),
            show_profile=False,
        )

    @staticmethod
    def error_message(player: Player, values):
        if values["age_prefer_not_to_say"]:
            return

        age = values["age"]
        if age is not None and age < C.MIN_AGE:
            return dict(age="You must be 18 or older")

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if player.age_prefer_not_to_say or player.field_maybe_none("age") is None:
            player.age = None
            player.age_prefer_not_to_say = True


class PartnerIdentification1(Page):
    template_name = "trust_game/PartnerIdentification.html"
    form_model = "player"
    form_fields = partner_survey_form_fields(1)

    @staticmethod
    def is_displayed(player: Player):
        return show_end_demographic_survey(player)

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
        return show_end_demographic_survey(player)

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
        return show_end_demographic_survey(player)

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
        return show_end_demographic_survey(player)

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
        return show_end_demographic_survey(player)

    @staticmethod
    def error_message(player: Player, values):
        return partner_survey_error_message(values, 5)

    @staticmethod
    def vars_for_template(player: Player):
        return partner_survey_vars(player, 5)


page_sequence = [
    InstructionsIntro,
    Instructions,
    Instructions2,
    Instructions3,
    Instructions4,
    Instructions5,
    Instructions6,
    InstructionQuiz,
    InstructionQuizFailed,
    RoleNotice,
    ProposerDecision,
    WaitForProposer,
    ResponderDecision,
    WaitForResponder,
    ProposerReceipt,
    ProposerBelief,
    ResponderReceipt,
    QuestionnaireInstructions,
    SelfIdentification,
    PartnerIdentification1,
    PartnerIdentification2,
    PartnerIdentification3,
    PartnerIdentification4,
    PartnerIdentification5,
]


SELF_DEMOGRAPHIC_EXPORT_FIELDS = [
    "age",
    "age_prefer_not_to_say",
    "ethnicity",
    "race",
    "gender",
    "sexuality",
]

PARTNER_SURVEY_EXPORT_SUFFIXES = [
    "age_guess",
    "age_confidence",
    "ethnicity_guess",
    "ethnicity_confidence",
    "race_guess",
    "race_confidence",
    "gender_guess",
    "gender_confidence",
    "sexuality_guess",
    "sexuality_confidence",
    "existing_relationship",
    "relationship_nature",
]


def self_demographic_headers(role_prefix):
    return [f"{role_prefix}_{field}" for field in SELF_DEMOGRAPHIC_EXPORT_FIELDS]


def partner_survey_headers(role_prefix):
    headers = []
    for slot in range(1, C.PERIODS + 1):
        headers.append(f"{role_prefix}_matched_partner_{slot}_name")
        headers.extend(
            f"{role_prefix}_matched_partner_{slot}_{suffix}"
            for suffix in PARTNER_SURVEY_EXPORT_SUFFIXES
        )
    return headers


def final_round_player(player):
    try:
        return player.in_round(C.NUM_ROUNDS)
    except Exception:
        return player


def self_demographic_values(player):
    final_player = final_round_player(player)
    return [
        nullable_field(final_player, field)
        for field in SELF_DEMOGRAPHIC_EXPORT_FIELDS
    ]


def partner_survey_values(player):
    final_player = final_round_player(player)
    values = []
    for slot in range(1, C.PERIODS + 1):
        partner = matched_partner_for_period(final_player, slot)
        values.append(profile_for(partner)["title"])
        values.extend(
            nullable_field(final_player, f"partner_{slot}_{suffix}")
            for suffix in PARTNER_SURVEY_EXPORT_SUFFIXES
        )
    return values


def custom_export(players):
    base_headers = [
        "session_code",
        "session_config",
        "treatment_randomization_level",
        "is_real_experiment",
        "treatment_box",
        "treatment_label",
        "treatment_code",
        "picture_condition",
        "random_multiplier_condition",
        "chance_of_3",
        "large_multiplier_probability",
        "low_multiplier",
        "large_multiplier",
        "realized_multiplier",
        "large_multiplier_applied",
        "period",
        "round_in_period",
        "otree_round",
        "is_practice_round",
        "proposer_code",
        "proposer_name",
        "responder_code",
        "responder_name",
        "offer",
        "multiplied_amount",
        "intended_return",
        "delivered_return",
        "proposer_belief_multiplier",
        "proposer_belief_low_balls",
        "proposer_belief_large_balls",
        "multiplier_belief_bonus",
        "proposer_payoff",
        "responder_payoff",
    ]
    yield (
        base_headers
        + self_demographic_headers("proposer")
        + partner_survey_headers("proposer")
        + self_demographic_headers("responder")
        + partner_survey_headers("responder")
    )

    for player in players:
        if nullable_field(player, "role_name") != "proposer":
            continue

        group = player.group
        group_players = group.get_players()
        proposer = next(
            p for p in group_players if nullable_field(p, "role_name") == "proposer"
        )
        responder = next(
            p for p in group_players if nullable_field(p, "role_name") == "responder"
        )
        offer = nullable_field(group, "offer")
        multiplied_amount = (
            offer * get_group_realized_multiplier(group)
            if offer is not None
            else None
        )
        base_values = [
            player.session.code,
            player.session.config["name"],
            get_treatment_randomization_level(player.session),
            is_real_experiment_session(player.session),
            nullable_field(group, "treatment_label"),
            nullable_field(group, "treatment_label"),
            nullable_field(group, "treatment_code"),
            nullable_field(group, "treatment_picture"),
            nullable_field(group, "treatment_error"),
            get_chance_of_3(player.session),
            get_group_high_multiplier_probability(group),
            C.LOW_MULTIPLIER,
            get_large_multiplier(player.session),
            get_group_realized_multiplier(group),
            nullable_field(group, "high_multiplier_applied"),
            nullable_field(player, "period_number"),
            nullable_field(player, "round_in_period"),
            player.round_number,
            nullable_field(player, "is_practice_round"),
            proposer.participant.code,
            profile_for(proposer)["title"],
            responder.participant.code,
            profile_for(responder)["title"],
            offer,
            multiplied_amount,
            nullable_field(group, "intended_return"),
            nullable_field(group, "delivered_return"),
            nullable_field(proposer, "proposer_belief_multiplier"),
            nullable_field(proposer, "proposer_belief_low_balls"),
            nullable_field(proposer, "proposer_belief_large_balls"),
            nullable_field(proposer, "multiplier_belief_bonus"),
            nullable_field(proposer, "payoff"),
            nullable_field(responder, "payoff"),
        ]
        yield (
            base_values
            + self_demographic_values(proposer)
            + partner_survey_values(proposer)
            + self_demographic_values(responder)
            + partner_survey_values(responder)
        )
