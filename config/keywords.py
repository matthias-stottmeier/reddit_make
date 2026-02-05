"""
Keyword configuration for MAKE Reddit Scraper
All keywords organized by category for pain scoring and intent detection
"""

# =============================================================================
# KEYWORD CATEGORIES
# =============================================================================

# A. Core Financial Pain Signals (Highest Intent) - Weight: 3.0
PAIN_KEYWORDS = [
    "payout",
    "payouts",
    "delayed payout",
    "missing payout",
    "payout stuck",
    "payment pending",
    "money stuck",
    "funds frozen",
    "account frozen",
    "account closed",
    "payment failed",
    "withdrawal failed",
    "withdrawal pending",
    "money on hold",
]

# B. Compliance & Fear Language (Very Important) - Weight: 2.5
COMPLIANCE_KEYWORDS = [
    "flagged account",
    "compliance issue",
    "verification failed",
    "KYC problem",
    "AML review",
    "suspicious activity",
    "banned",
    "terminated",
    "account review",
    "identity verification",
    "document rejected",
]

# C. Alternative/Switching Intent (Conversion Gold) - Weight: 4.0
SWITCH_KEYWORDS = [
    "alternative to Paxum",
    "Paxum alternative",
    "Skrill alternative",
    "PayPal alternative",
    "banking for creators",
    "bank for OnlyFans",
    "best payout method",
    "safest payout method",
    "creator banking",
    "adult friendly bank",
    "what bank do you use",
    "recommend a bank",
    "which bank",
    "better than Paxum",
    "switch from",
    "looking for alternative",
]

# D. Fees & Loss Anxiety - Weight: 1.5
FEE_KEYWORDS = [
    "high fees",
    "payout fees",
    "conversion fees",
    "FX fees",
    "currency conversion",
    "exchange rate",
    "lost money",
    "missing money",
    "fee breakdown",
    "transfer fees",
    "withdrawal fees",
]

# =============================================================================
# PLATFORMS TO MONITOR
# =============================================================================

PLATFORMS = [
    "OnlyFans",
    "Fansly",
    "Fanvue",
    "MYM",
    "Uncove",
    "4Based",
    "Fantime",
    "Loverfans",
    "F2F",
    "Maloum",
    "ManyVids",
    "LoyalFans",
    "Fanfix",
    "Streamate",
    "Passes",
    "Chaturbate",
    "Stripchat",
    "MyFreeCams",
    "Flirt4Free",
    "JustForFans",
    "Cam4",
    "BongaCams",
]

# Platform-specific query templates
PLATFORM_QUERY_TEMPLATES = [
    "{platform} payout delayed",
    "{platform} payout stuck",
    "{platform} payout issue",
    "{platform} payment pending",
    "{platform} not paying",
    "{platform} withdrawal problem",
    "money stuck in {platform}",
    "{platform} payout method",
]

# =============================================================================
# BANKING & PAYMENT PROVIDERS
# =============================================================================

# Adult-unfriendly or commonly blocked
PAYMENT_PROVIDERS = [
    "Paxum",
    "Cosmo",
    "Skrill",
    "Neteller",
    "MassPay",
    "Payoneer",
]

MAINSTREAM_BANKS = [
    "Bank of America",
    "Chase",
    "Wells Fargo",
    "Citi",
    "HSBC",
    "Barclays",
    "Revolut",
    "Wise",
]

WALLETS = [
    "PayPal",
    "Cash App",
    "Venmo",
    "Zelle",
]

# Modifiers to combine with banking entities
BANKING_MODIFIERS = [
    "frozen",
    "blocked",
    "closed",
    "rejected",
    "flagged",
]

# =============================================================================
# REGEX PATTERNS FOR ADVANCED MATCHING
# =============================================================================

REGEX_PATTERNS = [
    r"(payout|withdrawal|payment).*(stuck|pending|delayed|failed)",
    r"(account|funds).*(frozen|closed|blocked)",
    r"(bank|payment).*(issue|problem|blocked)",
    r"(alternative|replacement).*(paxum|skrill|paypal)",
    r"(looking for|need|want).*(bank|payout|payment)",
    r"(help|advice).*(payout|withdrawal|bank)",
]

# =============================================================================
# KEYWORD WEIGHTS FOR SCORING
# =============================================================================

KEYWORD_WEIGHTS = {
    "pain": 3.0,
    "compliance": 2.5,
    "switch": 4.0,  # Highest intent!
    "fee": 1.5,
    "platform": 1.0,
    "banking": 2.0,
}

# =============================================================================
# COMBINED SEARCH KEYWORDS
# (Subset for initial scraping - most important keywords)
# =============================================================================

# Priority keywords to search for (used in URL queries)
PRIORITY_SEARCH_KEYWORDS = [
    # Core pain
    "payout",
    "payment",
    "withdrawal",
    "frozen",
    "stuck",

    # Banking
    "banking",
    "bank",
    "Paxum",
    "PayPal",

    # Switching intent
    "alternative",
    "recommend",
    "which bank",
    "best payout",

    # Compliance
    "banned",
    "flagged",
    "verification",

    # Fees
    "fees",
    "conversion",
]


def get_all_keywords():
    """Return all keywords as a flat list"""
    all_kw = []
    all_kw.extend(PAIN_KEYWORDS)
    all_kw.extend(COMPLIANCE_KEYWORDS)
    all_kw.extend(SWITCH_KEYWORDS)
    all_kw.extend(FEE_KEYWORDS)
    all_kw.extend(PAYMENT_PROVIDERS)
    all_kw.extend(WALLETS)
    return list(set(all_kw))


def get_keyword_category(keyword: str) -> str:
    """Determine the category of a keyword"""
    keyword_lower = keyword.lower()

    if any(kw.lower() in keyword_lower for kw in SWITCH_KEYWORDS):
        return "switch"
    if any(kw.lower() in keyword_lower for kw in PAIN_KEYWORDS):
        return "pain"
    if any(kw.lower() in keyword_lower for kw in COMPLIANCE_KEYWORDS):
        return "compliance"
    if any(kw.lower() in keyword_lower for kw in FEE_KEYWORDS):
        return "fee"
    if any(kw.lower() in keyword_lower for kw in PAYMENT_PROVIDERS + WALLETS + MAINSTREAM_BANKS):
        return "banking"
    if any(kw.lower() in keyword_lower for kw in PLATFORMS):
        return "platform"

    return "other"
