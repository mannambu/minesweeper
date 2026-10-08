import itertools
import unittest

from engine import Board, neighbors


class BoardTests(unittest.TestCase):
    def test_invalid_dimensions_and_mine_counts(self):
        for args in ((1, 5, 1), (5, 1, 1), (5, 5, 0), (5, 5, 25)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                Board(*args)

    def test_corner_edge_and_interior_neighbors(self):
        self.assertEqual(len(neighbors(5, 5, (0, 0))), 3)
        self.assertEqual(len(neighbors(5, 5, (0, 2))), 5)
        self.assertEqual(len(neighbors(5, 5, (2, 2))), 8)

    def test_mines_are_placed_on_first_open_not_on_flag(self):
        board = Board(seed=1)
        board.toggle_flag((0, 0))
        self.assertEqual(board.status, "ready")
        self.assertEqual(board.reveal((0, 0)), ())
        self.assertEqual(board.status, "ready")

    def test_first_click_and_ring_safe_across_presets(self):
        for rows, mines in ((5, 4), (9, 10), (16, 40)):
            for seed in range(15):
                board = Board(rows, rows, mines, seed)
                first = (rows // 2, rows // 2)
                board.reveal(first)
                self.assertNotEqual(board.status, "lost")
                self.assertEqual(board.visible_value(first), 0)
                self.assertEqual(len(board._mines), mines)
                self.assertFalse({first, *neighbors(rows, rows, first)} & board._mines)

    def test_dense_board_protects_first_cell_only(self):
        board = Board(2, 2, 3, seed=2)
        board.reveal((0, 0))
        self.assertEqual(board.status, "won")
        self.assertEqual(board.visible_value((0, 0)), 3)

    def test_seed_is_reproducible_with_same_first_cell(self):
        boards = [Board(seed=42), Board(seed=42)]
        for board in boards:
            board.reveal((4, 4))
        self.assertEqual(boards[0]._mines, boards[1]._mines)
        self.assertEqual(boards[0].revealed, boards[1].revealed)

    def test_open_number_does_not_expand(self):
        board = Board.from_mines(3, 3, {(0, 0)})
        self.assertEqual(board.reveal((1, 1)), ((1, 1),))
        self.assertEqual(board.visible_value((1, 1)), 1)

    def test_zero_expands_and_opens_boundary(self):
        board = Board.from_mines(3, 3, {(0, 0)})
        opened = board.reveal((2, 2))
        self.assertEqual(len(opened), 8)
        self.assertEqual(len(set(opened)), len(opened))
        self.assertNotIn((0, 0), opened)
        self.assertEqual(board.status, "won")

    def test_safe_flag_blocks_flood_until_removed(self):
        board = Board.from_mines(3, 3, {(0, 0)})
        board.toggle_flag((0, 2))
        board.reveal((2, 2))
        self.assertNotIn((0, 2), board.revealed)
        self.assertEqual(board.status, "playing")
        board.toggle_flag((0, 2))
        board.reveal((0, 2))
        self.assertEqual(board.status, "won")

    def test_flags_alone_do_not_win(self):
        board = Board.from_mines(3, 3, {(0, 0)})
        board.toggle_flag((0, 0))
        self.assertEqual(board.status, "playing")

    def test_cannot_flag_revealed_cell(self):
        board = Board.from_mines(3, 3, {(0, 0)})
        board.reveal((1, 1))
        self.assertFalse(board.toggle_flag((1, 1)))

    def test_mine_ends_game_and_locks_input(self):
        board = Board.from_mines(3, 3, {(0, 0)})
        board.reveal((0, 0))
        self.assertEqual(board.status, "lost")
        self.assertEqual(board.exploded, (0, 0))
        self.assertEqual(board.reveal((2, 2)), ())
        self.assertFalse(board.toggle_flag((1, 1)))

    def test_winning_locks_input(self):
        board = Board.from_mines(3, 3, {(0, 0)})
        board.reveal((2, 2))
        self.assertFalse(board.toggle_flag((0, 0)))
        self.assertEqual(board.reveal((0, 0)), ())
        self.assertEqual(board.status, "won")

    def test_mines_only_exposed_to_gui_after_finish(self):
        board = Board.from_mines(3, 3, {(0, 0)})
        self.assertFalse(board.mine_after_game((0, 0)))
        board.reveal((0, 0))
        self.assertTrue(board.mine_after_game((0, 0)))

    def test_snapshot_has_no_hidden_values(self):
        board = Board.from_mines(3, 3, {(0, 0)})
        board.reveal((1, 1))
        view = board.snapshot()
        self.assertEqual(view.clues[1][1], 1)
        self.assertIsNone(view.clues[0][0])
        self.assertIsNone(view.clues[2][2])
        self.assertFalse(hasattr(view, "_mines"))

    def test_out_of_range_inputs_rejected(self):
        board = Board()
        for cell in ((-1, 0), (9, 0), (0, 9)):
            with self.assertRaises(ValueError):
                board.reveal(cell)

    def test_bfs_matches_independent_region_oracle(self):
        cells = set(itertools.product(range(3), repeat=2))
        # All 36 two-mine layouts, every safe starting cell: 252 openings.
        for pair in itertools.combinations(sorted(cells), 2):
            mines = set(pair)
            safe = cells - mines
            counts = {c: len(set(neighbors(3, 3, c)) & mines) for c in safe}
            for start in sorted(safe):
                expected = {start}
                while True:
                    expanded = expected | {
                        n for c in expected if counts[c] == 0
                        for n in neighbors(3, 3, c) if n in safe
                    }
                    if expanded == expected:
                        break
                    expected = expanded
                board = Board.from_mines(3, 3, mines)
                self.assertEqual(set(board.reveal(start)), expected)


if __name__ == "__main__":
    unittest.main()
