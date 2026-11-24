import unittest

from lily_ai.schedule import lr_at


class ScheduleTests(unittest.TestCase):
    def test_warm_up_then_fall_to_a_tenth(self):
        self.assertAlmostEqual(lr_at(0, 1000, 1.0, warmup=10), 0.1)
        self.assertAlmostEqual(lr_at(9, 1000, 1.0, warmup=10), 1.0)
        self.assertAlmostEqual(lr_at(1000, 1000, 1.0, warmup=10), 0.1)
        values = [lr_at(step, 1000, 1.0, warmup=10) for step in range(10, 1000)]
        self.assertEqual(values, sorted(values, reverse=True))


if __name__ == "__main__":
    unittest.main()
