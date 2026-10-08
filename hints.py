"""Explainable deductions and an explicitly approximate risk heuristic.

The hint engine accepts a Snapshot, never a Board or its hidden mine locations.
Player flags are annotations, not evidence: a misplaced flag cannot invalidate
a deduction. This is deliberately a small educational solver, not a full CSP.
"""

from __future__ import annotations

from dataclasses import dataclass
from engine import Cell, Snapshot, neighbors


def label(cell: Cell) -> str:
    return f"row {cell[0] + 1}, column {cell[1] + 1}"


@dataclass(frozen=True)
class Constraint:
    cells: frozenset[Cell]
    mines: int
    source: str


@dataclass(frozen=True)
class Hint:
    action: str  # open, flag, unflag, guess, none
    cell: Cell | None
    title: str
    explanation: str
    risk_score: float | None = None


@dataclass
class Deductions:
    safe: set[Cell]
    mines: set[Cell]
    reasons: dict[Cell, str]


def constraints_for(view: Snapshot) -> list[Constraint]:
    hidden = view.hidden
    result = []
    for r in range(view.rows):
        for c in range(view.cols):
            clue = view.clues[r][c]
            if clue is None:
                continue
            cells = frozenset(n for n in neighbors(view.rows, view.cols, (r, c)) if n in hidden)
            if cells or clue:
                result.append(Constraint(cells, clue, f"Clue {clue} at {label((r, c))}"))
    result.append(Constraint(hidden, view.mine_count, "The board's total mine count"))
    return result


def deduce(constraints: list[Constraint]) -> Deductions:
    """Propagate zero/all-mine rules and extreme subset differences to a fixpoint.

    We do not keep arbitrary derived constraints. This bounds the constraint
    count but also means some valid deductions will remain undiscovered.
    """
    safe: set[Cell] = set()
    mines: set[Cell] = set()
    reasons: dict[Cell, str] = {}

    def record(cells: frozenset[Cell], target: set[Cell], reason: str) -> None:
        for cell in sorted(cells - target):
            target.add(cell)
            reasons[cell] = reason

    while True:
        before = len(safe) + len(mines)
        reduced = []
        for constraint in constraints:
            unknown = constraint.cells - safe - mines
            remaining = constraint.mines - len(constraint.cells & mines)
            if not 0 <= remaining <= len(unknown):
                raise ValueError("Visible clues are inconsistent.")
            if not unknown:
                continue
            reduced.append(Constraint(unknown, remaining, constraint.source))
            if remaining == 0:
                record(unknown, safe, f"{constraint.source}: after earlier deductions, no mines remain among these hidden cells.")
            elif remaining == len(unknown):
                record(unknown, mines, f"{constraint.source}: {remaining} mines remain in exactly {len(unknown)} hidden cells, so all are mines.")

        if safe & mines:
            raise ValueError("Visible clues imply contradictory deductions.")
        if len(safe) + len(mines) > before:
            continue  # Normalize all constraints against the new knowledge.

        for small in reduced:
            for large in reduced:
                if not small.cells < large.cells:
                    continue
                difference = large.cells - small.cells
                count = large.mines - small.mines
                if not 0 <= count <= len(difference):
                    raise ValueError("Visible subset constraints are inconsistent.")
                reason = (f"Subset rule: {small.source.lower()} gives {small.mines} mine(s) in the smaller set; "
                          f"{large.source.lower()} gives {large.mines} in the containing set. "
                          f"The {len(difference)} extra cell(s) contain {count} mine(s).")
                if count == 0:
                    record(difference, safe, reason)
                elif count == len(difference):
                    record(difference, mines, reason)
        if safe & mines:
            raise ValueError("Visible clues imply contradictory deductions.")
        if len(safe) + len(mines) == before:
            return Deductions(safe, mines, reasons)


def choose_hint(view: Snapshot) -> Hint:
    if view.status in {"won", "lost"}:
        return Hint("none", None, "Game finished", "Start a new game to get more hints.")
    hidden = view.hidden
    playable = hidden - view.flags
    if view.status == "ready":
        if not playable:
            return Hint("none", None, "Remove a flag", "Every hidden cell is flagged. Remove a flag to make your first move.")
        center = ((view.rows - 1) / 2, (view.cols - 1) / 2)
        cell = min(playable, key=lambda p: ((p[0] - center[0]) ** 2 + (p[1] - center[1]) ** 2, p))
        return Hint("open", cell, "Safe first move", "This game's first move is protected. Mines are placed only when you open a cell.")

    constraints = constraints_for(view)
    known = deduce(constraints)
    if known.safe:
        # Prefer a safe tile that can be opened immediately over removing a flag.
        cell = min(known.safe, key=lambda p: (p in view.flags, p))
        if cell in view.flags:
            return Hint("unflag", cell, "This flag can be removed", known.reasons[cell] + " This cell is safe; remove its flag first.")
        return Hint("open", cell, "Proven safe move", known.reasons[cell])
    unflagged_mines = known.mines - view.flags
    if unflagged_mines:
        cell = min(unflagged_mines)
        return Hint("flag", cell, "Proven mine", known.reasons[cell])

    candidates = playable - known.mines
    if not candidates:
        return Hint("none", None, "Review your flags", "No unflagged candidate remains. Flags are guesses until the clues prove them; remove one to continue.")
    unknown = hidden - known.mines
    baseline = (view.mine_count - len(known.mines)) / len(unknown)
    scores: dict[Cell, float] = {}
    for cell in candidates:
        ratios = [
            (con.mines - len(con.cells & known.mines)) / len(con.cells - known.mines)
            for con in constraints[:-1]  # Global density is only the fallback.
            if cell in con.cells
        ]
        scores[cell] = sum(ratios) / len(ratios) if ratios else baseline
    # More adjacent hidden cells is an inexpensive information-gain proxy.
    cell = min(candidates, key=lambda p: (
        scores[p], -sum(n in hidden for n in neighbors(view.rows, view.cols, p)), p
    ))
    return Hint(
        "guess", cell, "Guess - safety is not proven",
        f"Lowest estimated risk score: {scores[cell]:.1%}. This is the mean of adjacent clue densities, "
        "or the board-wide density when no clue touches this cell. It is not an exact probability. "
        "Ties favor more adjacent hidden cells. This move can hit a mine.", scores[cell],
    )
