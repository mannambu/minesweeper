"""Optional GUI integration check: python gui_smoke.py (requires a display).

Exercises our own Tk callbacks and checks that widgets fit their allocated space.
It does not replace a manual visual review on another operating system.
"""

import tkinter as tk

from engine import Board
from main import LEVELS, MinesweeperApp


def check_layout(widget):
    for child in widget.winfo_children():
        if isinstance(child, (tk.Label, tk.Button, tk.Checkbutton)):
            assert child.winfo_ismapped(), f"Unmapped widget: {child.cget('text')}"
            assert child.winfo_height() >= child.winfo_reqheight(), f"Clipped height: {child}"
        check_layout(child)


def run():
    root = tk.Tk()
    app = MinesweeperApp(root, seed=42)
    try:
        for name, (rows, cols, mines) in LEVELS.items():
            app.level.set(name)
            app.new_game()
            root.update()
            assert app.board.status == "ready"
            app.hint_button.invoke()
            assert app.hint.action == "open"
            app.apply_button.invoke()
            root.update()
            assert app.board.status != "lost"
            assert app.board.revealed
            assert app.started_at is not None
            if not app.board.finished:
                app.hint_button.invoke()
                root.update()
                assert app.hint.cell is not None
            check_layout(root)
            print(f"PASS: {rows}x{cols} controls, hint, first move, layout")

        app.level.set(next(iter(LEVELS)))
        app.new_game()
        app.board = Board.from_mines(5, 5, {(0, 0), (4, 4)})
        app.open_cell((1, 1))
        app.show_hint()
        assert app.hint.action == "guess"
        assert app.apply_button.cget("text") == "Play guess (may lose)"
        root.update()
        check_layout(root)
        print("PASS: uncertain hint label and full explanation layout")

        app.new_game()
        app.board = Board.from_mines(5, 5, {(0, 0)})
        app._render()
        app.flag_cell((0, 4))
        app.open_cell((4, 4))
        assert app.board.status == "playing"
        app.show_hint()
        assert app.hint.action == "unflag"
        app.apply_hint()
        app.open_cell((0, 4))
        assert app.board.status == "won"
        root.update()
        check_layout(root)
        assert app.hint_button.cget("state") == "disabled"
        print("PASS: safe flag correction and victory")

        app.new_button.invoke()
        app.board = Board.from_mines(5, 5, {(0, 0)})
        app._render()
        app.open_cell((0, 0))
        assert app.board.status == "lost"
        root.update()
        check_layout(root)
        assert app.hint_button.cget("state") == "disabled"
        app.new_button.invoke()
        assert app.board.status == "ready"
        assert app.started_at is None
        assert app.hint is None
        assert app.time_text.get() == "00:00"
        print("PASS: loss, input lock, and reset")
        print(f"Tk window requested size: {root.winfo_reqwidth()}x{root.winfo_reqheight()}")
    finally:
        app.close()


if __name__ == "__main__":
    run()
