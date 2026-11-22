"""Variant Designer: design, preview, test, play and release a variant
without writing any code.

Start it with design.command / design.bat / ./design.sh, or
`python3 design.py [variant.json]`.

    left   a form: name, board, speed, which pieces
    right  live preview: chance of each difficulty class, average holes,
           every piece that can appear, and any problems with the variant
    top    Play, Robot playtest, Release, Save
"""
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import geometry as g
from .mixes import MODES
from .pieces import DIFFICULTY_CLASSES, ExTetromino
from .playtest import playtest, summary
from .release import build_release
from .variant import MODE_NAMES, Variant
from .window import CLASS_COLOURS, GameWindow

GROUPS = ["classic"] + [c.__name__ for c in DIFFICULTY_CLASSES]
GROUP_LABELS = {"classic": "Classic 7 (I O T S Z L Γ)"}
STAGE_CHOICES = ["(none)"] + list(MODES) + ["my mix"]
MAX_STAGES = 4

HELP_TEXT = """1. Give your variant a name.
2. Choose the board size and speed.
3. Choose the pieces:
   - Ready-made mode: pick one from the list.
   - My own mix: drag the sliders. Each slider is a share;
     they don't need to add up to 100.
   - Gets harder: pick up to 4 stages ("my mix" uses the
     sliders) and how many lines each stage lasts.
4. Watch the preview on the right: chances, difficulty,
   and every piece that can appear.
5. Play it, or let the robot playtest it.
6. Save it (a .json file you can open again), and
   Release it as a zip anyone can unzip and double-click."""


def difficulty_word(holes):
    if holes < 0.35:
        return "like classic Tetris"
    if holes < 0.8:
        return "easy"
    if holes < 1.3:
        return "medium"
    if holes < 1.8:
        return "hard"
    return "very hard"


