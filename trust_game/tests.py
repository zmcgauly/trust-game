from otree.api import Bot, Submission

from . import (
    C,
    InstructionsIntro,
    Instructions,
    Instructions2,
    Instructions3,
    Instructions4,
    Instructions5,
    InstructionQuiz,
    ProposerBeliefPost,
    ProposerDecision,
    ProposerReceipt,
    ResponderDecision,
    ResponderReceipt,
    RoleNotice,
    QuestionnaireInstructions,
    SelfIdentification,
    PaymentSummary,
    get_active_periods,
    is_real_experiment_session,
    treatment_partner_cue,
)


class PlayerBot(Bot):
    def play_round(self):
        if self.round_number == 1:
            if is_real_experiment_session(self.player.session):
                yield InstructionsIntro
                yield Instructions
                yield Instructions2
                yield Instructions3
                yield Instructions4
                yield Instructions5
                yield InstructionQuiz, dict(
                    instruction_quiz_1="same",
                    instruction_quiz_2="learning",
                    instruction_quiz_3="zero_to_twenty",
                    instruction_quiz_4="sent_available",
                    instruction_quiz_5="correct",
                    instruction_quiz_6="both_rounds",
                    instruction_quiz_7="eighty_four",
                )
            else:
                yield InstructionsIntro, dict(skip_instructions="1")

        if not self.player.is_active_round:
            return

        if self.player.round_in_period == 1:
            yield RoleNotice

        if self.player.role_name == "proposer":
            yield ProposerDecision, dict(offer=10)
            yield ProposerReceipt
            yield ProposerBeliefPost, dict(belief_post_probability_low=50)
        else:
            yield ResponderDecision, dict(
                intended_return=int(self.player.group.multiplied_amount() / 2)
            )
            yield ResponderReceipt

        if self.round_number == C.PRACTICE_ROUNDS + get_active_periods(self.player.session) * C.ROUNDS_PER_PERIOD:
            yield QuestionnaireInstructions
            identification = dict(
                age=None,
                age_prefer_not_to_say=True,
                ethnicity="Prefer not to say",
                race="Prefer not to say",
                gender="Prefer not to say",
                sexuality="Prefer not to say",
            )
            yield SelfIdentification, identification

            if treatment_partner_cue(self.player):
                from . import (
                    PartnerIdentification1, PartnerIdentification2, PartnerIdentification3,
                    PartnerIdentification4, PartnerIdentification5, PartnerIdentification6,
                    PartnerIdentification7, PartnerIdentification8, PartnerIdentification9,
                    PartnerIdentification10,
                )
                pages = [
                    PartnerIdentification1, PartnerIdentification2, PartnerIdentification3,
                    PartnerIdentification4, PartnerIdentification5, PartnerIdentification6,
                    PartnerIdentification7, PartnerIdentification8, PartnerIdentification9,
                    PartnerIdentification10,
                ]
                for slot, page in enumerate(pages[: get_active_periods(self.player.session)], start=1):
                    prefix = f"partner_{slot}"
                    yield page, {
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
            yield Submission(PaymentSummary, check_html=False)
