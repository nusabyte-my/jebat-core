"""JEBAT CyberSec Toolkit — TukangBesi (Blacksmith of Security).

Pentest and cybersecurity tools for the JEBAT warrior:
  - Port scanning (nmap wrapper)
  - CVE lookup (NVD/NIST API)
  - Shodan reconnaissance
  - DNS enumeration
  - Subdomain discovery
  - HTTP header security audit
  - OWASP top-10 quick check
  - Password strength analysis
  - SSL/TLS certificate check

Safety: All tools use tier-based safety system.
  AUTO     → read-only recon (CVE lookup, DNS, Shodan, SSL check)
  CONFIRM  → active scanning (nmap, subdomain brute, HTTP audit)
  DANGEROUS → exploitation tools (future: sqlmap, nikto attacks)
"""

from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass, field
from typing import Any

import httpx

# ── Safety Tiers ──────────────────────────────────────────────────────────

class CyberSafetyTier:
    AUTO = "auto"        # Read-only recon
    CONFIRM = "confirm"  # Active scanning
    DANGEROUS = "dangerous"  # Exploitation


# ── CVE Lookup ────────────────────────────────────────────────────────────

@dataclass(slots=True)
class CVEEntry:
    cve_id: str
    description: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    cvss_score: float
    published: str
    affected_products: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)


async def cve_lookup(cve_id: str) -> CVEEntry:
    """Look up a CVE by ID from NVD/NIST API.
    
    Safety: AUTO (read-only API query)
    """
    cve_id = cve_id.upper().strip()
    if not re.match(r"CVE-\d{4}-\d{4,}", cve_id):
        raise ValueError(f"Invalid CVE ID format: {cve_id}")

    url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve_id}"
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, headers={"Accept": "application/json"})
        response.raise_for_status()

    data = response.json()
    vulnerabilities = data.get("vulnerabilities", [])
    if not vulnerabilities:
        raise ValueError(f"CVE {cve_id} not found in NVD")

    vuln = vulnerabilities[0].get("cve", {})
    
    # Extract description
    descriptions = vuln.get("descriptions", [])
    desc = ""
    for d in descriptions:
        if d.get("lang") == "en":
            desc = d.get("value", "")
            break

    # Extract CVSS
    metrics = vuln.get("metrics", {})
    cvss_data = metrics.get("cvssMetricV31", []) or metrics.get("cvssMetricV2", [])
    severity = "UNKNOWN"
    cvss_score = 0.0
    if cvss_data:
        primary = cvss_data[0].get("cvssData", {})
        severity = primary.get("baseSeverity", "UNKNOWN")
        cvss_score = primary.get("baseScore", 0.0)

    # Extract affected products
    products: list[str] = []
    configurations = vuln.get("configurations", [])
    for config in configurations:
        for node in config.get("nodes", []):
            for cpe in node.get("cpeMatch", []):
                criteria = cpe.get("criteria", "")
                if criteria:
                    products.append(criteria)

    # Extract references
    refs: list[str] = []
    references = vuln.get("references", [])
    for ref in references:
        url_ref = ref.get("url", "")
        if url_ref:
            refs.append(url_ref)

    return CVEEntry(
        cve_id=vuln.get("id", cve_id),
        description=desc,
        severity=severity,
        cvss_score=cvss_score,
        published=vuln.get("published", ""),
        affected_products=products[:10],
        references=refs[:5],
    )


