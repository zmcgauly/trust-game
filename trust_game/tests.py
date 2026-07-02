from otree.api import Bot

from . import (
    C,
    Instructions,
    ProposerBelief,
    ProposerDecision,
    ProposerReceipt,
    ResponderDecision,
    ResponderReceipt,
    RoleNotice,
    SelfIdentification,
    PartnerIdentification,
)


class PlayerBot(Bot):
    def play_round(self):
        if self.player.round_in_period == 1:
            yield RoleNotice

        if self.round_number == 1:
            yield Instructions

        if self.player.role_name == "proposer":
            yield ProposerDecision, dict(offer=10)
            yield ProposerReceipt
            yield ProposerBelief, dict(proposer_belief_return=15)
        else:
            tripled_amount = 10 * C.MULTIPLIER
            yield ResponderDecision, dict(intended_return=tripled_amount / 2)
            yield ResponderReceipt

        if self.player.round_in_period == C.ROUNDS_PER_PERIOD and self.player.group.treatment_picture:
            identification = dict(
                age=30,
                ethnicity="No",
                race="Other",
                gender="Prefer not to say",
                sexuality="Prefer not to say",
            )
            partner_identification = dict(
                partner_age_guess=30,
                partner_ethnicity_guess="No",
                partner_race_guess="Other",
                partner_gender_guess="Prefer not to say",
                partner_sexuality_guess="Prefer not to say",
            )
            yield SelfIdentification, identification
            yield PartnerIdentification, partner_identification
