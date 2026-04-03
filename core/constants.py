"""
constants.py — App-wide constants, categories, merchant→category map, color palette.
"""

APP_NAME = "Wallet Hub"
APP_VERSION = "3.0.0"
DB_NAME = "wallethub.db"

# ── Expense Categories ─────────────────────────────────────────────
CATEGORIES = [
    "Food & Dining",
    "Groceries",
    "Transportation",
    "Shopping",
    "Entertainment",
    "Bills & Utilities",
    "Health & Medical",
    "Education",
    "Travel",
    "Rent & Housing",
    "Subscriptions",
    "Insurance",
    "Investments",
    "Personal Care",
    "Gifts & Donations",
    "Income",
    "Other",
]

# ── Merchant → Category Mapping (Smart Categorizer dictionary) ────
MERCHANT_CATEGORY_MAP: dict[str, str] = {
    # Food & Dining
    "starbucks": "Food & Dining", "mcdonald": "Food & Dining",
    "burger king": "Food & Dining", "subway": "Food & Dining",
    "domino": "Food & Dining", "pizza hut": "Food & Dining",
    "kfc": "Food & Dining", "chipotle": "Food & Dining",
    "dunkin": "Food & Dining", "wendy": "Food & Dining",
    "taco bell": "Food & Dining", "panda express": "Food & Dining",
    "chick-fil-a": "Food & Dining", "popeye": "Food & Dining",
    "zomato": "Food & Dining", "swiggy": "Food & Dining",
    "uber eats": "Food & Dining", "doordash": "Food & Dining",
    "grubhub": "Food & Dining", "restaurant": "Food & Dining",
    "cafe": "Food & Dining", "diner": "Food & Dining",
    "bakery": "Food & Dining", "coffee": "Food & Dining",

    # Groceries
    "walmart": "Groceries", "costco": "Groceries",
    "kroger": "Groceries", "target": "Groceries",
    "whole foods": "Groceries", "trader joe": "Groceries",
    "aldi": "Groceries", "lidl": "Groceries",
    "big bazaar": "Groceries", "dmart": "Groceries",
    "reliance fresh": "Groceries", "grocery": "Groceries",
    "supermarket": "Groceries", "market": "Groceries",

    # Transportation
    "uber": "Transportation", "lyft": "Transportation",
    "ola": "Transportation", "rapido": "Transportation",
    "shell": "Transportation", "bp gas": "Transportation",
    "petrol": "Transportation", "diesel": "Transportation",
    "gas station": "Transportation", "parking": "Transportation",
    "toll": "Transportation", "metro": "Transportation",
    "transit": "Transportation", "railway": "Transportation",

    # Shopping
    "amazon": "Shopping", "flipkart": "Shopping",
    "ebay": "Shopping", "myntra": "Shopping",
    "ajio": "Shopping", "nike": "Shopping",
    "adidas": "Shopping", "zara": "Shopping",
    "h&m": "Shopping", "ikea": "Shopping",

    # Entertainment
    "netflix": "Subscriptions", "spotify": "Subscriptions",
    "disney+": "Subscriptions", "hbo": "Subscriptions",
    "hulu": "Subscriptions", "apple music": "Subscriptions",
    "youtube premium": "Subscriptions", "amazon prime": "Subscriptions",
    "hotstar": "Subscriptions", "xbox": "Entertainment",
    "playstation": "Entertainment", "steam": "Entertainment",
    "cinema": "Entertainment", "movie": "Entertainment",
    "theatre": "Entertainment", "concert": "Entertainment",

    # Bills & Utilities
    "electric": "Bills & Utilities", "water bill": "Bills & Utilities",
    "internet": "Bills & Utilities", "broadband": "Bills & Utilities",
    "mobile recharge": "Bills & Utilities", "airtel": "Bills & Utilities",
    "jio": "Bills & Utilities", "vodafone": "Bills & Utilities",
    "verizon": "Bills & Utilities", "at&t": "Bills & Utilities",
    "t-mobile": "Bills & Utilities", "comcast": "Bills & Utilities",

    # Health & Medical
    "pharmacy": "Health & Medical", "hospital": "Health & Medical",
    "doctor": "Health & Medical", "clinic": "Health & Medical",
    "apollo": "Health & Medical", "medplus": "Health & Medical",
    "cvs": "Health & Medical", "walgreens": "Health & Medical",
    "dental": "Health & Medical", "optician": "Health & Medical",
    "gym": "Health & Medical", "fitness": "Health & Medical",

    # Education
    "udemy": "Education", "coursera": "Education",
    "skillshare": "Education", "tuition": "Education",
    "school": "Education", "university": "Education",
    "college": "Education", "book": "Education",

    # Travel
    "airline": "Travel", "flight": "Travel",
    "hotel": "Travel", "airbnb": "Travel",
    "booking.com": "Travel", "makemytrip": "Travel",
    "expedia": "Travel", "trivago": "Travel",

    # Rent
    "rent": "Rent & Housing", "lease": "Rent & Housing",
    "mortgage": "Rent & Housing", "housing": "Rent & Housing",

    # Insurance
    "insurance": "Insurance", "lic": "Insurance",
    "policy": "Insurance", "premium": "Insurance",

    # Income
    "salary": "Income", "payroll": "Income",
    "freelance": "Income", "dividend": "Income",
    "interest earned": "Income", "refund": "Income",
    "cashback": "Income",
}

# ── Asset Types ───────────────────────────────────────────────────
ASSET_TYPES = ["Crypto", "Stock", "Mutual Fund", "Gold", "Other"]

# ── Default Envelope Budget Limits ────────────────────────────────
DEFAULT_ENVELOPES = {
    "Food & Dining": 5000,
    "Groceries": 4000,
    "Transportation": 3000,
    "Shopping": 3000,
    "Entertainment": 2000,
    "Bills & Utilities": 5000,
    "Health & Medical": 2000,
    "Subscriptions": 1500,
}

# ── Color Palette (Trading-Terminal / Catppuccin Mocha) ───────────
COLORS = {
    "bg_darkest":    "#0d1117",
    "bg_dark":       "#161b22",
    "bg_card":       "#1c2128",
    "bg_surface":    "#21262d",
    "bg_hover":      "#292e36",
    "border":        "#30363d",
    "border_light":  "#3d444d",
    "text_primary":  "#e6edf3",
    "text_secondary":"#8b949e",
    "text_muted":    "#6e7681",
    "accent":        "#6c63ff",
    "accent_hover":  "#5a52d5",
    "green":         "#3fb950",
    "green_dim":     "#1a7f37",
    "red":           "#f85149",
    "red_dim":       "#b62324",
    "orange":        "#d29922",
    "blue":          "#58a6ff",
    "purple":        "#bc8cff",
    "cyan":          "#39d2c0",
    "pink":          "#f778ba",
}

CHART_COLORS = [
    "#6c63ff", "#f85149", "#3fb950", "#d29922", "#58a6ff",
    "#bc8cff", "#39d2c0", "#f778ba", "#8b949e", "#ff7b72",
    "#7ee787", "#79c0ff",
]
