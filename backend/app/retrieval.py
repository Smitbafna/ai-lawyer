import re
JURISDICTION = "Uttarakhand"

SUPPORTED = {JURISDICTION}
SOURCE_REGISTER = {
    "SRC-02": {
        "title": "Uttarakhand Tenancy Act, 2021 (Act No. 02 of 2022) - Official Gazette",
        "type": "statute (enacted)",
        "jurisdiction": "Uttarakhand",
        "url": "https://cdnbbsr.s3waas.gov.in/s3bc7f621451b4f5df308a8e098112185d/uploads/2025/03/202503251012941681.pdf",
    },
}

# Parsed provision entries from provision_inventory.md
# Each entry contains full metadata for retrieval and source attribution.
PROVISIONS: List[Dict[str, Any]] = []


def _init_provisions() -> None:
    """Initialize PROVISIONS from parsed knowledge-base content."""
    global PROVISIONS
    PROVISIONS.clear()
    PROVISIONS.extend([
        {
            "id": "ST-UK-1(3)",
            "section": "S 1(3)",
            "legal_proposition": "Comes into force on date appointed by State Govt via gazette notification",
            "qualifications": "Effective date 01.01.2023 per Not No 67/iv(2)-sh. Vi.-2023-53 (sha)/2021 dated 13 Jan 2023",
            "source": "Uttarakhand Gazette (SRC-02)",
            "source_id": "SRC-02",
            "source_url": "https://cdnbbsr.s3waas.gov.in/s3bc7f621451b4f5df308a8e098112185d/uploads/2025/03/202503251012941681.pdf",
            "verification_status": "Verified commencement 01.01.2023",
            "jurisdiction": "Uttarakhand",
            "statute": "Uttarakhand Tenancy Act 2021",
            "act_number": "Act No 02 of 2022",
            "commencement": "01.01.2023",
            "document_type": "statutory provision",
            "provision_identifier": "S 1(3)",
        },
        {
            "id": "ST-UK-2",
            "section": "S 2",
            "legal_proposition": "Definitions: landlord tenant premises tenancy rent security deposit residential non-residential",
            "qualifications": "Exact wording must be verified against original gazette",
            "source": "Uttarakhand Gazette (SRC-02)",
            "source_id": "SRC-02",
            "source_url": "https://cdnbbsr.s3waas.gov.in/s3bc7f621451b4f5df308a8e098112185d/uploads/2025/03/202503251012941681.pdf",
            "verification_status": "Definitions framework verified exact wording to confirm",
            "jurisdiction": "Uttarakhand",
            "statute": "Uttarakhand Tenancy Act 2021",
            "act_number": "Act No 02 of 2022",
            "commencement": "01.01.2023",
            "document_type": "statutory provision",
            "provision_identifier": "S 2",
        },
        {
            "id": "ST-UK-3",
            "section": "S 3",
            "legal_proposition": "Nothing in Act applies to categories of premises exempted",
            "qualifications": "Exemptions per property verification needed",
            "source": "Uttarakhand Gazette (SRC-02)",
            "source_id": "SRC-02",
            "source_url": "https://cdnbbsr.s3waas.gov.in/s3bc7f621451b4f5df308a8e098112185d/uploads/2025/03/202503251012941681.pdf",
            "verification_status": "Exemptions partially verified per property scope",
            "jurisdiction": "Uttarakhand",
            "statute": "Uttarakhand Tenancy Act 2021",
            "act_number": "Act No 02 of 2022",
            "commencement": "01.01.2023",
            "document_type": "statutory provision",
            "provision_identifier": "S 3",
        },
        {
            "id": "ST-UK-11(1)",
            "section": "S 11(1)",
            "legal_proposition": "Security deposit paid by tenant in advance agreed between landlord tenant cannot exceed 2 months rent residential 6 months non-residential",
            "qualifications": "Deposit above cap must be refunded regardless of deductions",
            "source": "Uttarakhand Gazette (SRC-02)",
            "source_id": "SRC-02",
            "source_url": "https://cdnbbsr.s3waas.gov.in/s3bc7f621451b4f5df308a8e098112185d/uploads/2025/03/202503251012941681.pdf",
            "verification_status": "Verified cap 2 months residential 6 months non-residential",
            "jurisdiction": "Uttarakhand",
            "statute": "Uttarakhand Tenancy Act 2021",
            "act_number": "Act No 02 of 2022",
            "commencement": "01.01.2023",
            "document_type": "statutory provision",
            "provision_identifier": "S 11(1)",
        },
        {
            "id": "ST-UK-11(2)",
            "section": "S 11(2)",
            "legal_proposition": "Security deposit refunded to tenant on date of taking over vacant possession after deducting tenant liability",
            "qualifications": "Deposit above statutory cap must be refunded",
            "source": "Uttarakhand Gazette (SRC-02)",
            "source_id": "SRC-02",
            "source_url": "https://cdnbbsr.s3waas.gov.in/s3bc7f621451b4f5df308a8e098112185d/uploads/2025/03/202503251012941681.pdf",
            "verification_status": "Verified refund on vacant possession after liability deduction",
            "jurisdiction": "Uttarakhand",
            "statute": "Uttarakhand Tenancy Act 2021",
            "act_number": "Act No 02 of 2022",
            "commencement": "01.01.2023",
            "document_type": "statutory provision",
            "provision_identifier": "S 11(2)",
        },
        {
            "id": "ST-UK-12",
            "section": "S 12",
            "legal_proposition": "Tenancy agreement signed in duplicate by landlord and tenant one each retained",
            "qualifications": "Duplicate signed agreements required",
            "source": "Uttarakhand Gazette (SRC-02)",
            "source_id": "SRC-02",
            "source_url": "https://cdnbbsr.s3waas.gov.in/s3bc7f621451b4f5df308a8e098112185d/uploads/2025/03/202503251012941681.pdf",
            "verification_status": "Verified duplicate signing requirement",
            "jurisdiction": "Uttarakhand",
            "statute": "Uttarakhand Tenancy Act 2021",
            "act_number": "Act No 02 of 2022",
            "commencement": "01.01.2023",
            "document_type": "statutory provision",
            "provision_identifier": "S 12",
        },
        {
            "id": "ST-UK-30",
            "section": "S 30",
            "legal_proposition": "District Collector or DM may appoint officer not below rank of Deputy Collector as Rent Authority",
            "qualifications": "Operational status of appointed authorities unverified per district",
            "source": "Uttarakhand Gazette (SRC-02)",
            "source_id": "SRC-02",            "source_url": "https://cdnbbsr.s3waas.gov.in/s3bc7f621451b4f5df308a8e098112185d/uploads/2025/03/202503251012941681.pdf",            "verification_status": "Partially verified appointment authority identified functional status unknown",
            "jurisdiction": "Uttarakhand",
            "statute": "Uttarakhand Tenancy Act 2021",
            "act_number": "Act No 02 of 2022",
            "commencement": "01.01.2023",
            "document_type": "statutory provision",
            "provision_identifier": "S 30",
        },
        {
            "id": "ST-UK-47",
            "section": "S 47",
            "legal_proposition": "State Rent Control Act repealed pending cases continue under old act framework",
            "qualifications": "Repeal is legal not administrative operational continuity unverified",
            "source": "Uttarakhand Gazette (SRC-02)",
            "source_id": "SRC-02",
            "source_url": "https://cdnbbsr.s3waas.gov.in/s3bc7f621451b4f5df308a8e098112185d/uploads/2025/03/202503251012941681.pdf",
            "verification_status": "Verified repeal and savings provision text",
            "jurisdiction": "Uttarakhand",
            "statute": "Uttarakhand Tenancy Act 2021",
            "act_number": "Act No 02 of 2022",
            "commencement": "01.01.2023",
            "document_type": "statutory provision",
            "provision_identifier": "S 47",
        },
    ])

