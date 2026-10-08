"""Run with: python main.py [--level 5|9|16] [--seed 42]."""

from __future__ import annotations

import argparse
import time
import tkinter as tk
from tkinter import ttk

from engine import Board, Cell
from hints import Hint, choose_hint, label

LEVELS = {"5 x 5 / 4 mines": (5, 5, 4), "9 x 9 / 10 mines": (9, 9, 10), "16 x 16 / 40 mines": (16, 16, 40)}
BG = "#eef3f7"
INK = "#17324a"
MUTED = "#566e80"
ACCENT = "#007f78"
NUMBER_COLORS = {1: "#165bac", 2: "#087455", 3: "#bc3748", 4: "#7541a3", 5: "#963f13", 6: "#027d83", 7: "#172b3a", 8: "#596575"}


class MinesweeperApp:
    def __init__(self, root: tk.Tk, level: int = 9, seed: int | None = None):
        self.root = root
        self.seed = seed
        self.hint: Hint | None = None
        self.started_at: float | None = None
        self.elapsed = 0
        self._timer_id: str | None = None
        self.level = tk.StringVar(root, next(k for k, v in LEVELS.items() if v[0] == level))
        self.flag_mode = tk.BooleanVar(root, False)
        self.status_text = tk.StringVar(root)
        self.safe_text = tk.StringVar(root)
        self.flag_text = tk.StringVar(root)
        self.time_text = tk.StringVar(root, "00:00")
        self.hint_title = tk.StringVar(root)
        self.hint_body = tk.StringVar(root)
        self.move_text = tk.StringVar(root)
        self.bfs_text = tk.StringVar(root)
        root.title("Minesweeper | CO3061 - Topic 1")
        root.configure(bg=BG)
        root.resizable(False, False)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self._build_layout()
        self.new_game()
        self._tick()

    def _build_layout(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TCombobox", padding=7)
        header = tk.Frame(self.root, bg=INK, padx=24, pady=18)
        header.pack(fill="x")
        tk.Label(header, text="MINESWEEPER", bg=INK, fg="white", font=("Segoe UI", 22, "bold")).pack(anchor="w")
        tk.Label(header, text="CO3061  /  TOPIC 1     Explore. Deduce. Clear the board.", bg=INK, fg="#b8d2df", font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 0))

        toolbar = tk.Frame(self.root, bg=BG, padx=24, pady=16)
        toolbar.pack(fill="x")
        tk.Label(toolbar, text="BOARD", bg=BG, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 10))
        self.level_box = ttk.Combobox(toolbar, textvariable=self.level, values=list(LEVELS), state="readonly", width=23)
        self.level_box.pack(side="left")
        self.level_box.bind("<<ComboboxSelected>>", lambda event: self.new_game())
        self.new_button = self._button(toolbar, "New game", self.new_game, primary=True)
        self.new_button.pack(side="left", padx=12)
        tk.Checkbutton(toolbar, text="Flag mode", variable=self.flag_mode, bg=BG, fg=INK, activebackground=BG, font=("Segoe UI", 10)).pack(side="right")

        stats = tk.Frame(self.root, bg=BG, padx=24)
        stats.pack(fill="x")
        for i, (caption, variable) in enumerate((("STATUS", self.status_text), ("SAFE CELLS", self.safe_text), ("FLAGS / MINES", self.flag_text), ("TIME", self.time_text))):
            card = tk.Frame(stats, bg="white", padx=14, pady=10)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))
            stats.columnconfigure(i, weight=1, uniform="stats")
            tk.Label(card, text=caption, bg="white", fg=MUTED, font=("Segoe UI", 8, "bold")).pack(anchor="w")
            tk.Label(card, textvariable=variable, bg="white", fg=INK, font=("Segoe UI", 15, "bold")).pack(anchor="w", pady=(2, 0))

        body = tk.Frame(self.root, bg=BG, padx=24, pady=18)
        body.pack(fill="both")
        board_panel = tk.Frame(body, bg=BG, width=490, height=540)
        board_panel.grid(row=0, column=0, sticky="n")
        board_panel.pack_propagate(False)
        self.canvas = tk.Canvas(board_panel, bg=BG, highlightthickness=0)
        self.canvas.pack(anchor="n")
        self.canvas.bind("<Button-1>", self._left_click)
        self.canvas.bind("<Button-3>", self._right_click)
        self.canvas.bind("<Control-Button-1>", self._right_click)
        tk.Label(board_panel, text="Left-click: open    Right-click: flag\nFlag mode lets you flag with a left-click.", bg=BG, fg=MUTED, font=("Segoe UI", 10), justify="center").pack(pady=(12, 0))

        side = tk.Frame(body, bg="white", padx=18, pady=18, width=286, height=540)
        side.grid(row=0, column=1, sticky="n", padx=(18, 0))
        side.pack_propagate(False)
        tk.Label(side, text="REASONING ASSISTANT", bg="white", fg=ACCENT, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(side, textvariable=self.hint_title, bg="white", fg=INK, font=("Segoe UI", 15, "bold"), wraplength=245, justify="left").pack(anchor="w", pady=(14, 8))
        tk.Label(side, textvariable=self.hint_body, bg="white", fg=MUTED, font=("Segoe UI", 10), wraplength=245, justify="left").pack(anchor="w")
        tk.Label(side, textvariable=self.move_text, bg="white", fg=ACCENT, font=("Segoe UI", 10, "bold"), wraplength=245, justify="left").pack(anchor="w", pady=12)
        self.hint_button = self._button(side, "Get a hint", self.show_hint, primary=True)
        self.hint_button.pack(fill="x")
        self.apply_button = self._button(side, "Play highlighted move", self.apply_hint)
        self.apply_button.pack(fill="x", pady=(8, 0))
        tk.Frame(side, bg="#e0e8ed", height=1).pack(fill="x", pady=16)
        tk.Label(side, text="BFS FLOOD FILL", bg="white", fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(side, textvariable=self.bfs_text, bg="white", fg=INK, font=("Segoe UI", 10), wraplength=245, justify="left").pack(anchor="w", pady=(6, 0))
        tk.Label(self.root, text="Win by opening every safe cell. Flags are optional; guesses can still hit mines.", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(pady=(0, 16))

    @staticmethod
    def _button(parent: tk.Widget, text: str, command, primary: bool = False) -> tk.Button:
        return tk.Button(parent, text=text, command=command, bg=ACCENT if primary else "#e7f0f3",
                         fg="white" if primary else INK, activebackground="#006b66" if primary else "#d9e8ed",
                         activeforeground="white" if primary else INK, relief="flat", borderwidth=0,
                         padx=15, pady=9, cursor="hand2", font=("Segoe UI", 10, "bold"))

    def new_game(self) -> None:
        self.board = Board(*LEVELS[self.level.get()], seed=self.seed)
        self.cell_size = {5: 64, 9: 47, 16: 28}[self.board.rows]
        self.margin = 24
        self.canvas.configure(width=self.margin + self.board.cols * self.cell_size + 3,
                              height=self.margin + self.board.rows * self.cell_size + 3)
        self.started_at, self.elapsed = None, 0
        self.time_text.set("00:00")
        self.flag_mode.set(False)
        self._clear_hint()
        self._render()

    def _clear_hint(self) -> None:
        self.hint = None
        self.hint_title.set("Your move")
        self.hint_body.set("Open a tile to begin. Your first move is safe. Ask for a hint to see a deduction or an estimated-risk guess.")
        self.move_text.set("")
        self.apply_button.configure(state="disabled", text="Play highlighted move")

    def _event_cell(self, event) -> Cell | None:
        c, r = (event.x - self.margin) // self.cell_size, (event.y - self.margin) // self.cell_size
        return (r, c) if 0 <= r < self.board.rows and 0 <= c < self.board.cols else None

    def _left_click(self, event) -> None:
        cell = self._event_cell(event)
        if cell is not None:
            self.flag_cell(cell) if self.flag_mode.get() else self.open_cell(cell)

    def _right_click(self, event) -> str:
        cell = self._event_cell(event)
        if cell is not None:
            self.flag_cell(cell)
        return "break"

    def open_cell(self, cell: Cell) -> None:
        changed = self.board.reveal(cell)
        if not changed:
            return
        if self.started_at is None:
            self.started_at = time.monotonic()
        self.elapsed = int(time.monotonic() - self.started_at)
        self._clear_hint()
        self._render()

    def flag_cell(self, cell: Cell) -> None:
        if self.board.toggle_flag(cell):
            self._clear_hint()
            self._render()

    def show_hint(self) -> None:
        self.hint = choose_hint(self.board.snapshot())
        self.hint_title.set(self.hint.title)
        self.hint_body.set(self.hint.explanation)
        self.move_text.set(f"{self.hint.action.upper()}: {label(self.hint.cell)}" if self.hint.cell is not None else "")
        self.apply_button.configure(state="normal" if self.hint.cell is not None else "disabled",
                                    text="Play guess (may lose)" if self.hint.action == "guess" else "Play highlighted move")
        self._draw_board()

    def apply_hint(self) -> None:
        if self.hint is None or self.hint.cell is None:
            return
        action, cell = self.hint.action, self.hint.cell
        if action in {"flag", "unflag"}:
            self.flag_cell(cell)
        elif action in {"open", "guess"}:
            self.open_cell(cell)

    def _render(self) -> None:
        self.status_text.set({"ready": "Ready", "playing": "Playing", "won": "You won!", "lost": "Mine hit"}[self.board.status])
        self.safe_text.set(f"{len(self.board.revealed)} / {self.board.safe_total}")
        self.flag_text.set(f"{len(self.board.flags)} / {self.board.mine_count}")
        self.hint_button.configure(state="disabled" if self.board.finished else "normal")
        self.bfs_text.set(f"Last opening: {self.board.last_reveal_count} safe cell(s).\nAn empty tile expands through its zero region and reveals the numbered boundary.")
        if self.board.finished:
            self.hint_title.set("Board cleared!" if self.board.status == "won" else "A mine was opened")
            self.hint_body.set("All safe cells are open. Start a new game to try another board." if self.board.status == "won" else "Mines are now visible. An X marks an incorrect flag. Start a new game to try again.")
        elif self.board.status == "playing":
            self.hint_body.set("Use the numbers to count neighboring mines. Hints use only visible clues; your flags are not assumed to be correct.")
        self._draw_board()

    def _draw_board(self) -> None:
        canvas, size, margin = self.canvas, self.cell_size, self.margin
        canvas.delete("all")
        for i in range(self.board.cols):
            canvas.create_text(margin + (i + .5) * size, 10, text=i + 1, fill=MUTED, font=("Segoe UI", 8))
        for r in range(self.board.rows):
            canvas.create_text(10, margin + (r + .5) * size, text=r + 1, fill=MUTED, font=("Segoe UI", 8))
            for c in range(self.board.cols):
                cell = (r, c)
                x, y = margin + c * size, margin + r * size
                cx, cy = x + size / 2, y + size / 2
                opened = cell in self.board.revealed
                mine = self.board.mine_after_game(cell)
                flagged = cell in self.board.flags
                fill = "#e0e9ee" if opened else "#28485f"
                if cell == self.board.exploded:
                    fill = "#cb4a55"
                elif mine and self.board.finished:
                    fill = "#afc7d2"
                canvas.create_rectangle(x + 2, y + 2, x + size - 1, y + size - 1, fill=fill, outline="")
                if flagged:
                    color = "#078579" if self.board.finished and mine else "#ffc96b"
                    canvas.create_line(cx - 5, cy - 9, cx - 5, cy + 9, fill=color, width=2)
                    canvas.create_line(cx - 10, cy + 9, cx + 4, cy + 9, fill=color, width=2)
                    canvas.create_polygon(cx - 4, cy - 9, cx + 9, cy - 4, cx - 4, cy + 1, fill=color)
                    if self.board.finished and not mine:
                        canvas.create_text(cx + 4, cy + 3, text="X", fill="#ff9c9c", font=("Segoe UI", 13, "bold"))
                elif mine:
                    radius = max(4, size * .14)
                    canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill=INK, outline=INK)
                    for dx, dy in ((1, 0), (0, 1), (.7, .7), (.7, -.7)):
                        canvas.create_line(cx - dx * radius * 1.6, cy - dy * radius * 1.6, cx + dx * radius * 1.6, cy + dy * radius * 1.6, fill=INK, width=2)
                elif opened:
                    value = self.board.visible_value(cell)
                    if value:
                        canvas.create_text(cx, cy, text=value, fill=NUMBER_COLORS[value], font=("Segoe UI", max(12, int(size * .40)), "bold"))
                if self.hint and self.hint.cell == cell:
                    canvas.create_rectangle(x + 2, y + 2, x + size - 1, y + size - 1, outline="#e7a82c", width=3)

    def _tick(self) -> None:
        if self.started_at is not None and not self.board.finished:
            self.elapsed = int(time.monotonic() - self.started_at)
        self.time_text.set(f"{self.elapsed // 60:02d}:{self.elapsed % 60:02d}")
        self._timer_id = self.root.after(200, self._tick)

    def close(self) -> None:
        if self._timer_id is not None:
            self.root.after_cancel(self._timer_id)
            self._timer_id = None
        self.root.destroy()


def main() -> None:
    parser = argparse.ArgumentParser(description="Minesweeper with BFS and explainable hints")
    parser.add_argument("--level", type=int, choices=(5, 9, 16), default=9)
    parser.add_argument("--seed", type=int, default=None, help="Repeat a board using the same first click; omit for random games.")
    args = parser.parse_args()
    root = tk.Tk()
    MinesweeperApp(root, args.level, args.seed)
    root.mainloop()


if __name__ == "__main__":
    main()