class VariantDesigner:
    """The designer window. `variant` and `path` are optional starting points."""

    def __init__(self, variant=None, path=None, master=None):
        self.root = master or tk.Tk()
        self.root.minsize(900, 640)
        self.variant = variant or Variant()
        self.path = Path(path) if path else None
        self.dirty = False
        self._building = True
        self.extra_weights = {}      # mix shares the sliders can't show
        self.current_probabilities = {}

        self._make_vars()
        self._build_menu()
        self._build_layout()
        self._load_into_form(self.variant)
        self._building = False
        self.refresh()
        self.root.protocol("WM_DELETE_WINDOW", self.quit)

    def run(self):
        """Show the designer until it is closed."""
        self.root.mainloop()

    # --- form state -------------------------------------------------------------------
    def _make_vars(self):
        r = self.root
        self.v = {k: tk.StringVar(r) for k in (
            "name", "author", "width", "height", "start_delay_ms", "speedup_every",
            "faster_pct", "min_delay_ms", "cell_size", "kind", "mode", "every_lines")}
        self.shares = {k: tk.DoubleVar(r, value=0) for k in GROUPS}
        self.stages = [tk.StringVar(r, value="(none)") for _ in range(MAX_STAGES)]
        self.preview_lines = tk.DoubleVar(r, value=0)
        for var in list(self.v.values()) + list(self.shares.values()) + self.stages:
            var.trace_add("write", self._changed)
        self.preview_lines.trace_add("write", lambda *a: self._draw_preview())

    def _changed(self, *args):
        if self._building:
            return
        self.dirty = True
        self.refresh()

    @staticmethod
    def _num(text, kind=int):
        """A number from a form field, or the raw text (so checking reports it)."""
        try:
            return kind(str(text).strip())
        except ValueError:
            return str(text)

    def _my_mix(self):
        weights = {k: round(var.get()) for k, var in self.shares.items()
                   if round(var.get()) > 0}
        weights.update(self.extra_weights)
        return weights

    def form_to_variant(self):
        """Build a Variant from what's in the form now."""
        v, num = self.v, self._num
        pct = num(v["faster_pct"].get(), float)
        factor = round(1 - pct / 100, 4) if isinstance(pct, float) else pct
        kind = v["kind"].get()
        if kind == "mode":
            pieces = {"kind": "mode", "mode": v["mode"].get()}
        elif kind == "mix":
            pieces = {"kind": "mix", "weights": self._my_mix()}
        else:
            stages = []
            for s in self.stages:
                choice = s.get()
                if choice == "my mix":
                    stages.append(self._my_mix())
                elif choice != "(none)":
                    stages.append(choice)
            pieces = {"kind": "progressive", "stages": stages,
                      "every_lines": num(v["every_lines"].get())}
        return Variant({
            "name": v["name"].get(),
            "author": v["author"].get(),
            "description": self.description.get("1.0", "end").strip(),
            "board": {"width": num(v["width"].get()), "height": num(v["height"].get())},
            "speed": {"start_delay_ms": num(v["start_delay_ms"].get()),
                      "speedup_every": num(v["speedup_every"].get()),
                      "speedup_factor": factor,
                      "min_delay_ms": num(v["min_delay_ms"].get())},
            "pieces": pieces,
            "window": {"cell_size": num(v["cell_size"].get())},
        })

    def _set_shares(self, weights):
        self.extra_weights = {}
        for var in self.shares.values():
            var.set(0)
        for key, w in (weights or {}).items():
            k = key.__name__ if isinstance(key, type) else key
            if k in self.shares:
                self.shares[k].set(w)
            else:
                self.extra_weights[k] = w

    def _load_into_form(self, variant):
        self._building = True
        d = variant.data
        v = self.v
        v["name"].set(d["name"])
        v["author"].set(d.get("author", ""))
        self.description.delete("1.0", "end")
        self.description.insert("1.0", d.get("description", ""))
        v["width"].set(d["board"]["width"])
        v["height"].set(d["board"]["height"])
        s = d["speed"]
        v["start_delay_ms"].set(s["start_delay_ms"])
        v["speedup_every"].set(s["speedup_every"])
        factor = s["speedup_factor"]
        v["faster_pct"].set(round((1 - factor) * 100) if isinstance(factor, (int, float))
                            else factor)
        v["min_delay_ms"].set(s["min_delay_ms"])
        v["cell_size"].set(d["window"]["cell_size"])
        p = d["pieces"]
        kind = p.get("kind", "mode")
        v["kind"].set(kind)
        v["mode"].set(p.get("mode", "progressive"))
        v["every_lines"].set(p.get("every_lines", 10))
        self._set_shares(p.get("weights") if kind == "mix" else {"classic": 70, "OneHole": 30})
        for var in self.stages:
            var.set("(none)")
        if kind == "progressive":
            used_mix = False
            for var, stage in zip(self.stages, p.get("stages", [])):
                if isinstance(stage, str):
                    var.set(stage)
                elif not used_mix:
                    self._set_shares(stage)
                    var.set("my mix")
                    used_mix = True
        else:
            self.stages[0].set("classic")
            self.stages[1].set("easy")
            self.stages[2].set("normal")
            self.stages[3].set("hard")
        self._building = False
        self.dirty = False

    # --- layout ---------------------------------------------------------------------
    def _build_menu(self):
        bar = tk.Menu(self.root)
        f = tk.Menu(bar, tearoff=False)
        f.add_command(label="New", command=self.new, accelerator="Ctrl+N")
        f.add_command(label="Open…", command=self.open, accelerator="Ctrl+O")
        f.add_command(label="Save", command=self.save, accelerator="Ctrl+S")
        f.add_command(label="Save As…", command=self.save_as)
        f.add_separator()
        f.add_command(label="Release…", command=self.release)
        f.add_separator()
        f.add_command(label="Quit", command=self.quit)
        bar.add_cascade(label="File", menu=f)
        h = tk.Menu(bar, tearoff=False)
        h.add_command(label="How to use", command=lambda: messagebox.showinfo(
            "How to use the Variant Designer", HELP_TEXT, parent=self.root))
        bar.add_cascade(label="Help", menu=h)
        self.root.config(menu=bar)
        for key, fn in (("n", self.new), ("o", self.open), ("s", self.save)):
            self.root.bind(f"<Control-{key}>", lambda e, fn=fn: fn())
            self.root.bind(f"<Command-{key}>", lambda e, fn=fn: fn())

    def _build_layout(self):
        top = ttk.Frame(self.root, padding=(10, 8))
        top.pack(fill="x")
        for text, cmd in (("Play", self.play), ("Robot playtest", self.robot_test),
                          ("Release…", self.release), ("Save", self.save)):
            ttk.Button(top, text=text, command=cmd).pack(side="left", padx=(0, 6))

        body = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        body.pack(fill="both", expand=True)
        left = ttk.Frame(body)
        left.pack(side="left", fill="y")
        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True, padx=(12, 0))
        self._build_form(left)
        self._build_preview(right)

    def _row(self, parent, label, widget_maker, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=2)
        w = widget_maker(parent)
        w.grid(row=row, column=1, sticky="we", pady=2, padx=(6, 0))
        return w

    def _spin(self, var, lo, hi, step=1):
        return lambda p: ttk.Spinbox(p, from_=lo, to=hi, increment=step,
                                     textvariable=var, width=8)

    def _build_form(self, parent):
        about = ttk.LabelFrame(parent, text="About", padding=8)
        about.pack(fill="x")
        self._row(about, "Name", lambda p: ttk.Entry(p, textvariable=self.v["name"], width=28), 0)
        self._row(about, "Author", lambda p: ttk.Entry(p, textvariable=self.v["author"], width=28), 1)
        ttk.Label(about, text="Description").grid(row=2, column=0, sticky="nw", pady=2)
        self.description = tk.Text(about, width=30, height=3, wrap="word")
        self.description.grid(row=2, column=1, sticky="we", pady=2, padx=(6, 0))
        self.description.bind("<KeyRelease>", lambda e: self._changed())

        board = ttk.LabelFrame(parent, text="Board and speed", padding=8)
        board.pack(fill="x", pady=(8, 0))
        rows = [("Width (squares)", "width", 4, 40, 1),
                ("Height (squares)", "height", 4, 40, 1),
                ("Starting fall delay (ms)", "start_delay_ms", 50, 5000, 50),
                ("Speed up every … lines", "speedup_every", 1, 1000, 1),
                ("Each speed-up: % faster", "faster_pct", 0, 90, 1),
                ("Fastest fall delay (ms)", "min_delay_ms", 10, 5000, 10),
                ("Square size (pixels)", "cell_size", 10, 60, 1)]
        for n, (label, key, lo, hi, step) in enumerate(rows):
            self._row(board, label, self._spin(self.v[key], lo, hi, step), n)

        pieces = ttk.LabelFrame(parent, text="Pieces", padding=8)
        pieces.pack(fill="x", pady=(8, 0))
        for text, value in (("Ready-made mode", "mode"), ("My own mix", "mix"),
                            ("Gets harder as lines are cleared", "progressive")):
            ttk.Radiobutton(pieces, text=text, value=value,
                            variable=self.v["kind"]).pack(anchor="w")

        self.mode_frame = ttk.Frame(pieces, padding=(18, 4, 0, 0))
        ttk.Combobox(self.mode_frame, state="readonly", values=MODE_NAMES,
                     textvariable=self.v["mode"], width=14).pack(anchor="w")

        self.mix_frame = ttk.Frame(pieces, padding=(18, 4, 0, 0))
        self.share_labels = []
        for n, key in enumerate(GROUPS):
            ttk.Label(self.mix_frame, text=GROUP_LABELS.get(key, key)).grid(
                row=n, column=0, sticky="w")
            ttk.Scale(self.mix_frame, from_=0, to=100, variable=self.shares[key],
                      length=130).grid(row=n, column=1, padx=4)
            value_label = ttk.Label(self.mix_frame, width=4)
            value_label.grid(row=n, column=2)
            self.share_labels.append(value_label)
        self.extra_label = ttk.Label(self.mix_frame, foreground="#555", wraplength=260)
        self.extra_label.grid(row=len(GROUPS), column=0, columnspan=3, sticky="w")

        self.prog_frame = ttk.Frame(pieces, padding=(18, 4, 0, 0))
        for n, var in enumerate(self.stages):
            ttk.Label(self.prog_frame, text=f"Stage {n + 1}").grid(row=n, column=0, sticky="w")
            ttk.Combobox(self.prog_frame, state="readonly", values=STAGE_CHOICES,
                         textvariable=var, width=12).grid(row=n, column=1, sticky="w", pady=1)
        ttk.Label(self.prog_frame, text="Each stage lasts (lines)").grid(
            row=MAX_STAGES, column=0, sticky="w", pady=(4, 0))
        ttk.Spinbox(self.prog_frame, from_=1, to=500, textvariable=self.v["every_lines"],
                    width=6).grid(row=MAX_STAGES, column=1, sticky="w", pady=(4, 0))
        ttk.Label(self.prog_frame, text='"my mix" uses the sliders of "My own mix".',
                  foreground="#555").grid(row=MAX_STAGES + 1, column=0, columnspan=2,
                                          sticky="w")

    def _build_preview(self, parent):
        head = ttk.Frame(parent)
        head.pack(fill="x")
        ttk.Label(head, text="Preview", font=("Helvetica", 14, "bold")).pack(side="left")
        self.lines_box = ttk.Frame(head)
        ttk.Label(self.lines_box, text="   chances after").pack(side="left")
        self.lines_scale = ttk.Scale(self.lines_box, from_=0, to=40, length=140,
                                     variable=self.preview_lines)
        self.lines_scale.pack(side="left")
        self.lines_label = ttk.Label(self.lines_box, width=10)
        self.lines_label.pack(side="left")

        self.chart = tk.Canvas(parent, height=170, bg="white", highlightthickness=0)
        self.chart.pack(fill="x", pady=(6, 0))
        self.difficulty = ttk.Label(parent, font=("Helvetica", 12))
        self.difficulty.pack(anchor="w", pady=(4, 6))
        ttk.Label(parent, text="Pieces that can appear (chance of each):").pack(anchor="w")
        self.gallery = tk.Canvas(parent, height=300, bg="white", highlightthickness=0)
        self.gallery.pack(fill="both", expand=True, pady=(4, 6))
        self.problem_box = tk.Label(parent, justify="left", anchor="w", wraplength=520,
                                    font=("Helvetica", 12))
        self.problem_box.pack(fill="x")

    # --- refreshing -------------------------------------------------------------------
    def refresh(self):
        """Re-read the form, re-check the variant and redraw the preview."""
        kind = self.v["kind"].get()
        for frame, k in ((self.mode_frame, "mode"), (self.mix_frame, "mix"),
                         (self.prog_frame, "progressive")):
            if k == kind:
                frame.pack(fill="x")
            else:
                frame.pack_forget()
        for label, key in zip(self.share_labels, GROUPS):
            label.config(text=str(round(self.shares[key].get())))
        self.extra_label.config(text=(
            "Also kept from the file: " + ", ".join(f"{k} {w}" for k, w in
                                                    self.extra_weights.items()))
            if self.extra_weights else "")

        self.variant = self.form_to_variant()
        problems = self.variant.problems()
        if problems:
            self.problem_box.config(fg="#c62828", text="Problems to fix:\n• " +
                                    "\n• ".join(problems))
        else:
            self.problem_box.config(fg="#2e7d32", text="✓ Ready to play, save and release.")
        starts = self.variant.stage_starts() if not problems else [0]
        if len(starts) > 1:
            self.lines_box.pack(side="left")
            self.lines_scale.config(to=max(starts) + 10)
        else:
            self.lines_box.pack_forget()
            self.preview_lines.set(0)
        name = self.variant.name or "untitled"
        self.root.title(f"ExTetris Variant Designer — {name}{' *' if self.dirty else ''}")
        self._draw_preview()

    def _draw_preview(self):
        self.chart.delete("all")
        self.gallery.delete("all")
        lines = int(round(self.preview_lines.get()))
        self.lines_label.config(text=f"{lines} lines")
        try:
            mix = self.variant.piece_mix()
            probs = mix.probabilities(lines)
            by_class = mix.probabilities_by_class(lines)
            holes = mix.expected_holes(lines)
        except ValueError:
            self.current_probabilities = {}
            self.difficulty.config(text="(fix the problems below to see the preview)")
            return
        self.current_probabilities = probs

        w = max(self.chart.winfo_width(), 420)
        bar_left, bar_max, row_h = 150, w - 210, 26
        for n, cls in enumerate(DIFFICULTY_CLASSES):
            name = cls.__name__
            share = by_class.get(name, 0.0)
            y = 8 + n * row_h
            self.chart.create_text(8, y + 10, anchor="w",
                                   text=f"{name} ({cls.SPAWN_HOLES} holes)")
            self.chart.create_rectangle(bar_left, y + 2, bar_left + max(1, share * bar_max),
                                        y + 18, fill=CLASS_COLOURS[name], outline="")
            self.chart.create_text(bar_left + share * bar_max + 6, y + 10, anchor="w",
                                   text=f"{share:.0%}")
        self.difficulty.config(text=f"Average holes per piece: {holes:.2f}  →  "
                                    f"{difficulty_word(holes)}   (classic 0.29 … all 34 pieces 1.85)")

        tile_w, tile_h, cell = 78, 62, 9
        cols = max(1, max(self.gallery.winfo_width(), 520) // tile_w)
        shown = [i for i in ExTetromino.catalogue() if i.name in probs]
        for n, info in enumerate(shown):
            x0 = (n % cols) * tile_w + 6
            y0 = (n // cols) * tile_h + 4
            turn = info.spawn_turns[0]
            for r, c in g.cells(turn):
                self.gallery.create_rectangle(x0 + c * cell, y0 + r * cell,
                                              x0 + c * cell + cell - 1, y0 + r * cell + cell - 1,
                                              fill=CLASS_COLOURS[info.piece_class.__name__],
                                              outline="")
            self.gallery.create_text(x0, y0 + 4 * cell + 4, anchor="nw",
                                     text=f"{info.name} {probs[info.name]:.0%}",
                                     font=("Helvetica", 9))
        rows = (len(shown) + cols - 1) // cols
        self.gallery.config(height=max(120, rows * tile_h + 8))

    # --- actions -------------------------------------------------------------------------
    def _require_valid(self, action):
        problems = self.variant.problems()
        if problems:
            messagebox.showerror(f"Can't {action} yet",
                                 "Fix these first:\n\n• " + "\n• ".join(problems),
                                 parent=self.root)
            return False
        return True

    def play(self):
        """Open a game window for the current variant."""
        if not self._require_valid("play"):
            return None
        top = tk.Toplevel(self.root)
        win = GameWindow(self.variant.make_game(), master=top, title=self.variant.name,
                         cell_size=self.variant.data["window"]["cell_size"])
        top.focus_force()
        return win

    def robot_test(self):
        """Let the robot play a few games and report how it went."""
        if not self._require_valid("playtest"):
            return None
        self.root.config(cursor="watch")
        self.root.update()
        try:
            report = playtest(self.variant, games=5, max_pieces=250)
        finally:
            self.root.config(cursor="")
        messagebox.showinfo("Robot playtest", summary(report) +
                            "\n\nThe same robot clears about 73 lines on classic Tetris "
                            "and about 2 with all 34 pieces, for comparison.",
                            parent=self.root)
        return report

    def _confirm_discard(self):
        if not self.dirty:
            return True
        answer = messagebox.askyesnocancel("Unsaved changes",
                                           "Save your changes first?", parent=self.root)
        if answer is None:
            return False
        return self.save() if answer else True

    def new(self):
        """Start a new variant (asks to save unsaved changes)."""
        if self._confirm_discard():
            self.path = None
            self._load_into_form(Variant())
            self.refresh()

    def _variants_dir(self):
        d = Path.cwd() / "variants"
        return str(d if d.is_dir() else Path.cwd())

    def open(self, path=None):
        """Open a variant file (asks for one if no path is given)."""
        if not self._confirm_discard():
            return
        path = path or filedialog.askopenfilename(
            parent=self.root, initialdir=self._variants_dir(),
            filetypes=[("ExTetris variants", "*.json"), ("All files", "*.*")])
        if not path:
            return
        try:
            variant = Variant.load(path)
        except (OSError, ValueError) as e:
            messagebox.showerror("Can't open", str(e), parent=self.root)
            return
        self.path = Path(path)
        self._load_into_form(variant)
        self.refresh()

    def save(self):
        """Save to the current file (asks for a name the first time)."""
        if self.path is None:
            return self.save_as()
        self.variant.save(self.path)
        self.dirty = False
        self.refresh()
        return True

    def save_as(self):
        """Save to a new file."""
        path = filedialog.asksaveasfilename(
            parent=self.root, initialdir=self._variants_dir(),
            initialfile=f"{self.variant.slug}.json", defaultextension=".json",
            filetypes=[("ExTetris variants", "*.json")])
        if not path:
            return False
        self.path = Path(path)
        return self.save()

    def release(self, out_dir=None):
        """Package the variant as a zip that anyone can unzip and play."""
        if not self._require_valid("release"):
            return None
        if out_dir is None:
            default = Path.cwd() / "releases"
            default.mkdir(exist_ok=True)
            out_dir = filedialog.askdirectory(parent=self.root, initialdir=str(default),
                                              title="Where should the release go?")
            if not out_dir:
                return None
        zip_path = build_release(self.variant, out_dir)
        messagebox.showinfo(
            "Released",
            f"Your game is ready to share:\n\n{zip_path}\n\n"
            "Whoever receives it unzips it and double-clicks play.command (macOS) "
            "or play.bat (Windows). A README describing your variant is inside.",
            parent=self.root)
        return zip_path

    def quit(self):
        """Close the designer (asks to save unsaved changes)."""
        if self._confirm_discard():
            self.root.destroy()