_init_provisions()


def keyword_search(query: str, jurisdiction: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
    """Search provisions by keyword query."""
    if jurisdiction and jurisdiction != JURISDICTION:
        return _unsupported_jurisdiction_result(jurisdiction)
    if not query or not query.strip():
        return []
    terms = re.findall(r"\\w+", query.lower())
    matches: List[Tuple[int, int, Dict[str, Any]]] = []
    for idx, entry in enumerate(PROVISIONS):
        score = 0
        if terms and any(term in entry.get("section", "").lower() for term in terms):
            score += 3
        if terms and any(term in entry.get("legal_proposition", "").lower() for term in terms):
            score += 2
        if terms and any(term in entry.get("qualifications", "").lower() for term in terms):
            score += 1
        if terms and any(term in entry.get("provision_identifier", "").lower() for term in terms):
            score += 2
        if score > 0:
            matches.append((score, idx, entry))
    matches.sort(key=lambda m: (-m[0], PROVISIONS[m[1]]["id"]))
    return [m[2] for m in matches[:top_k]]


def metadata_filter(
    jurisdiction: Optional[str] = None,
    statute: Optional[str] = None,
    section: Optional[str] = None,
    provision_id: Optional[str] = None,
    verification_status: Optional[str] = None,
    document_type: Optional[str] = None,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """Filter provisions by metadata fields."""
    if jurisdiction and jurisdiction != JURISDICTION:
        return _unsupported_jurisdiction_result(jurisdiction)
    filtered: List[Dict[str, Any]] = []
    for entry in PROVISIONS:
        if entry.get("jurisdiction") != JURISDICTION:
            continue
        if statute and entry.get("statute") != statute:
            continue
        if section and section not in entry.get("section", ""):
            continue
        if provision_id and entry.get("id") != provision_id:
            continue
        if verification_status and entry.get("verification_status") != verification_status:
            continue
        if document_type and entry.get("document_type") != document_type:
            continue
        filtered.append(entry)
    return filtered[:top_k]


def hybrid_search(
    query: str,
    jurisdiction: str = JURISDICTION,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """Combine keyword search with metadata filtering."""
    if jurisdiction != JURISDICTION:
        return _unsupported_jurisdiction_result(jurisdiction)
    if not query or not query.strip():
        return []
    candidates = PROVISIONS
    terms = re.findall(r"\\w+", query.lower())
    scored: List[Tuple[int, Dict[str, Any]]] = []
    for entry in candidates:
        score = 0
        if terms and any(term in entry.get("section", "").lower() for term in terms):
            score += 3
        if terms and any(term in entry.get("legal_proposition", "").lower() for term in terms):
            score += 2
        if terms and any(term in entry.get("qualifications", "").lower() for term in terms):
            score += 1
        if terms and any(term in entry.get("provision_identifier", "").lower() for term in terms):
            score += 2
        if score > 0:
            scored.append((score, entry))
    scored.sort(key=lambda m: (-m[0], PROVISIONS.index(m[1])))
    return [entry for _, entry in scored[:top_k]]


def get_provision(provision_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific provision by its ID."""
    for entry in PROVISIONS:
        if entry["id"] == provision_id:
            return entry
    return None


def _unsupported_jurisdiction_result(jurisdiction: str) -> List[Dict[str, Any]]:
    """Return result indicating jurisdiction is not supported."""
    return [{
        "id": "UNSUPPORTED",
        "section": "--",
        "legal_proposition": f"Jurisdiction '{jurisdiction}' is not part of the initial supported corpus. Only Uttarakhand is supported for the M2.1E prototype.",
        "qualifications": "Unsupported jurisdiction — do not silently retrieve Uttarakhand law when another jurisdiction is requested.",
        "source": "Unsupported jurisdiction guard",
        "source_id": "guard",
        "verification_status": "Unsupported",
        "jurisdiction": jurisdiction,
        "statute": "N/A",
        "act_number": "N/A",
        "commencement": "N/A",
        "document_type": "unsupported guard",
        "provision_identifier": "--",
        "importance_note": "This result indicates the query was rejected at the jurisdiction gate; it does NOT constitute legal advice for the requested jurisdiction.",
    }]


def list_all_provisions() -> List[Dict[str, Any]]:
    """Return all provisions (for testing/inspection)."""
    return PROVISIONS.copy()


def get_unresolved_claims() -> List[Dict[str, Any]]:
    """Return summary of unresolved claims relevant to the retrieval layer."""
    return [
        {
            "claim_id": "UK-UC-001",
            "claim": "Functional status of Rent Authorities per district unverified",
            "relevant_provisions": ["ST-UK-30"],
            "blocks_prototype": True,
            "signal": "unresolved — verify Rent Authority functional status in user's district before relying on statutory remedies",
        },
        {
            "claim_id": "UK-UC-004",
            "claim": "Exemption categories under Section 3 not fully verified per property",
            "relevant_provisions": ["ST-UK-3"],
            "blocks_prototype": True,
            "signal": "unresolved — exemption determination requires per-property verification",
        },
        {
            "claim_id": "UK-UC-006",
            "claim": "Commencement applicability to pre-existing deposits unresolved",
            "relevant_provisions": ["ST-UK-1(3)", "ST-UK-47"],
            "blocks_prototype": True,
            "signal": "unresolved — whether Act applies to deposits paid before 01.01.2023 requires legal interpretation",
        },
    ]


def list_all_unresolved_claims() -> List[Dict[str, Any]]:
    """Return all unresolved claims."""
    return get_unresolved_claims()

