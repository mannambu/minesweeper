# Minesweeper - CO3061 Homework 1, Topic 1

A playable Python/Tkinter project with iterative BFS and explainable hints.

Group: **Group6_HW1**

| Full name | Contribution |
| --- | --- |
| Lý Quốc Hào | 50% |
| Nguyễn Ngọc Phát | 50% |

## Start here

1. Extract the ZIP completely.
2. Open the `minesweeper` folder.
3. On Windows, double-click `run.bat`, or open a terminal in that folder and run:

```text
python main.py
```

Use Python 3.10 or newer with Tkinter. The game itself uses only the standard
library. `python -m tkinter` checks that your Python installation includes Tk.
If Tkinter is missing, use a Python installation that includes Tcl/Tk. On Windows,
the Python.org installer offers Tcl/Tk support. The MSYS2 Python already installed
on the development computer also passed the GUI integration checks.

## Play

- Left-click a tile to open it. Right-click to add/remove a flag.
- Use **Flag mode** if you prefer to flag with left-clicks.
- Select 5 x 5 (4 mines), 9 x 9 (10 mines), or 16 x 16 (40 mines).
  Changing the selection starts a fresh game.
- The first opened tile is safe. On these presets, its neighbors are also safe.
- An empty tile has zero adjacent mines; BFS opens its connected empty region
  and the safe numbered boundary. Flagged tiles stay closed.
- Open every safe tile to win. Flags alone do not win the game.
- **Get a hint** highlights a move and explains it. **Play highlighted move**
  applies it. A guess uses a separate **Play guess (may lose)** label.
- The flag counter shows flags placed versus total mines, not verified mines.

For a repeatable demo:

```text
python main.py --level 9 --seed 42
```

Use the same first click to reproduce a board. With `--seed`, New game repeats
that seed; omit it for fresh random games.

## Understand the code in this order

1. `engine.py`: eight-neighbor coordinates, lazy mine placement, clues, flags,
   game states, and the queue in `Board.reveal()`.
2. `hints.py`: constraints from visible clues, zero/all-mine rules, subset
   deductions, and the approximate risk score when proof is unavailable.
3. `main.py`: Tkinter widgets and callbacks connecting the rules to the screen.
4. `report.pdf`: the design and algorithms explained with an example.

BFS does not choose the next safe move. It expands already-known empty regions.
The separate hint engine reasons from the visible numbers and total mine count.
It never receives hidden mine positions and does not assume player flags are true.

## Verify

```text
python -m unittest discover -s tests -v
python gui_smoke.py
```

The first command runs 32 tests, including all 4,608 combinations of a two-mine
3 x 3 layout and its revealed safe-cell subsets. It also checks BFS against an
independent region oracle for 252 starting positions. The GUI check needs a
graphical desktop and exercises the actual Tk callbacks and widget sizes.
Recorded results are in `validation.txt`.

## Files

| File | Purpose |
| --- | --- |
| `main.py`, `engine.py`, `hints.py` | Playable game source |
| `run.bat` | Windows launcher |
| `tests/` | Automated rule and hint tests |
| `gui_smoke.py` | Optional Tk integration and layout checks |
| `report.pdf` | Illustrated design and algorithm report |
| `report.md`, `team.json`, `build_report.py` | Editable report and PDF builder |
| `validation.txt` | Recorded test results |

## A short presentation demo

1. Start a seeded 9 x 9 game. Show the safe first move and BFS opening count.
2. Explain what one numbered tile says about its eight neighbors.
3. Place/remove a flag, then ask for a hint and explain its rule.
4. Point out that the guess score is not an exact probability.
5. Open `Board.reveal()` and explain the queue, visited set, and zero expansion.
6. Run the tests and show the small-board soundness checks.

## References

- Supplied `HW1.pdf`, CO3061, Homework 1, Topic 1, pages 1-2.
- [Python Tkinter documentation](https://docs.python.org/3/library/tkinter.html)
- [Python deque documentation](https://docs.python.org/3/library/collections.html#collections.deque)
- [Python unittest documentation](https://docs.python.org/3/library/unittest.html)
