"""
1DGR Matching Algorithm UI
Opens on the Match Results page (toggle between Candidate and Company view)
"Candidate Info" and "Job Info" buttons open in new windows

Run with:
    python ui_main.py
    or 
    python3 ui_main.py
"""

import tkinter as tk
from tkinter import ttk

# STYLE CONSTANTS — light theme matching the 1DGR site (white cards,
# serif headlines, muted gray body text, soft blue accent chips)
BG            = "#ffffff"
PANEL         = "#f7f7f8"   # light gray for alt table rows / card fill
BORDER        = "#e3e3e7"   # hairline borders on buttons/cards
HOVER_BG      = "#f3f4f6"   # subtle hover state for plain buttons
TEXT          = "#17171a"   # near-black body/heading text
SUBTEXT       = "#6b7280"   # gray metadata text
ACCENT        = "#4f5bd5"   # blue-violet accent (links, active state text)
ACCENT_BG     = "#eaf0ff"   # pale accent fill, like the site's "BETA" chip
ACCENT_BORDER = "#c7d2fb"   # border for the active/selected chip
ENTRY_BG      = "#ffffff"

FONT_SERIF = "Georgia"   # headline typeface, like the site's serif logo/titles
FONT_SANS  = "Helvetica"  # body/metadata typeface

FONT_H1    = (FONT_SERIF, 22)
FONT_H2    = (FONT_SERIF, 16)
FONT_BODY  = (FONT_SANS, 12)
FONT_SMALL = (FONT_SANS, 10)
FONT_TABLE_HEADING = (FONT_SANS, 11, "bold")


def make_button(parent, text, command, active=False):
    """Bordered chip button, like the site's filter/tab controls.
    'active' switches to a pale accent fill so a toggle can show
    which view is currently selected."""
    bg = ACCENT_BG if active else BG
    border_color = ACCENT_BORDER if active else BORDER
    fg = ACCENT if active else TEXT

    frame = tk.Frame(parent, bg=bg,
                      highlightthickness=1,
                      highlightbackground=border_color,
                      highlightcolor=border_color)
    lbl = tk.Label(frame, text=text, bg=bg, fg=fg,
                   font=FONT_BODY, padx=16, pady=10, anchor="center")
    lbl.pack(fill="both", expand=True)

    def _click(e):
        command()

    def _enter(e):
        hover_bg = ACCENT_BG if active else HOVER_BG
        lbl.configure(bg=hover_bg)
        frame.configure(bg=hover_bg)

    def _leave(e):
        rest_bg = ACCENT_BG if active else BG
        lbl.configure(bg=rest_bg)
        frame.configure(bg=rest_bg)

    for w in (frame, lbl):
        w.bind("<Button-1>", _click)
        w.bind("<Enter>", _enter)
        w.bind("<Leave>", _leave)
    return frame


def apply_treeview_style():
    """Light theme for all Treeview widgets, matching the site's tables."""
    s = ttk.Style()
    s.theme_use("clam")
    s.configure("Treeview",
                background=BG, foreground=TEXT,
                fieldbackground=BG, rowheight=30, font=FONT_BODY,
                borderwidth=0)
    s.configure("Treeview.Heading",
                background=PANEL, foreground=TEXT,
                font=FONT_TABLE_HEADING, relief="flat")
    s.map("Treeview", background=[("selected", ACCENT_BG)],
          foreground=[("selected", TEXT)])
    s.configure("TCombobox", fieldbackground=BG, background=BG,
                foreground=TEXT, arrowcolor=TEXT)


def make_tree(parent, columns, height=10):
    """columns = list of (col_id, heading, width)"""
    col_ids = [c[0] for c in columns]
    tree = ttk.Treeview(parent, columns=col_ids, show="headings", height=height)
    tree.tag_configure("odd", background=PANEL)
    tree.tag_configure("even", background=BG)
    for col_id, heading, width in columns:
        tree.heading(col_id, text=heading)
        tree.column(col_id, width=width, minwidth=60)

    wrap = tk.Frame(parent, bg=BG)
    sb = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    return wrap, tree


def center(win, w, h):
    win.update_idletasks()
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")


# PLACEHOLDER / HARDCODED SAMPLE DATA
# Every candidate has their own ranked list of jobs, and every job posting
# has its own ranked list of candidates — so each is keyed by who/what
# you're viewing results for. Replace with real scoring + imported
# profiles later; the dropdown + lookup pattern below can stay the same.
CANDIDATE_NAMES = ["Jordan Price", "Riley Chen", "Sam Okafor"]

JOB_POSTINGS = [
    "Software Engineer I — Acme Robotics",
    "Data Analyst — Northfield Health",
]