async def cve_search(keyword: str, limit: int = 10) -> list[CVEEntry]:
    """Search CVEs by keyword.
    
    Safety: AUTO (read-only API query)
    """
    url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch={keyword}&resultsPerPage={limit}"
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, headers={"Accept": "application/json"})
        response.raise_for_status()

    data = response.json()
    vulnerabilities = data.get("vulnerabilities", [])
    results: list[CVEEntry] = []
    
    for vuln_data in vulnerabilities:
        vuln = vuln_data.get("cve", {})
        descriptions = vuln.get("descriptions", [])
        desc = ""
        for d in descriptions:
            if d.get("lang") == "en":
                desc = d.get("value", "")
                break
        
        metrics = vuln.get("metrics", {})
        cvss_data = metrics.get("cvssMetricV31", []) or metrics.get("cvssMetricV2", [])
        severity = "UNKNOWN"
        cvss_score = 0.0
        if cvss_data:
            primary = cvss_data[0].get("cvssData", {})
            severity = primary.get("baseSeverity", "UNKNOWN")
            cvss_score = primary.get("baseScore", 0.0)

        results.append(CVEEntry(
            cve_id=vuln.get("id", ""),
            description=desc[:200],
            severity=severity,
            cvss_score=cvss_score,
            published=vuln.get("published", ""),
        ))

    return results


# ── Shodan Recon ──────────────────────────────────────────────────────────

@dataclass(slots=True)
class ShodanHost:
    ip: str
    hostnames: list[str] = field(default_factory=list)
    ports: list[int] = field(default_factory=list)
    os: str = ""
    country: str = ""
    city: str = ""
    org: str = ""
    vulns: list[str] = field(default_factory=list)


async def shodan_lookup(ip: str, api_key: str | None = None) -> ShodanHost:
    """Look up a host on Shodan.
    
    Safety: AUTO (read-only API query)
    Requires: SHODAN_API_KEY env var or explicit api_key
    """
    key = api_key or os.getenv("SHODAN_API_KEY", "")
    if not key:
        raise ValueError("SHODAN_API_KEY not set. Get one at https://account.shodan.io/")

    url = f"https://api.shodan.io/shodan/host/{ip}?key={key}"
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url)
        response.raise_for_status()

    data = response.json()
    return ShodanHost(
        ip=data.get("ip_str", ip),
        hostnames=data.get("hostnames", []),
        ports=data.get("ports", []),
        os=data.get("os", ""),
        country=data.get("country_name", ""),
        city=data.get("city", ""),
        org=data.get("org", ""),
        vulns=data.get("vulns", []),
    )


# ── Nmap Wrapper ──────────────────────────────────────────────────────────

@dataclass(slots=True)
class NmapResult:
    target: str
    ports: list[dict[str, Any]] = field(default_factory=list)
    hosts: list[dict[str, Any]] = field(default_factory=list)
    scan_time: float = 0.0
    command: str = ""


async def nmap_scan(
    target: str,
    ports: str | None = None,
    scan_type: str = "quick",
    extra_args: list[str] | None = None,
) -> NmapResult:
    """Run nmap scan. 
    
    Safety: CONFIRM (active network scanning)
    Requires: nmap installed on system
    """
    # Build nmap command
    cmd = ["nmap"]
    
    if scan_type == "quick":
        cmd.extend(["-T4", "-F"])  # Fast, top 100 ports
    elif scan_type == "standard":
        cmd.extend(["-T4", "-p", "1-1000"])
    elif scan_type == "full":
        cmd.extend(["-T4", "-p-", "--max-retries", "2"])
    elif scan_type == "vuln":
        cmd.extend(["--script", "vuln", "-T4"])
    elif scan_type == "service":
        cmd.extend(["-sV", "-T4"])
    
    if ports:
        cmd.extend(["-p", ports])
    
    if extra_args:
        cmd.extend(extra_args)
    
    cmd.append(target)
    
    # Run nmap
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    
    if proc.returncode != 0:
        raise RuntimeError(f"nmap failed: {stderr.decode().strip()}")
    
    output = stdout.decode()
    
    # Parse ports from nmap output
    port_list: list[dict[str, Any]] = []
    for line in output.split("\n"):
        match = re.match(r"(\d+)/(tcp|udp)\s+(\S+)\s+(\S+)", line.strip())
        if match:
            port_list.append({
                "port": int(match.group(1)),
                "protocol": match.group(2),
                "state": match.group(3),
                "service": match.group(4),
            })
    
    return NmapResult(
        target=target,
        ports=port_list,
        command=" ".join(cmd),
        scan_time=0.0,
    )


