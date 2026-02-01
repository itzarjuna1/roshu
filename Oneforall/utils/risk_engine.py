# -*- coding: utf-8 -*-

"""
Risk scoring & threat interpretation engine
Passive • Defensive • OWASP-aligned
"""

OWASP_WEIGHTS = {
    "missing_csp": 2,
    "missing_xfo": 1,
    "missing_xcto": 1,
    "missing_hsts": 2,
    "missing_referrer": 1,
    "missing_permissions": 1,
    "no_https": 3,
    "weak_tls": 2,
    "server_exposed": 1,
}


def calculate_risk(headers: dict, tls_info: dict) -> dict:
    """
    Returns risk score, level, threats, and recommendations
    """

    score = 0
    threats = []
    recommendations = []

    missing = headers.get("missing", {})
    server = headers.get("server", "unknown")

    # ---- Header based risks ----
    if "Content-Security-Policy" in missing:
        score += OWASP_WEIGHTS["missing_csp"]
        threats.append("lack of content security policy")
        recommendations.append("implement a strict content-security-policy")

    if "X-Frame-Options" in missing:
        score += OWASP_WEIGHTS["missing_xfo"]
        threats.append("clickjacking exposure")
        recommendations.append("enable x-frame-options header")

    if "X-Content-Type-Options" in missing:
        score += OWASP_WEIGHTS["missing_xcto"]
        threats.append("mime type sniffing risk")
        recommendations.append("set x-content-type-options to nosniff")

    if "Strict-Transport-Security" in missing:
        score += OWASP_WEIGHTS["missing_hsts"]
        threats.append("ssl stripping possibility")
        recommendations.append("enable hsts with long max-age")

    if "Referrer-Policy" in missing:
        score += OWASP_WEIGHTS["missing_referrer"]
        threats.append("referrer information leakage")
        recommendations.append("apply a strict referrer-policy")

    if "Permissions-Policy" in missing:
        score += OWASP_WEIGHTS["missing_permissions"]
        threats.append("browser feature abuse surface")
        recommendations.append("restrict browser permissions")

    # ---- TLS / HTTPS risks ----
    if not tls_info.get("https"):
        score += OWASP_WEIGHTS["no_https"]
        threats.append("unencrypted traffic exposure")
        recommendations.append("force https across the website")

    tls_version = tls_info.get("tls_version", "").lower()
    if tls_version and tls_version not in ("tlsv1.3", "tlsv1.2"):
        score += OWASP_WEIGHTS["weak_tls"]
        threats.append("weak or outdated tls configuration")
        recommendations.append("upgrade tls to version 1.2 or higher")

    # ---- Server exposure ----
    if server != "unknown":
        score += OWASP_WEIGHTS["server_exposed"]
        threats.append("server software fingerprint exposure")
        recommendations.append("hide or obfuscate server headers")

    # ---- Risk level mapping ----
    if score <= 3:
        level = "LOW"
    elif score <= 7:
        level = "MEDIUM"
    else:
        level = "HIGH"

    return {
        "score": score,
        "level": level,
        "threats": list(set(threats)),
        "recommendations": list(set(recommendations)),
      }
