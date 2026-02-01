# -*- coding: utf-8 -*-

import requests
import ssl
import socket


SECURITY_HEADERS = {
    "Content-Security-Policy": "Protects against XSS & data injection",
    "X-Frame-Options": "Prevents clickjacking",
    "X-Content-Type-Options": "Prevents MIME sniffing",
    "Strict-Transport-Security": "Forces HTTPS",
    "Referrer-Policy": "Controls referrer data leakage",
    "Permissions-Policy": "Restricts browser features",
}


def scan_security_headers(url: str) -> dict:
    """
    Passive scan for HTTP security headers
    """
    result = {
        "present": {},
        "missing": {},
        "server": "unknown",
    }

    try:
        r = requests.get(url, timeout=10, allow_redirects=True)
        headers = r.headers

        result["server"] = headers.get("Server", "unknown")

        for header, desc in SECURITY_HEADERS.items():
            if header in headers:
                result["present"][header] = headers.get(header)
            else:
                result["missing"][header] = desc

    except Exception:
        pass

    return result


def scan_https_tls(domain: str) -> dict:
    """
    Passive TLS / HTTPS inspection
    """
    info = {
        "https": False,
        "tls_version": "unknown",
        "certificate": "unknown",
    }

    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(
            socket.socket(socket.AF_INET),
            server_hostname=domain,
        ) as sock:
            sock.settimeout(5)
            sock.connect((domain, 443))

            info["https"] = True
            info["tls_version"] = sock.version()

            cert = sock.getpeercert()
            if cert:
                info["certificate"] = "valid"

    except Exception:
        pass

    return inform 
