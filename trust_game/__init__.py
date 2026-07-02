import random
from urllib.parse import quote

from otree.api import *


doc = """
Two-by-two trust game with fixed proposer/responder roles, rotating partners,
two rounds per period, optional picture/profile information, and an optional
hidden delivery error on responder returns.
"""


class C(BaseConstants):
    NAME_IN_URL = "trust_game"
    PLAYERS_PER_GROUP = 2
    NUM_DEMO_PARTICIPANTS = 10
    PROPOSERS = 5
    RESPONDERS = 5
    ROUNDS_PER_PERIOD = 2
    PERIODS = 5
    NUM_ROUNDS = PERIODS * ROUNDS_PER_PERIOD
    ENDOWMENT = cu(20)
    MULTIPLIER = 3
    DEFAULT_ERROR_PROBABILITY = 0.50
    DEFAULT_ERROR_RETURN_MULTIPLIER = 0.50
    MIN_AGE = 18
    MAX_AGE = 100
    GENDER_CHOICES = [
        ["Female", "Female"],
        ["Male", "Male"],
        ["Non-Binary", "Non-Binary"],
        ["Other", "Other"],
        ["Prefer not to say", "Prefer not to say"],
    ]
    RACE_CHOICES = [
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
    TREATMENTS = [
        dict(
            code="standard",
            label="No error / No picture",
            picture=False,
            error=False,
            visible_label="Pictures not shown",
        ),
        dict(
            code="error",
            label="Error / No picture",
            picture=False,
            error=True,
            visible_label="Pictures not shown",
        ),
        dict(
            code="picture",
            label="No error / Picture",
            picture=True,
            error=False,
            visible_label="Pictures shown",
        ),
        dict(
            code="picture_error",
            label="Error / Picture",
            picture=True,
            error=True,
            visible_label="Pictures shown",
        ),
    ]


class Subsession(BaseSubsession):
    def vars_for_admin_report(self):
        rows = []
        for index, treatment in enumerate(get_period_treatments(self.session), start=1):
            rows.append(
                dict(
                    period=index,
                    label=treatment["label"],
                    code=treatment["code"],
                    picture=treatment["picture"],
                    error=treatment["error"],
                    picture_text="Shown" if treatment["picture"] else "Not shown",
                    error_text="Active" if treatment["error"] else "Inactive",
                )
            )
        return dict(
            period_treatments=rows,
            error_probability=get_error_probability(self.session),
            error_return_multiplier=get_error_return_multiplier(self.session),
        )


class Group(BaseGroup):
    treatment_code = models.StringField()
    treatment_label = models.StringField()
    treatment_picture = models.BooleanField()
    treatment_error = models.BooleanField()
    error_probability = models.FloatField()
    error_return_multiplier = models.FloatField()

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

    def tripled_amount(self):
        return self.offer * C.MULTIPLIER


class Player(BasePlayer):
    role_name = models.StringField()
    role_number = models.IntegerField()
    period_number = models.IntegerField()
    round_in_period = models.IntegerField()
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
    sexuality = models.StringField(
        choices=C.SEXUALITY_CHOICES,
        label="What is your sexuality?",
        blank=True,
    )
    partner_gender_guess = models.StringField(
        choices=C.GENDER_CHOICES,
        label="Guess what gender this person identifies as.",
        blank=True,
    )
    partner_race_guess = models.StringField(
        choices=C.RACE_CHOICES,
        label="Guess what race this person identifies as.",
        blank=True,
    )
    partner_ethnicity_guess = models.StringField(
        choices=C.ETHNICITY_CHOICES,
        label="Guess if this person identifies as Hispanic or Latino.",
        blank=True,
    )
    partner_age_guess = models.IntegerField(
        label="Guess this person's age.",
        min=0,
        max=C.MAX_AGE,
        blank=True,
    )
    partner_sexuality_guess = models.StringField(
        choices=C.SEXUALITY_CHOICES,
        label="Guess what sexuality this person identifies as.",
        blank=True,
    )
    proposer_belief_return = models.CurrencyField(
        min=0,
        label="",
    )


def make_period_treatments():
    return [random.choice(C.TREATMENTS).copy() for _ in range(C.PERIODS)]


def get_period_treatments(session):
    return session.vars.get("period_treatments", [])


def get_period_treatment(session, period_index):
    return get_period_treatments(session)[period_index]


def get_error_probability(session):
    return float(session.config.get("error_probability", C.DEFAULT_ERROR_PROBABILITY))


def get_error_return_multiplier(session):
    return float(session.config.get("error_return_multiplier", C.DEFAULT_ERROR_RETURN_MULTIPLIER))


def get_group_error_probability(group: Group):
    value = group.field_maybe_none("error_probability")
    if value is None:
        value = get_error_probability(group.session)
        group.error_probability = value
    return float(value)


def get_group_error_return_multiplier(group: Group):
    value = group.field_maybe_none("error_return_multiplier")
    if value is None:
        value = get_error_return_multiplier(group.session)
        group.error_return_multiplier = value
    return float(value)


def nullable_field(record, field_name):
    return record.field_maybe_none(field_name)


def creating_session(subsession: Subsession):
    players = subsession.get_players()
    if len(players) != C.NUM_DEMO_PARTICIPANTS:
        raise ValueError("This trust-game schedule currently expects exactly 10 participants.")

    period_index = (subsession.round_number - 1) // C.ROUNDS_PER_PERIOD
    if subsession.round_number == 1:
        subsession.session.vars["period_treatments"] = make_period_treatments()

    treatment = get_period_treatment(subsession.session, period_index)
    proposers = players[: C.PROPOSERS]
    responders = players[C.PROPOSERS :]
    group_matrix = []

    for index, proposer in enumerate(proposers):
        responder = responders[(index + period_index) % C.RESPONDERS]
        group_matrix.append([proposer, responder])

    subsession.set_group_matrix(group_matrix)

    for group in subsession.get_groups():
        group.treatment_code = treatment["code"]
        group.treatment_label = treatment["label"]
        group.treatment_picture = treatment["picture"]
        group.treatment_error = treatment["error"]
        group.error_probability = get_error_probability(subsession.session)
        group.error_return_multiplier = get_error_return_multiplier(subsession.session)

    for player in subsession.get_players():
        is_proposer = player.id_in_subsession <= C.PROPOSERS
        role_number = player.id_in_subsession if is_proposer else player.id_in_subsession - C.PROPOSERS
        role_name = "proposer" if is_proposer else "responder"

        player.role_name = role_name
        player.role_number = role_number
        player.period_number = period_index + 1
        player.round_in_period = ((subsession.round_number - 1) % C.ROUNDS_PER_PERIOD) + 1

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


def visible_treatment_label(player: Player):
    if player.group.treatment_picture:
        return "Pictures shown"
    return "Pictures not shown"


def show_picture_elicitation(player: Player):
    return player.round_in_period == C.ROUNDS_PER_PERIOD and treatment_picture(player)


def set_payoffs(group: Group):
    proposer = get_proposer(group)
    responder = get_responder(group)
    intended_return = group.intended_return or cu(0)
    error_condition = bool(group.treatment_error)
    error_probability = get_group_error_probability(group)
    error_return_multiplier = get_group_error_return_multiplier(group)
    error_applied = error_condition and random.random() < error_probability
    delivered_return = (
        intended_return * error_return_multiplier
        if error_applied
        else intended_return
    )

    group.error_applied = error_applied
    group.delivered_return = delivered_return
    proposer.payoff = C.ENDOWMENT - group.offer + delivered_return
    responder.payoff = group.tripled_amount() - intended_return


def is_whole_point_amount(value):
    return float(value) == int(float(value))


def offer_error_message(group: Group, value):
    if not is_whole_point_amount(value):
        return "Please enter a whole-point amount."


def intended_return_max(group: Group):
    return group.tripled_amount()


def intended_return_error_message(group: Group, value):
    if not is_whole_point_amount(value):
        return "Please enter a whole-point amount."

    max_return = intended_return_max(group)
    if value > max_return:
        return f"You cannot send back more than {max_return}."


class RoleNotice(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            role_label=player.role_name.title(),
            player_profile=profile_for(player),
            visible_treatment_label=visible_treatment_label(player),
            show_profile=treatment_picture(player),
        )

    @staticmethod
    def is_displayed(player: Player):
        return player.round_in_period == 1


class Instructions(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class ProposerDecision(Page):
    form_model = "group"
    form_fields = ["offer"]

    @staticmethod
    def is_displayed(player: Player):
        return player.role_name == "proposer"

    @staticmethod
    def vars_for_template(player: Player):
        partner = get_partner(player)
        return dict(
            partner=partner,
            partner_profile=profile_for(partner),
            show_profile=treatment_picture(player),
            visible_treatment_label=visible_treatment_label(player),
            endowment=C.ENDOWMENT,
            multiplier=C.MULTIPLIER,
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
        partner = get_partner(player)
        return dict(
            partner=partner,
            partner_profile=profile_for(partner),
            show_profile=treatment_picture(player),
            visible_treatment_label=visible_treatment_label(player),
            offer=player.group.offer,
            tripled_amount=player.group.tripled_amount(),
        )


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
        partner = get_partner(player)
        return dict(
            partner=partner,
            partner_profile=profile_for(partner),
            show_profile=treatment_picture(player),
            visible_treatment_label=visible_treatment_label(player),
            offer=player.group.offer,
            delivered_return=player.group.delivered_return,
            proposer_payoff=player.payoff,
        )


class ProposerBelief(Page):
    form_model = "player"
    form_fields = ["proposer_belief_return"]

    @staticmethod
    def is_displayed(player: Player):
        return player.role_name == "proposer"

    @staticmethod
    def vars_for_template(player: Player):
        partner = get_partner(player)
        partner_profile = profile_for(partner)
        return dict(
            partner_profile=partner_profile,
            visible_treatment_label=visible_treatment_label(player),
            belief_question=f"How much do you think {partner_profile['title']} sent you?",
        )

    @staticmethod
    def error_message(player: Player, values):
        value = values["proposer_belief_return"]
        if not is_whole_point_amount(value):
            return dict(proposer_belief_return="Please enter a whole-point amount.")

        max_return = player.group.tripled_amount()
        if value > max_return:
            return dict(
                proposer_belief_return=f"You cannot enter more than {max_return}."
            )


class ResponderReceipt(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.role_name == "responder"

    @staticmethod
    def vars_for_template(player: Player):
        partner = get_partner(player)
        return dict(
            partner=partner,
            partner_profile=profile_for(partner),
            show_profile=treatment_picture(player),
            visible_treatment_label=visible_treatment_label(player),
            offer=player.group.offer,
            tripled_amount=player.group.tripled_amount(),
            intended_return=player.group.intended_return,
            responder_payoff=player.payoff,
        )


class SelfIdentification(Page):
    form_model = "player"
    form_fields = ["age", "ethnicity", "race", "gender", "sexuality"]

    @staticmethod
    def is_displayed(player: Player):
        return show_picture_elicitation(player)

    @staticmethod
    def error_message(player: Player, values):
        if values["age"] < C.MIN_AGE:
            return dict(age="You must be 18 or older")


class PartnerIdentification(Page):
    form_model = "player"
    form_fields = [
        "partner_age_guess",
        "partner_ethnicity_guess",
        "partner_race_guess",
        "partner_gender_guess",
        "partner_sexuality_guess",
    ]

    @staticmethod
    def is_displayed(player: Player):
        return show_picture_elicitation(player)

    @staticmethod
    def error_message(player: Player, values):
        if values["partner_age_guess"] < C.MIN_AGE:
            return dict(partner_age_guess="You must be 18 or older")

    @staticmethod
    def vars_for_template(player: Player):
        partner = get_partner(player)
        return dict(
            current_period=player.period_number,
            partner_profile=profile_for(partner),
        )


page_sequence = [
    RoleNotice,
    Instructions,
    ProposerDecision,
    WaitForProposer,
    ResponderDecision,
    WaitForResponder,
    ProposerReceipt,
    ProposerBelief,
    ResponderReceipt,
    SelfIdentification,
    PartnerIdentification,
]


def custom_export(players):
    yield [
        "session_code",
        "session_config",
        "treatment_box",
        "treatment_label",
        "treatment_code",
        "picture_condition",
        "error_condition",
        "error_probability",
        "error_return_multiplier",
        "period",
        "round_in_period",
        "otree_round",
        "proposer_code",
        "proposer_name",
        "responder_code",
        "responder_name",
        "offer",
        "tripled_amount",
        "intended_return",
        "error_applied",
        "delivered_return",
        "proposer_belief_return",
        "proposer_payoff",
        "responder_payoff",
        "proposer_age",
        "proposer_ethnicity",
        "proposer_race",
        "proposer_gender",
        "proposer_sexuality",
        "proposer_partner_age_guess",
        "proposer_partner_ethnicity_guess",
        "proposer_partner_race_guess",
        "proposer_partner_gender_guess",
        "proposer_partner_sexuality_guess",
        "responder_age",
        "responder_ethnicity",
        "responder_race",
        "responder_gender",
        "responder_sexuality",
        "responder_partner_age_guess",
        "responder_partner_ethnicity_guess",
        "responder_partner_race_guess",
        "responder_partner_gender_guess",
        "responder_partner_sexuality_guess",
    ]

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
        tripled_amount = offer * C.MULTIPLIER if offer is not None else None
        yield [
            player.session.code,
            player.session.config["name"],
            nullable_field(group, "treatment_label"),
            nullable_field(group, "treatment_label"),
            nullable_field(group, "treatment_code"),
            nullable_field(group, "treatment_picture"),
            nullable_field(group, "treatment_error"),
            get_group_error_probability(group),
            get_group_error_return_multiplier(group),
            nullable_field(player, "period_number"),
            nullable_field(player, "round_in_period"),
            player.round_number,
            proposer.participant.code,
            profile_for(proposer)["title"],
            responder.participant.code,
            profile_for(responder)["title"],
            offer,
            tripled_amount,
            nullable_field(group, "intended_return"),
            nullable_field(group, "error_applied"),
            nullable_field(group, "delivered_return"),
            nullable_field(proposer, "proposer_belief_return"),
            nullable_field(proposer, "payoff"),
            nullable_field(responder, "payoff"),
            nullable_field(proposer, "age"),
            nullable_field(proposer, "ethnicity"),
            nullable_field(proposer, "race"),
            nullable_field(proposer, "gender"),
            nullable_field(proposer, "sexuality"),
            nullable_field(proposer, "partner_age_guess"),
            nullable_field(proposer, "partner_ethnicity_guess"),
            nullable_field(proposer, "partner_race_guess"),
            nullable_field(proposer, "partner_gender_guess"),
            nullable_field(proposer, "partner_sexuality_guess"),
            nullable_field(responder, "age"),
            nullable_field(responder, "ethnicity"),
            nullable_field(responder, "race"),
            nullable_field(responder, "gender"),
            nullable_field(responder, "sexuality"),
            nullable_field(responder, "partner_age_guess"),
            nullable_field(responder, "partner_ethnicity_guess"),
            nullable_field(responder, "partner_race_guess"),
            nullable_field(responder, "partner_gender_guess"),
            nullable_field(responder, "partner_sexuality_guess"),
        ]
