from otree.api import Bot

from . import (
    C,
    InstructionsIntro,
    Instructions,
    Instructions2,
    Instructions3,
    Instructions4,
    Instructions5,
    Instructions6,
    InstructionQuiz,
    ProposerBelief,
    ProposerDecision,
    ProposerReceipt,
    ResponderDecision,
    ResponderReceipt,
    RoleNotice,
    SelfIdentification,
    PartnerIdentification1,
    PartnerIdentification2,
    PartnerIdentification3,
    PartnerIdentification4,
    PartnerIdentification5,
)


class PlayerBot(Bot):
    def play_round(self):
        if self.round_number == 1:
            yield InstructionsIntro, dict(skip_instructions="")
            yield Instructions, dict(skip_instructions="")
            yield Instructions2, dict(skip_instructions="")
            yield Instructions3, dict(skip_instructions="")
            yield Instructions4, dict(skip_instructions="")
            yield Instructions5, dict(skip_instructions="")
            yield Instructions6, dict(skip_instructions="")
            if self.player.session.config.get("is_real_experiment", True):
                yield InstructionQuiz, dict(
                    instruction_quiz_1="same",
                    instruction_quiz_2="learning",
                    instruction_quiz_3="zero_to_twenty",
                    instruction_quiz_4="sent_available",
                    instruction_quiz_5="correct",
                )

        if self.player.round_in_period == 1:
            yield RoleNotice

        if self.player.role_name == "proposer":
            yield ProposerDecision, dict(offer=10)
            yield ProposerReceipt
            yield ProposerBelief, dict(
                proposer_belief_low_balls=10,
                proposer_belief_large_balls=0,
            )
        else:
            yield ResponderDecision, dict(
                intended_return=self.player.group.multiplied_amount() / 2
            )
            yield ResponderReceipt

        if self.round_number == C.NUM_ROUNDS:
            identification = dict(
                age=None,
                age_prefer_not_to_say=True,
                ethnicity="Prefer not to say",
                race="Prefer not to say",
                gender="Prefer not to say",
                sexuality="Prefer not to say",
            )
            yield SelfIdentification, identification

            for slot, page in enumerate(
                [
                    PartnerIdentification1,
                    PartnerIdentification2,
                    PartnerIdentification3,
                    PartnerIdentification4,
                    PartnerIdentification5,
                ],
                start=1,
            ):
                prefix = f"partner_{slot}"
                partner_identification = {
                    f"{prefix}_age_guess": 30,
                    f"{prefix}_age_confidence": "Sure",
                    f"{prefix}_ethnicity_guess": "No",
                    f"{prefix}_ethnicity_confidence": "Unsure",
                    f"{prefix}_race_guess": "Other",
                    f"{prefix}_race_confidence": "Neither Sure or Unsure",
                    f"{prefix}_gender_guess": "Other",
                    f"{prefix}_gender_confidence": "Unsure",
                    f"{prefix}_sexuality_guess": "Other",
                    f"{prefix}_sexuality_confidence": "Unsure",
                    f"{prefix}_existing_relationship": "No",
                    f"{prefix}_relationship_nature": "",
                }
                yield page, partner_identification
