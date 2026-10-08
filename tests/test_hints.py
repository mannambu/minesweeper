import itertools
import unittest

from engine import Board, Snapshot, neighbors
from hints import Constraint, choose_hint, constraints_for, deduce


class HintTests(unittest.TestCase):
    def test_zero_constraint_proves_safe(self):
        cells = frozenset({(0, 0), (0, 1)})
        result = deduce([Constraint(cells, 0, "Visible zero")])
        self.assertEqual(result.safe, set(cells))
        self.assertFalse(result.mines)

    def test_full_constraint_proves_mines(self):
        cells = frozenset({(0, 0), (0, 1)})
        result = deduce([Constraint(cells, 2, "Visible two")])
        self.assertEqual(result.mines, set(cells))

    def test_subset_difference_proves_safe(self):
        a, b, c = (0, 0), (0, 1), (0, 2)
        result = deduce([Constraint(frozenset({a, b}), 1, "Clue A"), Constraint(frozenset({a, b, c}), 1, "Clue B")])
        self.assertEqual(result.safe, {c})
        self.assertFalse(result.mines)
        self.assertIn("Subset", result.reasons[c])

    def test_subset_difference_proves_mine(self):
        a, b, c = (0, 0), (0, 1), (0, 2)
        result = deduce([Constraint(frozenset({a, b}), 1, "Clue A"), Constraint(frozenset({a, b, c}), 2, "Clue B")])
        self.assertEqual(result.mines, {c})

    def test_deductions_propagate_between_constraints(self):
        a, b, c = (0, 0), (0, 1), (0, 2)
        result = deduce([Constraint(frozenset({a, b}), 1, "A"), Constraint(frozenset({b, c}), 1, "B"), Constraint(frozenset({a}), 1, "C")])
        self.assertEqual(result.mines, {a, c})
        self.assertEqual(result.safe, {b})

    def test_inconsistent_constraints_rejected(self):
        with self.assertRaises(ValueError):
            deduce([Constraint(frozenset({(0, 0)}), 2, "Invalid")])

    def test_first_hint_is_protected_opening(self):
        hint = choose_hint(Board().snapshot())
        self.assertEqual((hint.action, hint.cell), ("open", (4, 4)))

    def test_first_hint_avoids_flag(self):
        board = Board()
        board.toggle_flag((4, 4))
        self.assertNotEqual(choose_hint(board.snapshot()).cell, (4, 4))

    def test_all_flagged_before_start(self):
        board = Board(3, 3, 2)
        for cell in itertools.product(range(3), repeat=2):
            board.toggle_flag(cell)
        self.assertEqual(choose_hint(board.snapshot()).action, "none")

    def test_uncertain_position_is_labeled_guess(self):
        board = Board.from_mines(3, 3, {(0, 0)})
        board.reveal((1, 1))
        hint = choose_hint(board.snapshot())
        self.assertEqual(hint.action, "guess")
        self.assertAlmostEqual(hint.risk_score, 1 / 8)
        self.assertIn("not an exact probability", hint.explanation)

    def test_flags_are_not_trusted_as_facts(self):
        board = Board.from_mines(3, 3, {(0, 0)})
        board.reveal((1, 1))
        board.toggle_flag((2, 2))  # Incorrect, but unknown to the hint engine.
        hint = choose_hint(board.snapshot())
        self.assertEqual(hint.action, "guess")
        self.assertAlmostEqual(hint.risk_score, 1 / 8)
        self.assertNotEqual(hint.cell, (2, 2))

    def test_proven_safe_flag_is_removed(self):
        board = Board.from_mines(3, 3, {(0, 0)})
        board.toggle_flag((0, 2))
        board.reveal((2, 2))
        hint = choose_hint(board.snapshot())
        self.assertEqual((hint.action, hint.cell), ("unflag", (0, 2)))

    def test_finished_game_has_no_hint(self):
        board = Board.from_mines(3, 3, {(0, 0)})
        board.reveal((0, 0))
        self.assertEqual(choose_hint(board.snapshot()).action, "none")

    def test_hidden_layout_does_not_change_hint(self):
        first = Board.from_mines(3, 3, {(0, 0)})
        second = Board.from_mines(3, 3, {(2, 2)})
        for board in (first, second):
            board.reveal((1, 1))
        self.assertEqual(first.snapshot(), second.snapshot())
        self.assertEqual(choose_hint(first.snapshot()), choose_hint(second.snapshot()))

    def test_soundness_for_all_small_board_observations(self):
        cells = set(itertools.product(range(3), repeat=2))
        cases = 0
        # 36 layouts * 128 revealed subsets = 4,608 visible states.
        # Includes observations beyond those reachable by automatic flood fill.
        for pair in itertools.combinations(sorted(cells), 2):
            mines = set(pair)
            safe = sorted(cells - mines)
            counts = {c: len(set(neighbors(3, 3, c)) & mines) for c in safe}
            for bits in range(1 << len(safe)):
                shown = {c for i, c in enumerate(safe) if bits & (1 << i)}
                view = Snapshot(3, 3, 2, tuple(tuple(counts[(r, c)] if (r, c) in shown else None for c in range(3)) for r in range(3)), frozenset(), "playing")
                result = deduce(constraints_for(view))
                self.assertFalse(result.safe & mines)
                self.assertTrue(result.mines <= mines)
                self.assertFalse(result.safe & shown)
                cases += 1
        self.assertEqual(cases, 4608)


if __name__ == "__main__":
    unittest.main()