# candidate name -> top 5 job matches for THAT candidate
# (rank, job_title, company, match_pct)
SAMPLE_JOB_MATCHES_BY_CANDIDATE = {
    "Jordan Price": [
        (1, "Software Engineer I", "Acme Robotics",      94),
        (2, "Backend Developer",   "Lumen Logistics",    88),
        (3, "Data Analyst",        "Northfield Health",  81),
        (4, "Product Analyst",     "BrightPath Finance", 76),
        (5, "Junior Developer",    "Maple Retail Co.",   70),
    ],
    "Riley Chen": [
        (1, "Data Analyst",        "Northfield Health",  90),
        (2, "Product Analyst",     "BrightPath Finance", 85),
        (3, "Software Engineer I", "Acme Robotics",      79),
        (4, "Backend Developer",   "Lumen Logistics",    74),
        (5, "Junior Developer",    "Maple Retail Co.",   68),
    ],
    "Sam Okafor": [
        (1, "Backend Developer",   "Lumen Logistics",    91),
        (2, "Software Engineer I", "Acme Robotics",      86),
        (3, "Junior Developer",    "Maple Retail Co.",   80),
        (4, "Data Analyst",        "Northfield Health",  72),
        (5, "Product Analyst",     "BrightPath Finance", 65),
    ],
}

# job posting -> top 5 candidate matches for THAT posting
# (rank, candidate_name, target_role, match_pct)
SAMPLE_CANDIDATE_MATCHES_BY_JOB = {
    "Software Engineer I — Acme Robotics": [
        (1, "Jordan Price",   "Software Engineer I", 94),
        (2, "Riley Chen",     "Software Engineer I", 88),
        (3, "Sam Okafor",     "Software Engineer I", 83),
        (4, "Casey Nguyen",   "Software Engineer I", 79),
        (5, "Morgan Blake",   "Software Engineer I", 74),
    ],
    "Data Analyst — Northfield Health": [
        (1, "Riley Chen",     "Data Analyst", 92),
        (2, "Jordan Price",   "Data Analyst", 84),
        (3, "Morgan Blake",   "Data Analyst", 78),
        (4, "Sam Okafor",     "Data Analyst", 71),
        (5, "Casey Nguyen",   "Data Analyst", 66),
    ],
}


# MAIN WINDOW — Match Results page (opens first)
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("1DGR Matching Algorithm")
        self.configure(bg=BG)
        self.resizable(False, False)
        apply_treeview_style()
        center(self, 620, 560)

        self._view = "candidate"  # which results table is showing
        self._selected_candidate = tk.StringVar(value=CANDIDATE_NAMES[0])
        self._selected_job = tk.StringVar(value=JOB_POSTINGS[0])
        self._build()
        self._render_results()

    # Layout
    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=BG, pady=18)
        hdr.pack(fill="x")
        tk.Label(hdr, text="1DGR Match Results",
                 font=FONT_H1, bg=BG, fg=TEXT).pack()
        tk.Label(hdr, text="CS 5351 Senior Design  •  Matching Algorithm",
                 font=FONT_SMALL, bg=BG, fg=SUBTEXT).pack(pady=(4, 0))
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # Top nav — always-visible info-page buttons
        nav = tk.Frame(self, bg=BG, padx=20, pady=14)
        nav.pack(fill="x")
        make_button(nav, "Candidate Info",
                    lambda: CandidateInfoWindow(self)).pack(side="left", expand=True,
                                                             fill="x", padx=(0, 6))
        make_button(nav, "Job Info",
                    lambda: JobInfoWindow(self)).pack(side="left", expand=True,
                                                       fill="x", padx=(6, 0))

        # Toggle between candidate-view and company-view results
        self._toggle_row = tk.Frame(self, bg=BG, padx=20)
        self._toggle_row.pack(fill="x")
        self._rebuild_toggle()

        # Results body
        body = tk.Frame(self, bg=BG, padx=20, pady=16)
        body.pack(fill="both", expand=True)

        self._results_title = tk.StringVar()
        tk.Label(body, textvariable=self._results_title, font=FONT_H2,
                 bg=BG, fg=ACCENT, anchor="w").pack(fill="x", pady=(0, 4))

        self._results_subtitle = tk.StringVar()
        tk.Label(body, textvariable=self._results_subtitle, font=FONT_SMALL,
                 bg=BG, fg=SUBTEXT, anchor="w").pack(fill="x", pady=(0, 10))

        self._table_slot = tk.Frame(body, bg=BG)
        self._table_slot.pack(fill="both", expand=True)

        tk.Label(self, text="Match % shown is hardcoded sample data — "
                            "the scoring engine isn't wired in yet.",
                 font=FONT_SMALL, bg=BG, fg=SUBTEXT).pack(pady=(0, 10))

    # Toggle logic
    def _set_view(self, view):
        if view == self._view:
            return
        self._view = view
        self._rebuild_toggle()
        self._render_results()

    def _rebuild_toggle(self):
        # Rebuild both buttons so only the active one shows the "pressed" color
        for child in self._toggle_row.winfo_children():
            child.destroy()
        btn_candidate = make_button(
            self._toggle_row, "Candidate Matches",
            lambda: self._set_view("candidate"),
            active=(self._view == "candidate"))
        btn_company = make_button(
            self._toggle_row, "Job Matches",
            lambda: self._set_view("company"),
            active=(self._view == "company"))
        btn_candidate.pack(side="left", expand=True, fill="x", padx=(0, 6))
        btn_company.pack(side="left", expand=True, fill="x", padx=(6, 0))

    def _render_results(self):
        for w in self._table_slot.winfo_children():
            w.destroy()

        if self._view == "candidate":
            self._results_title.set("Top 5 Job Matches")
            self._results_subtitle.set("Ranked jobs for the selected candidate.")
            selector_label = "Candidate:"
            options = CANDIDATE_NAMES
            selector_var = self._selected_candidate
            if selector_var.get() not in options:
                selector_var.set(options[0])
            rows = SAMPLE_JOB_MATCHES_BY_CANDIDATE[selector_var.get()]
            columns = [
                ("rank", "Rank", 50),
                ("job_title", "Job Title", 220),
                ("company", "Company", 180),
                ("match_pct", "Match %", 80),
            ]
        else:
            self._results_title.set("Top 5 Candidate Matches")
            self._results_subtitle.set("Ranked candidates for the selected job posting.")
            selector_label = "Job posting:"
            options = JOB_POSTINGS
            selector_var = self._selected_job
            if selector_var.get() not in options:
                selector_var.set(options[0])
            rows = SAMPLE_CANDIDATE_MATCHES_BY_JOB[selector_var.get()]
            columns = [
                ("rank", "Rank", 50),
                ("candidate_name", "Candidate", 180),
                ("target_role", "Target Role", 220),
                ("match_pct", "Match %", 80),
            ]

        # Selector row — picks whose ranked list is being shown, since the
        # top-5 list is different for every candidate and every job posting.
        selector_row = tk.Frame(self._table_slot, bg=BG)
        selector_row.pack(fill="x", pady=(0, 10))
        tk.Label(selector_row, text=selector_label, font=FONT_BODY,
                 bg=BG, fg=TEXT).pack(side="left", padx=(0, 8))
        combo = ttk.Combobox(selector_row, textvariable=selector_var,
                              values=options, state="readonly",
                              font=FONT_BODY, width=32)
        combo.pack(side="left")
        combo.bind("<<ComboboxSelected>>", lambda e: self._render_results())

        wrap, tree = make_tree(self._table_slot, columns, height=8)
        wrap.pack(fill="both", expand=True)
        for i, row in enumerate(rows):
            tag = "odd" if i % 2 else "even"
            rank, a, b, pct = row
            tree.insert("", "end", tags=(tag,), values=(rank, a, b, f"{pct}%"))


