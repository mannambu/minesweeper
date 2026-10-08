# Minesweeper
## CO3061 - Homework 1 - Topic 1

**Design, BFS flood fill, and explainable move heuristics**

**Group: {{GROUP_NAME}}**

HCMUT - VNU HCM / Introduction to Artificial Intelligence

Prepared: 7 October 2026. Assignment deadline: Sunday, 11 October 2026, 23:59. The assignment does not specify a timezone.

{{DRAFT_NOTICE}}

### Group members and contributions

{{TEAM_TABLE}}

Contribution percentages record each member's share of the group's contribution.

### Project overview

This project implements a playable Minesweeper game in Python and Tkinter. It supports 5 x 5, 9 x 9, and 16 x 16 boards, mine flags, automatic opening of empty regions, a timer, and win/loss detection. The first opened cell is protected as a usability enhancement.

Breadth-first search (BFS) opens a connected region of zero-clue cells and its numbered boundary. A separate hint engine uses visible-clue constraints to prove safe cells or mines. When its rules cannot prove a move, it suggests a guess with a clearly labeled, approximate risk score.

### What the submission contains

| Deliverable | Included files |
| --- | --- |
| Playable source code | main.py, engine.py, hints.py, run.bat |
| Verification | tests/, gui_smoke.py, validation.txt |
| Documentation | report.pdf and README.md |
| Editable report | report.md, team.json, build_report.py |

The game requires Python 3.10 or later with Tkinter. There are no third-party runtime dependencies for the game. Rebuilding this report additionally requires ReportLab.

---

## 1. Requirements and design

The supplied assignment requires a GUI, opening and flagging cells, correct victory and defeat conditions, and a step-by-step PDF explanation. It permits DFS and/or BFS and asks which heuristics could be used. This implementation chooses BFS and also implements a hint system to demonstrate heuristic reasoning.

{{ARCHITECTURE}}

### Model and state

A cell is represented internally by a zero-based `(row, column)` tuple. The interface displays coordinates starting at 1. The board stores its dimensions, total mines, private mine positions, adjacent-mine counts, revealed safe cells, flags, and game status. A cell's neighbors are the valid horizontal, vertical, and diagonal adjacent cells, at most eight.

The state transitions are `ready -> playing -> won/lost`. Mine placement occurs on the first opening, not when a flag is placed. A win occurs exactly when the number of revealed safe cells equals `rows * columns - mine_count`. Opening a mine causes an immediate loss. Finished games reject further opens and flag changes.

### Interface and controls

| Control or display | Behavior |
| --- | --- |
| Board selector / New game | Starts a fresh 5 x 5, 9 x 9, or 16 x 16 board |
| Left-click | Opens an unflagged hidden cell |
| Right-click / Flag mode | Toggles a hidden tile's flag |
| Get a hint | Highlights a move and displays its explanation |
| Play highlighted move | Applies the suggested open, flag, or unflag |
| Play guess (may lose) | Explicitly applies an uncertain move |
| Status, safe cells, flags, time | Shows progress; flags are not verified mines |

### Separation of information

The GUI controls the board. The hint engine receives only an immutable snapshot of revealed clues, flags, dimensions, total mines, and status. Hidden cell values are `None`. It has no access to the board's mine positions. The GUI can display mines after a game finishes.

---

## 2. Mine placement and BFS

### Step 1 - generate a valid board

On the first opening, the engine excludes the clicked cell and, if there is sufficient space, all its neighbors from mine placement. It samples distinct mine positions from the remaining cells. For dense custom boards it protects only the clicked cell. All three supplied presets have room to protect the complete neighborhood.

For every cell, it then counts how many of the at most eight neighbors contain mines. An optional random seed makes the layout reproducible when the same first cell is chosen. This protects the first move but does not guarantee that the entire game can be solved without guessing.

### Step 2 - open using breadth-first search

```text
REVEAL(start):
    reject finished games, flagged cells, and already-open cells
    if ready: place mines while protecting start
    if start is a mine: lose and return
    queue <- [start]; queued <- {start}
    while queue is not empty:
        current <- remove from front of queue
        if current is flagged or already open: continue
        reveal current
        if clue(current) == 0:
            for each valid neighbor n:
                if n is not queued, flagged, or already open:
                    add n to queued; append n to queue
    if all safe cells are open: win
```

### Why it is correct

Only zero-clue cells expand their neighbors, and a zero has no neighboring mines. Therefore a safe starting cell cannot cause BFS to open a mine. Every reachable zero is eventually processed, revealing the connected empty area. Numbered cells next to that area are revealed but do not expand, forming the boundary. Flags deliberately block opening, including an incorrectly flagged safe cell.

The `queued` set prevents repeated enqueueing. Every iteration removes one entry from the queue, and there are finitely many cells, so the procedure terminates. The engine uses `collections.deque` to remove from the front without shifting a Python list.

### Complexity