# ── DNS Enumeration ───────────────────────────────────────────────────────

async def dns_lookup(domain: str, record_type: str = "A") -> list[dict[str, str]]:
    """DNS record lookup.
    
    Safety: AUTO (read-only DNS query)
    """
    # Use dig or nslookup
    try:
        proc = await asyncio.create_subprocess_exec(
            "dig", "+short", domain, record_type,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode().strip()
    except FileNotFoundError:
        # Fallback to nslookup
        proc = await asyncio.create_subprocess_exec(
            "nslookup", "-type=" + record_type, domain,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode().strip()

    records = []
    for line in output.split("\n"):
        line = line.strip()
        if line and not line.startswith(";"):
            records.append({"domain": domain, "type": record_type, "value": line})
    
    return records


async def dns_recon(domain: str) -> dict[str, list[dict[str, str]]]:
    """Full DNS reconnaissance for a domain.
    
    Safety: AUTO (read-only DNS queries)
    """
    record_types = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]
    results: dict[str, list[dict[str, str]]] = {}
    
    for rtype in record_types:
        try:
            records = await dns_lookup(domain, rtype)
            if records:
                results[rtype] = records
        except Exception:
            continue
    
    return results


# ── Subdomain Discovery ──────────────────────────────────────────────────

async def subdomain_discovery(domain: str) -> list[str]:
    """Discover subdomains via crt.sh (certificate transparency).
    
    Safety: AUTO (read-only public API)
    """
    url = f"https://crt.sh/?q=%.{domain}&output=json"
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url)
        if response.status_code == 200:
            data = response.json()
            subdomains: set[str] = set()
            for entry in data:
                name = entry.get("name_value", "")
                for name_line in name.split("\n"):
                    name_line = name_line.strip().lower()
                    if name_line and name_line.endswith(f".{domain}"):
                        subdomains.add(name_line)
            return sorted(subdomains)
    return []


# ── HTTP Header Security Audit ────────────────────────────────────────────

@dataclass(slots=True)
class HeaderAudit:
    url: str
    score: int  # 0-100
    findings: list[dict[str, str]] = field(default_factory=list)
    headers: dict[str, str] = field(default_factory=dict)


SECURITY_HEADERS = {
    "Strict-Transport-Security": {"weight": 15, "desc": "HSTS — enforce HTTPS"},
    "Content-Security-Policy": {"weight": 15, "desc": "CSP — prevent XSS"},
    "X-Content-Type-Options": {"weight": 10, "desc": "nosniff — prevent MIME sniffing"},
    "X-Frame-Options": {"weight": 10, "desc": "DENY/SAMEORIGIN — prevent clickjacking"},
    "X-XSS-Protection": {"weight": 5, "desc": "XSS filter (deprecated but still useful)"},
    "Referrer-Policy": {"weight": 5, "desc": "Control referrer information"},
    "Permissions-Policy": {"weight": 5, "desc": "Control browser features"},
    "Cross-Origin-Opener-Policy": {"weight": 5, "desc": "COOP — isolation"},
    "Cross-Origin-Resource-Policy": {"weight": 5, "desc": "CORP — resource isolation"},
}


async def http_header_audit(url: str) -> HeaderAudit:
    """Audit HTTP response headers for security best practices.
    
    Safety: AUTO (read-only HTTP GET)
    """
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        response = await client.get(url)
    
    headers = dict(response.headers)
    score = 20  # Base score for HTTPS
    findings: list[dict[str, str]] = []
    
    # Check HTTPS
    if not str(response.url).startswith("https"):
        score -= 20
        findings.append({"header": "Protocol", "status": "MISSING", "desc": "Not using HTTPS"})
    
    # Check security headers
    for header, info in SECURITY_HEADERS.items():
        if header.lower() in {k.lower(): k for k in headers}:
            score += info["weight"]
            findings.append({"header": header, "status": "PRESENT", "desc": info["desc"]})
        else:
            findings.append({"header": header, "status": "MISSING", "desc": info["desc"]})
    
    # Check for information disclosure
    server = headers.get("server", "")
    if server and len(server) > 5:
        findings.append({"header": "Server", "status": "WARN", "desc": f"Server header reveals: {server}"})
    
    x_powered = headers.get("x-powered-by", "")
    if x_powered:
        findings.append({"header": "X-Powered-By", "status": "WARN", "desc": f"Reveals technology: {x_powered}"})
    
    return HeaderAudit(url=str(response.url), score=max(0, min(100, score)), findings=findings, headers=headers)


