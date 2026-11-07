#!/usr/bin/env python3
import re
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from backend.app.embeddings import embed_text, embed_batch, get_embedding_dimension
KNOWN_JURISDICTIONS = {"Uttarakhand"}
CHROMA_PERSIST_DIR = Path("/home/smit-bafna/Projects/kuku/backend/persistent_chroma")
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_ID_PREFIX = "CHUNK-"
chroma_client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
collection_name = "uttarakhand_provisions"
collection = chroma_client.get_or_create_collection(name=collection_name, metadata={"hnsw_space": "cosine"})


def parse_provision_inventory(path: Path) -> List[Dict[str, Any]]:
    """Parse the provision_inventory.md file and return list of provision dicts."""
    content = path.read_text(encoding="utf-8").strip()
    lines_text = content.splitlines()

    header_idx = None
    separator_idx = None
    for i, line in enumerate(lines_text):
        if "| ID" in line and "| Section" in line:
            header_idx = i
        if line.strip().startswith("|---") or line.strip().startswith("| ---"):
            separator_idx = i

    if header_idx is None or separator_idx is None:
        return []

    header_line = lines_text[header_idx].strip().split("|")
    headers = [h.strip() for h in header_line if h.strip()]

    provisions = []
    for line in lines_text[separator_idx + 1:]:
        row = line.strip().split("|")
        if len(row) < len(headers):
            continue
        cells = [c.strip() for c in row if c.strip()]
        cells = cells[: len(headers)]
        while len(cells) < len(headers):
            cells.append("")
        entry = dict(zip(headers, cells))
        if entry.get("ID"):
            entry["id"] = entry.pop("ID")
        if entry.get("Section"):
            entry["section"] = entry.pop("Section")
        provisions.append(entry)

    return provisions


def parse_knowledge_markdown(kb_dir: Path) -> Dict[str, Dict[str, Any]]:
    """Parse all Markdown files in the knowledge-base directory."""
    corpus: Dict[str, Dict[str, Any]] = {}
    md_files = sorted(kb_dir.glob("*.md"))

    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        provision_ids = re.findall(r"ST-UK-\S+", text)
        section_refs = re.findall(r"S \d+(?:\(\d+\))?", text)

        corpus[md_file.stem] = {
            "path": str(md_file),
            "filename": md_file.name,
            "provision_ids": list(set(provision_ids)),
            "section_refs": list(set(section_refs)),
            "text": text,
        }

    return corpus


