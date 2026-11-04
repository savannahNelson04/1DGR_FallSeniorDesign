"""
1DGR Matching Algorithm UI
Opens on the Job <-> Candidate page. 
Three tabs across the top:
    Job <-> Candidate      pick a candidate or a job posting, press Match
    Candidate <-> Company  pick a candidate or a company, press Match
    Admin                  blank for now
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


def make_action_button(parent, text, command):
    """Solid accent button for the main action (Match)."""
    lbl = tk.Label(parent, text=text, bg=ACCENT, fg="#ffffff",
                   font=(FONT_SANS, 13), padx=46, pady=10)
    lbl.bind("<Button-1>", lambda e: command())
    return lbl


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
# Every candidate has their own ranked list of jobs and companies, and every
# job posting / company has its own ranked list of candidates — so each is
# keyed by who/what you're viewing results for. Replace with real scoring +
# imported profiles later; the dropdown + lookup pattern below can stay the same.
# Match scores are NOT shown to users (they only rank the lists), so the
# sample rows below carry no score column.
CANDIDATE_NAMES = ["Jordan Price", "Riley Chen", "Sam Okafor"]

JOB_POSTINGS = [
    "Software Engineer I — Acme Robotics",
    "Data Analyst — Northfield Health",
]

COMPANIES = [
    "Acme Robotics",
    "Northfield Health",
    "Lumen Logistics",
    "BrightPath Finance",
    "Maple Retail Co.",
]

# candidate name -> top 5 job matches for THAT candidate
# (rank, job_title, company, location)
SAMPLE_JOB_MATCHES_BY_CANDIDATE = {
    "Jordan Price": [
        (1, "Software Engineer I", "Acme Robotics",      "Dallas, TX"),
        (2, "Backend Developer",   "Lumen Logistics",    "Remote"),
        (3, "Data Analyst",        "Northfield Health",  "Austin, TX"),
        (4, "Product Analyst",     "BrightPath Finance", "Dallas, TX"),
        (5, "Junior Developer",    "Maple Retail Co.",   "Houston, TX"),
    ],
    "Riley Chen": [
        (1, "Data Analyst",        "Northfield Health",  "Austin, TX"),
        (2, "Product Analyst",     "BrightPath Finance", "Dallas, TX"),
        (3, "Software Engineer I", "Acme Robotics",      "Dallas, TX"),
        (4, "Backend Developer",   "Lumen Logistics",    "Remote"),
        (5, "Junior Developer",    "Maple Retail Co.",   "Houston, TX"),
    ],
    "Sam Okafor": [
        (1, "Backend Developer",   "Lumen Logistics",    "Remote"),
        (2, "Software Engineer I", "Acme Robotics",      "Dallas, TX"),
        (3, "Junior Developer",    "Maple Retail Co.",   "Houston, TX"),
        (4, "Data Analyst",        "Northfield Health",  "Austin, TX"),
        (5, "Product Analyst",     "BrightPath Finance", "Dallas, TX"),
    ],
}

# candidate name -> top 5 company matches for THAT candidate
# (rank, company, industry, best_matching_role)
# Each company is scored on its best-matching open role.
SAMPLE_COMPANY_MATCHES_BY_CANDIDATE = {
    "Jordan Price": [
        (1, "Acme Robotics",      "Manufacturing", "Software Engineer I"),
        (2, "Lumen Logistics",    "Logistics",     "Backend Developer"),
        (3, "Northfield Health",  "Healthcare",    "Data Analyst"),
        (4, "BrightPath Finance", "Finance",       "Product Analyst"),
        (5, "Maple Retail Co.",   "Retail",        "Junior Developer"),
    ],
    "Riley Chen": [
        (1, "Northfield Health",  "Healthcare",    "Data Analyst"),
        (2, "BrightPath Finance", "Finance",       "Product Analyst"),
        (3, "Acme Robotics",      "Manufacturing", "Software Engineer I"),
        (4, "Lumen Logistics",    "Logistics",     "Backend Developer"),
        (5, "Maple Retail Co.",   "Retail",        "Junior Developer"),
    ],
    "Sam Okafor": [
        (1, "Lumen Logistics",    "Logistics",     "Backend Developer"),
        (2, "Acme Robotics",      "Manufacturing", "Software Engineer I"),
        (3, "Maple Retail Co.",   "Retail",        "Junior Developer"),
        (4, "Northfield Health",  "Healthcare",    "Data Analyst"),
        (5, "BrightPath Finance", "Finance",       "Product Analyst"),
    ],
}

# Company side ranks candidates by PROFILE COMPLETION (not match score):
# the more fields a candidate has filled in, the higher they appear.
# (rank, candidate_name, target_role, profile_completion_pct)
# Placeholder: the same completion ranking is used for every job posting
# and every company until real profiles are imported.
SAMPLE_CANDIDATES_BY_COMPLETION = [
    (1, "Riley Chen",     "Data Analyst",        96),
    (2, "Jordan Price",   "Software Engineer I", 92),
    (3, "Sam Okafor",     "Backend Developer",   88),
    (4, "Casey Nguyen",   "Product Analyst",     81),
    (5, "Morgan Blake",   "Junior Developer",    74),
]
SAMPLE_CANDIDATES_BY_JOB = {j: SAMPLE_CANDIDATES_BY_COMPLETION for j in JOB_POSTINGS}
SAMPLE_CANDIDATES_BY_COMPANY = {c: SAMPLE_CANDIDATES_BY_COMPLETION for c in COMPANIES}


# MATCH PAGE — reusable page used by both the Job <-> Candidate tab and the
# Candidate <-> Company tab. Each page has two modes (a toggle at the top),
# a dropdown that picks whose list to show, and a Match button at the bottom.
# Results stay hidden until Match is pressed.
class MatchPage(tk.Frame):
    """modes = two dicts, one per toggle button, each with:
        label, title, subtitle, selector_label, options, rows (dict keyed by
        the dropdown choice), columns (for make_tree), pct_col (index of a
        column to show with a % sign, or None)"""

    def __init__(self, parent, modes):
        super().__init__(parent, bg=BG)
        self._modes = modes
        self._mode = 0  # which toggle button is active
        self._vars = [tk.StringVar(value=m["options"][0]) for m in modes]

        # Match button — fixed at the bottom of the page
        btn_row = tk.Frame(self, bg=BG, pady=14)
        btn_row.pack(side="bottom", fill="x")
        make_action_button(btn_row, "Match", self._on_match).pack()

        # Toggle between the two modes (rebuilt so only the active one is shaded)
        self._toggle_row = tk.Frame(self, bg=BG, padx=20, pady=14)
        self._toggle_row.pack(fill="x")

        # Selector row — picks whose ranked list is being shown
        self._selector_slot = tk.Frame(self, bg=BG, padx=20)
        self._selector_slot.pack(fill="x")

        # Results body
        body = tk.Frame(self, bg=BG, padx=20, pady=6)
        body.pack(fill="both", expand=True)

        self._results_title = tk.StringVar()
        tk.Label(body, textvariable=self._results_title, font=FONT_H2,
                 bg=BG, fg=ACCENT, anchor="w").pack(fill="x", pady=(0, 4))

        self._results_subtitle = tk.StringVar()
        tk.Label(body, textvariable=self._results_subtitle, font=FONT_SMALL,
                 bg=BG, fg=SUBTEXT, anchor="w").pack(fill="x", pady=(0, 10))

        self._table_slot = tk.Frame(body, bg=BG)
        self._table_slot.pack(fill="both", expand=True)

        self._rebuild_toggle()
        self._render_selector()
        self._render_results(show=False)

    # Toggle logic
    def _set_mode(self, mode):
        if mode == self._mode:
            return
        self._mode = mode
        self._rebuild_toggle()
        self._render_selector()
        self._render_results(show=False)

    def _rebuild_toggle(self):
        # Rebuild both buttons so only the active one shows the "pressed" color
        for child in self._toggle_row.winfo_children():
            child.destroy()
        btn_a = make_button(
            self._toggle_row, self._modes[0]["label"],
            lambda: self._set_mode(0), active=(self._mode == 0))
        btn_b = make_button(
            self._toggle_row, self._modes[1]["label"],
            lambda: self._set_mode(1), active=(self._mode == 1))
        btn_a.pack(side="left", expand=True, fill="x", padx=(0, 6))
        btn_b.pack(side="left", expand=True, fill="x", padx=(6, 0))

    # Dropdown
    def _render_selector(self):
        for w in self._selector_slot.winfo_children():
            w.destroy()
        m = self._modes[self._mode]
        tk.Label(self._selector_slot, text=m["selector_label"], font=FONT_BODY,
                 bg=BG, fg=TEXT).pack(side="left", padx=(0, 8))
        combo = ttk.Combobox(self._selector_slot, textvariable=self._vars[self._mode],
                              values=m["options"], state="readonly",
                              font=FONT_BODY, width=36)
        combo.pack(side="left")
        # Picking someone new clears the old list until Match is pressed again
        combo.bind("<<ComboboxSelected>>", lambda e: self._render_results(show=False))

    def _on_match(self):
        self._render_results(show=True)

    def _render_results(self, show):
        for w in self._table_slot.winfo_children():
            w.destroy()
        m = self._modes[self._mode]

        if not show:
            self._results_title.set("")
            self._results_subtitle.set("")
            tk.Label(self._table_slot,
                     text=f"Select a {m['selector_label'].rstrip(':').lower()} "
                          "and press Match.",
                     font=FONT_BODY, bg=BG, fg=SUBTEXT).pack(pady=40)
            return

        self._results_title.set(m["title"])
        self._results_subtitle.set(m["subtitle"])
        rows = m["rows"][self._vars[self._mode].get()]
        wrap, tree = make_tree(self._table_slot, m["columns"], height=5)
        wrap.pack(fill="both", expand=True)
        for i, row in enumerate(rows):
            tag = "odd" if i % 2 else "even"
            values = list(row)
            if m["pct_col"] is not None:
                values[m["pct_col"]] = f"{values[m['pct_col']]}%"
            tree.insert("", "end", tags=(tag,), values=values)


# JOB <-> CANDIDATE PAGE
def build_job_candidate_page(parent):
    return MatchPage(parent, [
        {
            "label": "Candidate → Jobs",
            "title": "Ranked Jobs",
            "subtitle": "Best-matching job postings for the selected candidate.",
            "selector_label": "Candidate:",
            "options": CANDIDATE_NAMES,
            "rows": SAMPLE_JOB_MATCHES_BY_CANDIDATE,
            "columns": [
                ("rank", "Rank", 50),
                ("job_title", "Job Title", 200),
                ("company", "Company", 170),
                ("location", "Location", 120),
            ],
            "pct_col": None,
        },
        {
            "label": "Job → Candidates",
            "title": "Ranked Candidates",
            "subtitle": "Ranked by profile completion for the selected job posting.",
            "selector_label": "Job posting:",
            "options": JOB_POSTINGS,
            "rows": SAMPLE_CANDIDATES_BY_JOB,
            "columns": [
                ("rank", "Rank", 50),
                ("candidate_name", "Candidate", 170),
                ("target_role", "Target Role", 200),
                ("completion", "Profile Completion", 120),
            ],
            "pct_col": 3,
        },
    ])


# CANDIDATE <-> COMPANY PAGE
def build_candidate_company_page(parent):
    return MatchPage(parent, [
        {
            "label": "Candidate → Companies",
            "title": "Ranked Companies",
            "subtitle": "Each company is scored on its best-matching open role.",
            "selector_label": "Candidate:",
            "options": CANDIDATE_NAMES,
            "rows": SAMPLE_COMPANY_MATCHES_BY_CANDIDATE,
            "columns": [
                ("rank", "Rank", 50),
                ("company", "Company", 180),
                ("industry", "Industry", 130),
                ("best_role", "Best-Matching Role", 170),
            ],
            "pct_col": None,
        },
        {
            "label": "Company → Candidates",
            "title": "Ranked Candidates",
            "subtitle": "Ranked by profile completion for the selected company.",
            "selector_label": "Company:",
            "options": COMPANIES,
            "rows": SAMPLE_CANDIDATES_BY_COMPANY,
            "columns": [
                ("rank", "Rank", 50),
                ("candidate_name", "Candidate", 170),
                ("target_role", "Target Role", 200),
                ("completion", "Profile Completion", 120),
            ],
            "pct_col": 3,
        },
    ])


# ADMIN PAGE — blank for now
class AdminPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        box = tk.Frame(self, bg=BG, highlightthickness=1,
                       highlightbackground=BORDER)
        box.pack(fill="both", expand=True, padx=20, pady=16)
        tk.Label(box, text="Admin page (blank for now)", font=FONT_BODY,
                 bg=BG, fg=SUBTEXT).pack(expand=True)


# MAIN WINDOW — tabs for the three pages (opens on Job <-> Candidate)
class MainApp(tk.Tk):
    TABS = ["Job ↔ Candidate", "Candidate ↔ Company", "Admin"]

    def __init__(self):
        super().__init__()
        self.title("1DGR Matching Algorithm")
        self.configure(bg=BG)
        self.resizable(False, False)
        apply_treeview_style()
        center(self, 760, 760)

        self._tab = 0  # which page is showing
        self._build()

    # Layout
    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=BG, pady=18)
        hdr.pack(fill="x")
        tk.Label(hdr, text="1DGR Matching",
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

        # Tabs — switch between the three pages
        self._tab_row = tk.Frame(self, bg=BG, padx=20)
        self._tab_row.pack(fill="x")
        self._rebuild_tabs()
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(10, 0))

        # Footer note — packed before the page area so it always stays visible
        tk.Label(self, text="Rankings shown are hardcoded sample data — "
                            "the scoring engine isn't wired in yet.",
                 font=FONT_SMALL, bg=BG, fg=SUBTEXT).pack(side="bottom", pady=(0, 10))

        # Page area — all three pages live here, only one is shown at a time
        self._page_slot = tk.Frame(self, bg=BG)
        self._page_slot.pack(fill="both", expand=True)
        self._pages = [
            build_job_candidate_page(self._page_slot),
            build_candidate_company_page(self._page_slot),
            AdminPage(self._page_slot),
        ]
        self._pages[self._tab].pack(fill="both", expand=True)

    # Tab logic
    def _set_tab(self, tab):
        if tab == self._tab:
            return
        self._pages[self._tab].pack_forget()
        self._tab = tab
        self._rebuild_tabs()
        self._pages[self._tab].pack(fill="both", expand=True)

    def _rebuild_tabs(self):
        # Rebuild all tab buttons so only the active one shows the "pressed" color
        for child in self._tab_row.winfo_children():
            child.destroy()
        for i, name in enumerate(self.TABS):
            btn = make_button(self._tab_row, name,
                              lambda i=i: self._set_tab(i),
                              active=(self._tab == i))
            btn.pack(side="left", expand=True, fill="x",
                     padx=(0 if i == 0 else 4, 0 if i == len(self.TABS) - 1 else 4))


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