Let N be the number of board cells. Each cell is enqueued at most once and examines at most eight neighbors. BFS takes O(N) time in the worst case, with O(N) auxiliary space. A single numbered opening takes O(1) after board generation. Mine placement and clue generation take O(N) time and space.

---

## 3. A worked BFS example

Consider this fixed 3 x 3 board with one mine at row 1, column 1. It is an explanatory test layout. Open row 3, column 3, which has clue 0. Coordinates below are one-based.

{{BFS_DIAGRAM}}

The implementation iterates neighbors in row order. Its queue processes the cells in the following order. A numbered cell is opened but does not add its neighbors.

| Step | Popped cell / clue | Newly appended cells |
| --- | --- | --- |
| 1 | (3,3) / 0 | (2,2), (2,3), (3,2) |
| 2 | (2,2) / 1 | None; numbered boundary |
| 3 | (2,3) / 0 | (1,2), (1,3) |
| 4 | (3,2) / 0 | (2,1), (3,1) |
| 5 | (1,2) / 1 | None; numbered boundary |
| 6 | (1,3) / 0 | None; all neighbors already queued |
| 7 | (2,1) / 1 | None; numbered boundary |
| 8 | (3,1) / 0 | None; all neighbors already queued |

All eight safe cells are revealed, so the board is won. The mine is never enqueued: no zero-clue cell is adjacent to it. If a safe cell were flagged, it would remain closed and would need to be unflagged and opened before victory.

### Why BFS rather than recursive DFS?

Both algorithms can compute the same empty region and its boundary in O(N) time. BFS uses a queue and provides a clear exploration order for explanation. Iterative DFS would also avoid recursion limits. Recursive DFS could exceed Python's recursion limit on a sufficiently large empty region, so the implementation uses an explicit queue.

BFS is not the strategy for choosing the next unknown cell. It is the flood-fill procedure after an opening. Choosing a move under uncertainty is the responsibility of the hint engine described next.

---

## 4. Logical hint rules

### Construct constraints from visible clues

For each revealed clue c, let U(c) be the set of its hidden neighboring cells. Let x(u) equal 1 if hidden cell u is a mine and 0 otherwise. The clue gives the constraint `sum(x(u) for u in U(c)) = c`. A separate global constraint states that all hidden cells together contain the board's total number of mines.

During propagation, remove cells already proved safe and subtract already proved mines from each constraint. The residual constraint contains an unknown set U and a remaining mine count k. Player flags are not subtracted: they may be wrong.

### Rule 1 - zero remaining mines

If `k = 0`, every cell in U is safe. For example, if a clue 1 already has a logically proved mine among its neighbors, all its other hidden neighbors are safe.

### Rule 2 - every remaining cell is a mine

If `k = |U|`, every cell in U is a mine. For example, a clue 2 with exactly two unresolved neighboring cells proves that both are mines. The assistant can recommend flagging one of them.

### Rule 3 - subset difference

If the unknown set of one constraint A is a strict subset of another constraint B, subtract the two equations. The cells in `B - A` contain `k(B) - k(A)` mines. If that difference is zero, those cells are safe; if it equals the size of `B - A`, they are all mines.

| Visible constraints | Consequence |
| --- | --- |
| A = {a,b}: 1 mine; B = {a,b,c}: 1 mine | c is safe because 1 - 1 = 0 |
| A = {a,b}: 1 mine; B = {a,b,c}: 2 mines | c is a mine because 2 - 1 = 1 |

### Repeat until no new facts appear

The engine normalizes the constraints, applies zero/all-mine rules, then checks subset differences. New facts are propagated until an iteration discovers nothing. It retains the original constraints, not arbitrary intermediate constraints. This keeps the method simple but makes it incomplete: it can miss valid deductions requiring more general constraint reasoning.

The assistant first suggests a proved safe opening, then removing a flag from a proved safe cell, then flagging a proved mine. These are deductions, not risk estimates. A guess is considered only when these actions are unavailable.

---

## 5. Heuristics when proof is unavailable

### Estimated local risk

For an unresolved cell u next to one or more revealed clues, calculate each adjacent clue's residual mine density `k / |U|`, after subtracting logically proved mines. The risk score for u is the arithmetic mean of these densities. If no revealed clue touches u, use the global density: remaining unproved mines divided by hidden cells not already proved to be mines.

The assistant chooses the eligible cell with the smallest score. It excludes flagged cells and proved mines. A flagged tile is not excluded from the constraint equations or density denominators: flags are only player annotations.

### Example and tie-breaking

If one cell participates in residual constraints with densities 1/3 and 1/2, its score is `(1/3 + 1/2) / 2 = 5/12`, approximately 41.7%. A candidate with score 1/4 is preferred. For equal scores, the assistant prefers a cell with more adjacent hidden tiles, as a cheap proxy for potential information gain. Final ties use row/column order for repeatability.

This information heuristic does not compute expected information gain and does not guarantee a larger opening. The local densities can overlap and be dependent. Their average is therefore an estimated ranking score, not an exact posterior mine probability and not a guarantee of safety.