# CANDIDATE INFO WINDOW — table of all candidate fields (empty, imported later)
class CandidateInfoWindow(tk.Toplevel):
    COLUMNS = [
        ("name", "Name", 140),
        ("target_roles", "Target Roles", 140),
        ("industry_interests", "Industry Interests", 140),
        ("location", "Location", 110),
        ("open_to_work", "Open to Work", 100),
        ("hard_skills", "Hard/Soft Skills", 160),
        ("education", "Education", 160),
        ("certifications", "Certifications", 140),
        ("languages", "Languages", 110),
        ("willing_to_relocate", "Willing to Relocate", 130),
        ("pay_range", "Pay Range", 110),
        ("availability", "Availability", 110),
    ]

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Candidate Info")
        self.configure(bg=BG)
        self.resizable(True, True)
        center(self, 820, 420)
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=BG, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Candidate Info", font=FONT_H2,
                 bg=BG, fg=TEXT).pack()
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        body = tk.Frame(self, bg=BG, padx=16, pady=14)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="No candidate profiles imported yet — "
                            "this table will populate once profile data is loaded.",
                 font=FONT_SMALL, bg=BG, fg=SUBTEXT, anchor="w",
                 wraplength=760, justify="left").pack(fill="x", pady=(0, 10))

        wrap, tree = make_tree(body, self.COLUMNS, height=12)
        wrap.pack(fill="both", expand=True)
        # No rows inserted — headers only, ready for imported data.


# JOB INFO WINDOW — table of all company/job fields (empty, imported later)
class JobInfoWindow(tk.Toplevel):
    COLUMNS = [
        ("company_name", "Company Name", 150),
        ("industry", "Industry", 120),
        ("job_title", "Job Title", 160),
        ("required_skills", "Required Skills", 160),
        ("degree_requirement", "Degree Requirement", 140),
        ("location", "Location", 110),
        ("work_type", "Work Type", 110),
        ("pay_range", "Pay Range", 110),
        ("seniority_level", "Seniority Level", 120),
        ("time_to_fill", "Time to Fill", 110),
    ]

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Job Info")
        self.configure(bg=BG)
        self.resizable(True, True)
        center(self, 820, 420)
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=BG, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Job Info", font=FONT_H2,
                 bg=BG, fg=TEXT).pack()
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        body = tk.Frame(self, bg=BG, padx=16, pady=14)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="No company/job postings imported yet — "
                            "this table will populate once profile data is loaded.",
                 font=FONT_SMALL, bg=BG, fg=SUBTEXT, anchor="w",
                 wraplength=760, justify="left").pack(fill="x", pady=(0, 10))

        wrap, tree = make_tree(body, self.COLUMNS, height=12)
        wrap.pack(fill="both", expand=True)
        # No rows inserted — headers only, ready for imported data.


# Entry point
if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
