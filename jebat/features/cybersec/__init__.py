"""JEBAT CyberSec Toolkit — TukangBesi (Blacksmith of Security).

Pentest & cybersecurity tools for the JEBAT warrior.
All tools use tier-based safety: AUTO (read-only), CONFIRM (active scan), DANGEROUS (exploit).
"""

from jebat.features.cybersec.cybersec import (
    # CVE tools
    CVEEntry,
    cve_lookup,
    cve_search,
    # Shodan tools
    ShodanHost,
    shodan_lookup,
    # Nmap tools
    NmapResult,
    nmap_scan,
    # DNS tools
    dns_lookup,
    dns_recon,
    # Subdomain tools
    subdomain_discovery,
    # HTTP audit tools
    HeaderAudit,
    http_header_audit,
    # SSL tools
    SSLCheck,
    ssl_check,
    # Password tools
    analyze_password,
    # Registry
    CyberSafetyTier,
    CYBERSEC_TOOLS,
    list_cybersec_tools,
)

__all__ = [
    "CVEEntry", "cve_lookup", "cve_search",
    "ShodanHost", "shodan_lookup",
    "NmapResult", "nmap_scan",
    "dns_lookup", "dns_recon",
    "subdomain_discovery",
    "HeaderAudit", "http_header_audit",
    "SSLCheck", "ssl_check",
    "analyze_password",
    "CyberSafetyTier", "CYBERSEC_TOOLS", "list_cybersec_tools",
]