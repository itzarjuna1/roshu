# -*- coding: utf-8 -*-

"""
Passive Website Vulnerability Scanner
NO exploitation, NO brute-force, NO active attacks
"""

import ssl
import socket
import requests
from urllib.parse import urlparse


COMMON_SECURITY_HEADERS = {
    "Content-Security-Policy": "Missing Content Security Policy",
    "X-Frame-Options": "Missing X-Frame-Options (Clickjacking risk)",
    "X-Content-Type-Options": "Missing X-Content-Type-Options",
    "Strict-Transport-Security": "Missing HSTS (HTTPS downgrade risk)",
    "Referrer-Policy": "Missing Referrer-Policy",
    "Permissions-Policy": "Missing Permissions-Policy",
}


def normalize_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        return "https://" + url
    return url


def check_ssl(domain: str) -> bool:
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(
            socket.socket(), server_hostname=domain
        ) as s:
            s.settimeout(3)
            s.connect((domain, 443))
        return True
    except Exception:
        return False


def scan_headers(response) -> list:
    issues = []
    headers = response.headers

    for header, warning in COMMON_SECURITY_HEADERS.items():
        if header not in headers:
            issues.append(warning)

    if "Server" in headers:
        issues.append(
            f"Server header exposed: {headers.get('Server')}"
        )

    if "X-Powered-By" in headers:
        issues.append(
            f"Technology disclosure via X-Powered-By: {headers.get('X-Powered-By')}"
        )

    return issues


def scan_website(target: str) -> dict:
    result = {
        "domain": target,
        "ssl": False,
        "threats": [],
        "recommendations": [],
        "score": 10,
        "risk": "Low",
    }

    url = normalize_url(target)
    parsed = urlparse(url)

    try:
        response = requests.get(
            url,
            timeout=6,
            allow_redirects=True,
            headers={"User-Agent": "Passive-VL-Scanner"},
        )
    except Exception:
        result["threats"].append("Website unreachable or blocking requests")
        result["score"] = 9
        result["risk"] = "High"
        return result

    # SSL Check
    if parsed.scheme == "https":
        result["ssl"] = check_ssl(parsed.hostname)
        if not result["ssl"]:
            result["threats"].append("Invalid or misconfigured SSL certificate")
            result["score"] -= 2
    else:
        result["threats"].append("Website does not enforce HTTPS")
        result["score"] -= 3

    # Header Scan
    header_issues = scan_headers(response)
    result["threats"].extend(header_issues)
    result["score"] -= len(header_issues)

    # Basic exposure checks
    if "/wp-admin" in response.text.lower():
        result["threats"].append("Possible WordPress exposure detected")

    if "phpinfo()" in response.text.lower():
        result["threats"].append("Potential phpinfo exposure")

    # Risk level
    if result["score"] <= 4:
        result["risk"] = "Critical"
    elif result["score"] <= 6:
        result["risk"] = "High"
    elif result["score"] <= 8:
        result["risk"] = "Medium"

    # Recommendations auto-gen
    for threat in result["threats"]:
        if "Missing" in threat:
            result["recommendations"].append(
                f"Implement proper {threat.replace('Missing ', '')}"
            )
        if "Server header exposed" in threat:
            result["recommendations"].append(
                "Hide server version information"
            )
        if "HTTPS" in threat:
            result["recommendations"].append(
                "Force HTTPS with HSTS enabled"
            )

    result["score"] = max(1, result["score"])

    return result