def build_chunks_from_provisions(
    provisions: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Build provision-level chunks from the PROVISIONS list.

    Each provision becomes one chunk. The chunk text combines the legal
    proposition and qualifications, keeping them distinct. All metadata is
    preserved as chunk metadata. Chunk IDs are stable: CHUNK-{provision_id}.
    """
    chunks = []
    for prov in provisions:
        prov_id = prov.get("id", "")
        section = prov.get("section", "")
        legal_proposition = prov.get("legal_proposition", "")
        qualifications = prov.get("qualifications", "")

        # Build chunk text: keep statutory text distinct from explanatory summaries
        text_parts = []
        if section:
            text_parts.append(f"S {section}")
        if legal_proposition:
            text_parts.append(f"Proposition: {legal_proposition}")
        if qualifications:
            text_parts.append(f"Qualifications: {qualifications}")

        chunk_text = " | ".join(text_parts) if text_parts else ""

        # Stable chunk ID
        chunk_id = f"{CHUNK_ID_PREFIX}{prov_id}"

        # Build metadata — preserve every field wherever supported by source data
        metadata = {
            "provision_id": prov_id,
            "section": section,
            "legal_proposition": legal_proposition,
            "qualifications": qualifications,
            "source": prov.get("source", ""),
            "source_id": prov.get("source_id", ""),
            "source_url": prov.get("source_url", ""),
            "verification_status": prov.get("verification_status", ""),
            "jurisdiction": prov.get("jurisdiction", ""),
            "statute": prov.get("statute", ""),
            "act_number": prov.get("act_number", ""),
            "commencement": prov.get("commencement", ""),
            "document_type": prov.get("document_type", "statutory provision"),
            "provision_identifier": prov.get("provision_identifier", section),
        }

        chunks.append(
            {
                "id": chunk_id,
                "text": chunk_text,
                "metadata": metadata,
            }
        )

    return chunks


def build_chunks_from_markdown_corpus(
    corpus: Dict[str, Dict[str, Any]],
    provisions_map: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Build chunks from the Markdown corpus, using the provisions_map for metadata.

    The Markdown corpus is the source of truth. For each file, we create a chunk
    that includes the relevant provision information. If a provision ID from the
    inventory is found in the markdown, we use that provision's full metadata.
    """
    chunks = []
    seen_ids = set()

    for filename, file_info in corpus.items():
        text = file_info["text"]
        provision_ids = file_info.get("provision_ids", [])
        section_refs = file_info.get("section_refs", [])

        for prov_id in provision_ids:
            if prov_id in provisions_map:
                prov = provisions_map[prov_id]
                section = prov.get("section", "")
                legal_proposition = prov.get("legal_proposition", "")
                qualifications = prov.get("qualifications", "")

                # Build chunk text
                text_parts = []
                if section:
                    text_parts.append(f"S {section}")
                if legal_proposition:
                    text_parts.append(f"Proposition: {legal_proposition}")
                if qualifications:
                    text_parts.append(f"Qualifications: {qualifications}")

                chunk_text = " | ".join(text_parts) if text_parts else ""

                chunk_id = f"{CHUNK_ID_PREFIX}{prov_id}"

                if chunk_id in seen_ids:
                    continue
                seen_ids.add(chunk_id)

                metadata = {
                    "provision_id": prov_id,
                    "section": section,
                    "legal_proposition": legal_proposition,
                    "qualifications": qualifications,
                    "source": prov.get("source", ""),
                    "source_id": prov.get("source_id", ""),
                    "source_url": prov.get("source_url", ""),
                    "verification_status": prov.get("verification_status", ""),
                    "jurisdiction": prov.get("jurisdiction", ""),
                    "statute": prov.get("statute", ""),
                    "act_number": prov.get("act_number", ""),
                    "commencement": prov.get("commencement", ""),
                    "document_type": prov.get("document_type", "statutory provision"),
                    "provision_identifier": prov.get("provision_identifier", section),
                    "corpus_source": filename,
                }

                chunks.append(
                    {
                        "id": chunk_id,
                        "text": chunk_text,
                        "metadata": metadata,
                    }
                )
            # Also create a generic chunk for section refs not tied to a full provision
            for sec_ref in section_refs:
                # Try to extract a short ID from the section ref
                m = re.search(r"S (\d+)(?:\(\d+\))?", sec_ref)
                if m:
                    short_id = f"ST-UK-{m.group(1)}"
                    if short_id in seen_ids:
                        continue
                    seen_ids.add(short_id)
                    metadata = {
                        "provision_id": short_id,
                        "section": sec_ref,
                        "legal_proposition": "",
                        "qualifications": "",
                        "source": "Knowledge base markdown",
                        "source_id": "KNOWLEDGE-BASE",
                        "source_url": "",
                        "verification_status": "Unverified from markdown",
                        "jurisdiction": "Uttarakhand",
                        "statute": "Uttarakhand Tenancy Act 2021",
                        "act_number": "Act No 02 of 2022",
                        "commencement": "01.01.2023",
                        "document_type": "statutory provision",
                        "provision_identifier": sec_ref,
                        "corpus_source": filename,
                    }
                    chunks.append(
                        {
                            "id": f"{CHUNK_ID_PREFIX}{short_id}",
                            "text": f"S {sec_ref}",
                            "metadata": metadata,
                        }
                    )

    return chunks