# ── SSL/TLS Certificate Check ────────────────────────────────────────────

@dataclass(slots=True)
class SSLCheck:
    domain: str
    issuer: str
    valid_from: str
    valid_to: str
    days_remaining: int
    protocol: str
    is_valid: bool
    SANs: list[str] = field(default_factory=list)


async def ssl_check(domain: str, port: int = 443) -> SSLCheck:
    """Check SSL/TLS certificate for a domain.
    
    Safety: AUTO (read-only TLS handshake)
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "openssl", "s_client", "-connect", f"{domain}:{port}",
            "-servername", domain,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        
        # Extract certificate
        cert_proc = await asyncio.create_subprocess_exec(
            "openssl", "x509", "-noout", "-text",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        cert_stdout, _ = await cert_proc.communicate(input=stdout)
        cert_text = cert_stdout.decode()
        
        # Parse issuer
        issuer_match = re.search(r"Issuer:.*?O\s*=\s*([^,\n]+)", cert_text)
        issuer = issuer_match.group(1).strip() if issuer_match else "Unknown"
        
        # Parse validity
        valid_from_match = re.search(r"Not Before\s*:\s*(.+)", cert_text)
        valid_to_match = re.search(r"Not After\s*:\s*(.+)", cert_text)
        valid_from = valid_from_match.group(1).strip() if valid_from_match else ""
        valid_to = valid_to_match.group(1).strip() if valid_to_match else ""
        
        # Parse SANs
        sans = re.findall(r"DNS:([^\s,]+)", cert_text)
        
        # Calculate days remaining
        days = 0
        if valid_to:
            try:
                from datetime import datetime, timezone
                expiry = datetime.strptime(valid_to.split(" GMT")[0].strip(), "%b %d %H:%M:%S %Y")
                days = (expiry - datetime.now(timezone.utc)).days
            except Exception:
                pass
        
        # Parse protocol
        protocol_match = re.search(r"Protocol\s*:\s*(.+)", stdout.decode())
        protocol = protocol_match.group(1).strip() if protocol_match else "TLS"
        
        return SSLCheck(
            domain=domain,
            issuer=issuer,
            valid_from=valid_from,
            valid_to=valid_to,
            days_remaining=days,
            protocol=protocol,
            is_valid=days > 0,
            SANs=sans,
        )
    except FileNotFoundError:
        raise RuntimeError("openssl not installed — required for SSL checks")


# ── Password Strength ────────────────────────────────────────────────────

def analyze_password(password: str) -> dict[str, Any]:
    """Analyze password strength.
    
    Safety: AUTO (local computation only)
    """
    score = 0
    findings: list[str] = []
    
    length = len(password)
    if length >= 16:
        score += 40
    elif length >= 12:
        score += 25
        findings.append("Consider using 16+ characters")
    elif length >= 8:
        score += 15
        findings.append("Password too short — use 12+ characters")
    else:
        findings.append("CRITICAL: Password under 8 characters")
    
    if re.search(r"[a-z]", password):
        score += 5
    else:
        findings.append("Missing lowercase letters")
    
    if re.search(r"[A-Z]", password):
        score += 5
    else:
        findings.append("Missing uppercase letters")
    
    if re.search(r"\d", password):
        score += 5
    else:
        findings.append("Missing digits")
    
    if re.search(r"[^a-zA-Z0-9]", password):
        score += 10
    else:
        findings.append("Missing special characters")
    
    # Common patterns
    if re.match(r"^123456", password) or re.match(r"^password", password):
        score = 0
        findings.append("CRITICAL: Extremely common password")
    
    if re.search(r"(.)\1{3,}", password):
        score -= 5
        findings.append("Repeating characters detected")
    
    return {
        "score": max(0, min(100, score)),
        "length": length,
        "strength": "STRONG" if score >= 70 else "MEDIUM" if score >= 40 else "WEAK",
        "findings": findings,
        "has_upper": bool(re.search(r"[A-Z]", password)),
        "has_lower": bool(re.search(r"[a-z]", password)),
        "has_digit": bool(re.search(r"\d", password)),
        "has_special": bool(re.search(r"[^a-zA-Z0-9]", password)),
    }


# ── Tool Registry ────────────────────────────────────────────────────────

CYBERSEC_TOOLS: dict[str, dict[str, Any]] = {
    "cve_lookup": {
        "description": "Look up a CVE by ID from NVD/NIST database",
        "safety": CyberSafetyTier.AUTO,
        "handler": cve_lookup,
        "parameters": {"cve_id": {"type": "string", "description": "CVE ID (e.g. CVE-2024-1234)"}},
    },
    "cve_search": {
        "description": "Search CVEs by keyword",
        "safety": CyberSafetyTier.AUTO,
        "handler": cve_search,
        "parameters": {"keyword": {"type": "string", "description": "Search keyword"}, "limit": {"type": "integer", "description": "Max results"}},
    },
    "shodan_lookup": {
        "description": "Look up a host on Shodan Internet Intelligence",
        "safety": CyberSafetyTier.AUTO,
        "handler": shodan_lookup,
        "parameters": {"ip": {"type": "string", "description": "IP address"}, "api_key": {"type": "string", "description": "Shodan API key (optional)"}},
    },
    "nmap_scan": {
        "description": "Run nmap port scan against a target",
        "safety": CyberSafetyTier.CONFIRM,
        "handler": nmap_scan,
        "parameters": {
            "target": {"type": "string", "description": "Target IP/hostname"},
            "scan_type": {"type": "string", "description": "quick/standard/full/vuln/service"},
            "ports": {"type": "string", "description": "Port range (optional)"},
        },
    },
    "dns_lookup": {
        "description": "DNS record lookup for a domain",
        "safety": CyberSafetyTier.AUTO,
        "handler": dns_lookup,
        "parameters": {"domain": {"type": "string"}, "record_type": {"type": "string", "description": "A/AAAA/MX/NS/TXT"}},
    },
    "dns_recon": {
        "description": "Full DNS reconnaissance for a domain",
        "safety": CyberSafetyTier.AUTO,
        "handler": dns_recon,
        "parameters": {"domain": {"type": "string"}},
    },
    "subdomain_discovery": {
        "description": "Discover subdomains via certificate transparency",
        "safety": CyberSafetyTier.AUTO,
        "handler": subdomain_discovery,
        "parameters": {"domain": {"type": "string"}},
    },
    "http_header_audit": {
        "description": "Audit HTTP security headers for a URL",
        "safety": CyberSafetyTier.AUTO,
        "handler": http_header_audit,
        "parameters": {"url": {"type": "string"}},
    },
    "ssl_check": {
        "description": "Check SSL/TLS certificate validity and details",
        "safety": CyberSafetyTier.AUTO,
        "handler": ssl_check,
        "parameters": {"domain": {"type": "string"}, "port": {"type": "integer"}},
    },
    "analyze_password": {
        "description": "Analyze password strength and provide recommendations",
        "safety": CyberSafetyTier.AUTO,
        "handler": analyze_password,
        "parameters": {"password": {"type": "string"}},
    },
}


def list_cybersec_tools() -> list[dict[str, str]]:
    """List all available cybersecurity tools."""
    return [
        {
            "name": name,
            "description": info["description"],
            "safety": info["safety"],
        }
        for name, info in CYBERSEC_TOOLS.items()
    ]