### User-facing behavior and limitations

The interface labels these moves as guesses, displays the score, and changes the apply button to **Play guess (may lose)**. The assistant never silently opens a cell. When the player requests a first-move hint, it recommends an unflagged cell near the center; first-click protection makes this opening safe in this implementation.

The system is not a complete Minesweeper solver. Some positions genuinely require guessing; others could be solved by stronger rules that this implementation does not include. A future extension could enumerate mine assignments consistent with all visible constraints and the total mine count. Exact enumeration can become expensive as the frontier grows.

### Hint cost

There are at most O(N) original constraints. Each productive propagation round identifies at least one new cell, so there are at most O(N) such rounds. Each round compares O(N^2) constraint pairs. Local constraints have at most eight cells; the global constraint has up to N. A conservative bound allowing O(N) per set operation is O(N^4) time, with O(N) stored cell memberships for the original constraints plus the global set. This bound is loose; no arbitrary derived-constraint collection is built. The preset boards are small, but large custom boards would need more efficient frontier processing.

---

## 6. Verification and results

### Automated checks

The recorded validation contains **32 passing unit tests**. The project includes the tests so another group member can rerun them rather than relying on this report alone. Tests cover invalid dimensions, neighbors, seeded generation, protected opening, flag behavior, numbered openings, zero expansion, win/loss locking, visibility boundaries, deduction rules, uncertainty labels, and misplaced flags.

| Check | Scope and observed result |
| --- | --- |
| BFS region oracle | All 36 two-mine 3 x 3 layouts, each of 7 safe starts: 252 openings matched an independent fixed-point region calculation |
| Deduction soundness | 36 layouts x 128 safe-cell reveal subsets: 4,608 states; no safe deduction hit a mine and no mine deduction named a safe cell |
| First-move protection | 15 seeds on each of 3 presets: all tested first cells and their neighborhoods were mine-free |
| Hidden-information isolation | Identical visible snapshots with different mine layouts produced identical hints |
| GUI integration | All presets: create/reset, hint application, and widget height checks passed; flag correction, victory, loss, and reset passed |

### Run the checks

From the project folder:

```text
python -m unittest discover -s tests -v
python gui_smoke.py
```

The second command needs a graphical desktop. It exercises this application's Tk widgets and callbacks and verifies that the tested text controls receive their requested height. Actual output and interpreter details are recorded in `validation.txt`.

### What these results establish

The exhaustive small-board cases provide strong evidence for the implemented deduction rules over that finite test domain. They do not prove correctness for every board size. The test of identical observations also checks that the hint engine's result is independent of unseen mine positions.

The GUI integration check runs the real application code, but it does not replace visual inspection on different screens or platforms. Native desktop capture could not see the isolated test process; a pixel-level review of the running window was not completed. No solver win-rate benchmark or calibrated probability claim is made. The risk heuristic remains approximate.

---

## 7. Running, presenting, and submitting

### Start the game

Extract the ZIP and open its `minesweeper` folder. On Windows, double-click `run.bat`. Alternatively, run `python main.py` in a terminal in that folder. Check Tk availability with `python -m tkinter`. The game requires no pip packages.

For a repeatable demonstration, run `python main.py --level 9 --seed 42`, then use the same first click each time. The available level values are 5, 9, and 16. Omit the seed for fresh randomly generated games.

### Suggested demonstration

1. Start a 9 x 9 game and explain the safe first opening.
2. Open an empty area and connect the revealed cells to the BFS queue.
3. Explain a numbered tile using its eight possible neighbors.
4. Add or remove a flag and show a hint's explanation.
5. Distinguish a proved safe move from an estimated-risk guess.
6. Show `Board.reveal()` and run the included automated tests.

### Before submission

- Verify the member names and contribution percentages in `team.json`.
- Read and revise the design explanation so it matches the code your group submits.
- If you change the code, rerun the tests and update the recorded results.
- Rebuild the PDF with `python build_report.py` after editing the report or team data. This optional build step requires ReportLab.
- Inspect the resulting PDF, especially names and page breaks.
- The prepared archive is `Group6_HW1.zip`. The assignment gives the filename pattern `HW1_YOURNAME.zip`. Include source code and the PDF, and submit once per group on LMS.

### References

1. Supplied HW1.pdf, CO3061, Homework 1, Topic 1, pages 1-2. Source for the assignment requirements and deadline.
2. Python Software Foundation. [Tkinter documentation](https://docs.python.org/3/library/tkinter.html). Reference for the GUI interface and installation check.
3. Python Software Foundation. [collections.deque documentation](https://docs.python.org/3/library/collections.html#collections.deque). Reference for efficient queue operations.
4. Python Software Foundation. [unittest documentation](https://docs.python.org/3/library/unittest.html). Reference for the test framework and discovery command.

Web documentation checked on 7 October 2026. The hint rules, worked examples, implementation, and validation procedures are described explicitly in this report.
