"""Minesweeper rules and iterative BFS, independent of the GUI.

Coordinates are zero-based (row, column) internally. No third-party packages.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import random

Cell = tuple[int, int]


def neighbors(rows: int, cols: int, cell: Cell) -> tuple[Cell, ...]:
    """Return the at most eight valid cells surrounding a cell."""
    r, c = cell
    return tuple(
        (nr, nc)
        for nr in range(max(0, r - 1), min(rows, r + 2))
        for nc in range(max(0, c - 1), min(cols, c + 2))
        if (nr, nc) != cell
    )


@dataclass(frozen=True)
class Snapshot:
    """Only information available to a player; hidden clues are None."""

    rows: int
    cols: int
    mine_count: int
    clues: tuple[tuple[int | None, ...], ...]
    flags: frozenset[Cell]
    status: str

    @property
    def hidden(self) -> frozenset[Cell]:
        return frozenset(
            (r, c) for r in range(self.rows) for c in range(self.cols)
            if self.clues[r][c] is None
        )


class Board:
    def __init__(self, rows: int = 9, cols: int = 9,
                 mine_count: int = 10, seed: int | None = None):
        if rows < 2 or cols < 2 or not 1 <= mine_count < rows * cols:
            raise ValueError("Use at least 2 rows/columns and 1 to rows*cols-1 mines.")
        self.rows, self.cols, self.mine_count = rows, cols, mine_count
        self._rng = random.Random(seed)
        self._mines: set[Cell] = set()
        self._counts: dict[Cell, int] = {}
        self.revealed: set[Cell] = set()  # Safe cells only, even after a loss.
        self.flags: set[Cell] = set()
        self.status = "ready"
        self.exploded: Cell | None = None
        self.last_reveal_count = 0

    @classmethod
    def from_mines(cls, rows: int, cols: int, mines: set[Cell]) -> Board:
        """Create a fixed board for tests; this bypasses first-click protection."""
        board = cls(rows, cols, len(mines))
        for cell in mines:
            board._validate(cell)
        board._mines = set(mines)
        board._count_neighbors()
        board.status = "playing"
        return board

    def _validate(self, cell: Cell) -> None:
        r, c = cell
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            raise ValueError(f"Cell outside the board: {cell}")

    def _place_mines(self, first: Cell) -> None:
        # Lazy placement protects the first cell and, when possible, its ring.
        protected = {first, *neighbors(self.rows, self.cols, first)}
        if self.rows * self.cols - len(protected) < self.mine_count:
            protected = {first}
        candidates = [
            (r, c) for r in range(self.rows) for c in range(self.cols)
            if (r, c) not in protected
        ]
        self._mines = set(self._rng.sample(candidates, self.mine_count))
        self._count_neighbors()
        self.status = "playing"

    def _count_neighbors(self) -> None:
        self._counts = {
            (r, c): sum(n in self._mines for n in neighbors(self.rows, self.cols, (r, c)))
            for r in range(self.rows) for c in range(self.cols)
        }

    @property
    def finished(self) -> bool:
        return self.status in {"won", "lost"}

    @property
    def safe_total(self) -> int:
        return self.rows * self.cols - self.mine_count

    def toggle_flag(self, cell: Cell) -> bool:
        self._validate(cell)
        if self.finished or cell in self.revealed:
            return False
        if cell in self.flags:
            self.flags.remove(cell)
        else:
            self.flags.add(cell)
        return True

    def reveal(self, cell: Cell) -> tuple[Cell, ...]:
        """Open a cell and BFS through zeros, revealing their numbered boundary.

        The queue contains each candidate at most once. Flags stop automatic
        opening. A mine is only triggered by directly opening that mine.
        """
        self._validate(cell)
        if self.finished or cell in self.flags or cell in self.revealed:
            return ()
        if self.status == "ready":
            self._place_mines(cell)
        if cell in self._mines:
            self.status, self.exploded = "lost", cell
            self.last_reveal_count = 0
            return (cell,)

        queue = deque([cell])
        queued = {cell}
        changed: list[Cell] = []
        while queue:
            current = queue.popleft()
            if current in self.flags or current in self.revealed:
                continue
            self.revealed.add(current)
            changed.append(current)
            if self._counts[current] == 0:
                for other in neighbors(self.rows, self.cols, current):
                    if other not in queued and other not in self.flags and other not in self.revealed:
                        queued.add(other)
                        queue.append(other)
        self.last_reveal_count = len(changed)
        if len(self.revealed) == self.safe_total:
            self.status = "won"
        return tuple(changed)

    def snapshot(self) -> Snapshot:
        return Snapshot(
            self.rows, self.cols, self.mine_count,
            tuple(tuple(self._counts[(r, c)] if (r, c) in self.revealed else None
                        for c in range(self.cols)) for r in range(self.rows)),
            frozenset(self.flags), self.status,
        )

    def visible_value(self, cell: Cell) -> int | None:
        return self._counts[cell] if cell in self.revealed else None

    def mine_after_game(self, cell: Cell) -> bool:
        """The GUI may display mines only after the game has finished."""
        return self.finished and cell in self._mines
