import unittest

from lily.llm.profile_picker import pick
from lily.state import State

RULES = {"smart": ["code", "plan"], "fast": ["quick", "tl;dr"]}


def state_with(text, profile="auto"):
    state = State(profile=profile)
    state.add("user", text)
    return state


class ProfilePickerTests(unittest.TestCase):
    def test_profile_set_by_hand_always_wins(self):
        self.assertEqual(pick(state_with("write code", "fast"), RULES), "fast")

    def test_coding_words_pick_smart(self):
        self.assertEqual(pick(state_with("Fix this CODE please"), RULES), "smart")

    def test_planning_matches_the_start_of_a_word(self):
        self.assertEqual(pick(state_with("I am planning a trip"), RULES), "smart")

    def test_word_must_start_with_the_trigger(self):
        # "explain" contains "plan" but does not start with it
        self.assertEqual(pick(state_with("explain clouds"), RULES), "auto")

    def test_quick_words_pick_fast(self):
        self.assertEqual(pick(state_with("quick question: capital of Peru?"), RULES), "fast")

    def test_trigger_with_special_characters(self):
        self.assertEqual(pick(state_with("tl;dr of this?"), RULES), "fast")

    def test_smart_is_checked_before_fast(self):
        self.assertEqual(pick(state_with("quick code review"), RULES), "smart")

    def test_no_match_stays_auto(self):
        self.assertEqual(pick(state_with("hello there"), RULES), "auto")

    def test_only_the_latest_user_message_counts(self):
        state = state_with("write code")
        state.add("assistant", "sure")
        state.add("user", "thanks, how is the weather")
        self.assertEqual(pick(state, RULES), "auto")

    def test_empty_conversation_and_no_rules(self):
        self.assertEqual(pick(State(), RULES), "auto")
        self.assertEqual(pick(state_with("code"), {}), "auto")


if __name__ == "__main__":
    unittest.main()
