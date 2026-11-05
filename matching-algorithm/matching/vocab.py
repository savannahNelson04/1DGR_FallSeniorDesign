"""
Word lists used to normalize free text. Extend these as real 1DGR data arrives.
"""

# Different spellings of the same skill map to one canonical name (all lowercase).
SKILL_SYNONYMS = {
    "js": "javascript", "java script": "javascript",
    "ts": "typescript",
    "node": "node.js", "nodejs": "node.js",
    "reactjs": "react", "react.js": "react",
    "postgres": "postgresql", "psql": "postgresql",
    "ml": "machine learning",
    "nlp": "natural language processing",
    "ms excel": "excel", "microsoft excel": "excel",
    "powerbi": "power bi", "microsoft power bi": "power bi",
    "amazon web services": "aws",
    "power bi (learning)": "power bi",
    "ux research": "user research",
    "html": "html/css", "css": "html/css",
    "sfdc": "salesforce",
    "c lang": "c",
}

# Industries that count as a partial match for each other (both directions are added automatically).
RELATED_INDUSTRIES = {
    "Software": ["Financial Technology", "Education Technology", "Cybersecurity", "Healthcare Technology"],
    "Financial Technology": ["Financial Services"],
    "Financial Services": ["Consulting"],
    "Healthcare Technology": ["Healthcare"],
    "Healthcare": ["Biotechnology"],
    "Biotechnology": ["Manufacturing"],
    "Renewable Energy": ["Construction & Engineering", "Manufacturing"],
    "Logistics & Supply Chain": ["Manufacturing", "Retail & E-commerce"],
    "Manufacturing": ["Aerospace"],
    "Marketing & Advertising": ["Media & Entertainment", "Retail & E-commerce"],
    "Education Technology": ["Nonprofit"],
}

# Seniority levels: 0 intern, 1 entry, 2 mid, 3 senior, 4 lead/manager.
# See normalize.title_level() for how these combine (e.g., "Assistant Project Manager" -> entry).
INTERN_WORDS = {"intern", "internship", "co-op", "coop", "trainee"}
ENTRY_WORDS = {"junior", "jr", "associate", "assistant", "entry", "i", "coordinator", "technician",
               "representative", "apprentice"}
MID_WORDS = {"ii"}
SENIOR_WORDS = {"senior", "sr", "lead", "staff", "iii"}
MANAGER_WORDS = {"manager", "director", "head", "principal", "vp", "chief"}
DEFAULT_TITLE_LEVEL = 1   # plain titles ("Data Analyst") are treated as entry level on an early-career platform

EXPERIENCE_LEVEL = {      # industry_exp enum -> seniority level
    "NO_EXPERIENCE": 1, "INTERNSHIP": 1, "1_2_YEARS": 1, "3_5_YEARS": 2, "5_PLUS_YEARS": 3,
}
EXPECTED_YEARS_BY_LEVEL = {0: 0.0, 1: 0.5, 2: 2.0, 3: 5.0, 4: 7.0}

EDUCATION_RANK = {        # education_level enum -> rank
    "HIGH_SCHOOL": 0, "CERTIFICATE": 1, "ASSOCIATES": 2, "ASSOCIATE": 2, "BACHELORS": 3,
    "MASTERS": 4, "MASTER": 4, "PHD": 5, "PROFESSIONAL_DOCTORATE": 5,
}

STOPWORDS = set("""
a an and the of to in on for with at by from as is are was were be been this that these those it its our your
we you they their them i me my he she his her or but not into over under about across than then so such very
will can could would should may might must also more most other new real every each all any some team teams
work working role roles job jobs company day days project projects experience help helps join
""".split())
