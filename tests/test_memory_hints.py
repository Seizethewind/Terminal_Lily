import unittest

from lily.llm.profile_picker import pick
from lily.memory import feedback, run_log
from lily.memory.db import Database
from lily.memory.profile_hints import suggest
from lily.state import State

TEXT = "please summarize this meeting transcript"


def teach(db, profile, rating, text=TEXT, times=1):
    for _ in range(times):
        feedback.rate(db, run_log.record(db, {"user_text": text, "answer": "x", "profile": profile}), rating)


class HintTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")

    def test_no_history_means_no_opinion(self):
        self.assertIsNone(suggest(self.db, TEXT))

    def test_one_verdict_is_not_enough(self):
        teach(self.db, "smart", 1)
        self.assertIsNone(suggest(self.db, TEXT))

    def test_good_answers_vote_for_their_profile(self):
        teach(self.db, "smart", 1, times=2)
        self.assertEqual(suggest(self.db, "can you summarize that meeting transcript too"), "smart")

    def test_bad_fast_answers_vote_for_smart(self):
        teach(self.db, "fast", -1, times=2)
        self.assertEqual(suggest(self.db, TEXT), "smart")

    def test_bad_smart_answers_say_nothing(self):
        teach(self.db, "smart", -1, times=3)
        self.assertIsNone(suggest(self.db, TEXT))

    def test_unrelated_questions_are_not_affected(self):
        teach(self.db, "smart", 1, times=3)
        self.assertIsNone(suggest(self.db, "what is the weather in Cebu tomorrow"))

    def test_a_tie_gives_no_opinion(self):
        teach(self.db, "smart", 1, times=2)
        teach(self.db, "fast", 1, times=2)
        self.assertIsNone(suggest(self.db, TEXT))

    def test_picker_uses_the_hint_only_when_rules_do_not_match(self):
        state = State()
        state.add("user", "quick note")
        self.assertEqual(pick(state, {"fast": ["quick"]}, lambda text: "smart"), "fast")
        other = State()
        other.add("user", "hello")
        self.assertEqual(pick(other, {"fast": ["quick"]}, lambda text: "smart"), "smart")
        self.assertEqual(pick(other, {"fast": ["quick"]}, lambda text: None), "auto")

    def test_picker_never_overrides_a_profile_set_by_hand(self):
        state = State(profile="fast")
        state.add("user", "hello")
        self.assertEqual(pick(state, {}, lambda text: "smart"), "fast")


if __name__ == "__main__":
    unittest.main()
