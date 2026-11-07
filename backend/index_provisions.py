#!/usr/bin/env python3
import re
import os
import json
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from backend.app.embeddings import embed_text, embed_batch, get_embedding_dimension
KNOWN_JURISDICTIONS = {"Uttarakhand"}
CHROMA_PERSIST_DIR = Path("/home/smit-bafna/Projects/kuku/backend/persistent_chroma")
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_ID_PREFIX = "CHUNK-"
KNOWLEDGE_BASE_DIR = Path("/home/smit-bafna/Projects/kuku/knowledge-base")
chroma_client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
collection_name = "uttarakhand_provisions"
collection = chroma_client.get_or_create_collection(name=collection_name, metadata={"hnsw_space": "cosine"})


def parse_provision_inventory(path: Path) -> List[Dict[str, Any]]:
    content = path.read_text(encoding="utf-8").strip()
    lines_text = content.splitlines()
    header_indices = []
    for i, line in enumerate(lines_text):
        if "| ID" in line and "| Section" in line:
            header_indices.append(i)
    all_provisions = []
    for hi in header_indices:
        separator_idx = None
        for j in range(hi + 1, len(lines_text)):
            if lines_text[j].strip().startswith("|---") or lines_text[j].strip().startswith("| ---"):
                separator_idx = j
                break
        if separator_idx is None:
            continue
        for j in range(separator_idx + 1, len(lines_text)):
            row = lines_text[j].strip().split("|")
            if len(row) < 7:
                continue
            cells = [c.strip() for c in row[1:7]]
            entry = {
                "id": cells[0] if len(cells) > 0 else "",
                "section": cells[1] if len(cells) > 1 else "",
                "legal_proposition": cells[2] if len(cells) > 2 else "",
                "qualifications": cells[3] if len(cells) > 3 else "",
                "source": cells[4] if len(cells) > 4 else "",
                "verification_status": cells[5] if len(cells) > 5 else "",
            }
            source = entry.get("source", "")
            if "Uttarakhand" in source and not entry.get("jurisdiction"):
                entry["jurisdiction"] = "Uttarakhand"
            if entry.get("id") and entry["id"].startswith("ST-UK-"):
                all_provisions.append(entry)
    return all_provisions


def parse_knowledge_markdown(kb_dir: Path) -> Dict[str, Dict[str, Any]]:
    corpus: Dict[str, Dict[str, Any]] = {}
    import re as re_mod
    md_files = sorted(kb_dir.glob("*.md"))
    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        provision_ids = re_mod.findall(r"ST-UK-\d+(?:\d+\))?", text)
        section_refs = re_mod.findall(r"S \d+(?:\d+\))?", text)
        corpus[md_file.stem] = {
            "path": str(md_file),
            "filename": md_file.name,
            "provision_ids": list(set(provision_ids)),
            "section_refs": list(set(section_refs)),
            "text": text,
        }
    return corpus


def build_chunks_from_provisions(provisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    chunks = []
    seen_ids = set()
    for prov in provisions:
        prov_id = prov.get("id", "")
        section = prov.get("section", "")
        legal_proposition = prov.get("legal_proposition", "")
        qualifications = prov.get("qualifications", "")
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
            "verification_status": prov.get("verification_status", ""),
            "jurisdiction": prov.get("jurisdiction", ""),
            "statute": prov.get("statute", ""),
            "act_number": prov.get("act_number", ""),
            "commencement": prov.get("commencement", ""),
            "document_type": prov.get("document_type", "statutory provision"),
            "provision_identifier": prov.get("provision_identifier", section),
        }
        chunks.append({
            "id": chunk_id,
            "text": chunk_text,
            "metadata": metadata,
        })
    return chunks


def is_provision_valid(prov: Dict[str, Any], known_jurisdictions: set) -> bool:
    prov_id = prov.get("id", "").strip()
    section = prov.get("section", "").strip()
    legal_proposition = prov.get("legal_proposition", "").strip()
    qualifications = prov.get("qualifications", "").strip()
    jurisdiction = prov.get("jurisdiction", "").strip()
    verification_status = prov.get("verification_status", "").strip()
    if not prov_id:
        return False
    if not section:
        return False
    if not legal_proposition:
        return False
    if not qualifications:
        return False
    if jurisdiction not in known_jurisdictions:
        return False
    if not verification_status:
        return False
    if verification_status.lower().startswith("unverified"):
        return False
    return True


def get_rejection_reason(prov: Dict[str, Any]) -> str:
    prov_id = prov.get("id", "unknown")
    jurisdiction = prov.get("jurisdiction", "").strip()
    verification_status = prov.get("verification_status", "").strip()
    section = prov.get("section", "").strip()
    reasons = []
    if not verification_status:
        reasons.append("missing verification status")
    if verification_status.lower().startswith("unverified"):
        reasons.append(f"unverified (status: '{verification_status}')")
    if jurisdiction and jurisdiction not in {"Uttarakhand"}:
        reasons.append(f"unknown jurisdiction: '{jurisdiction}'")
    if not section:
        reasons.append("missing section")
    if not prov_id:
        reasons.append("missing provision ID")
    return "; ".join(reasons) if reasons else "failed legal chunk contract validation"


def rebuild_index() -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "inventory_records_encountered": 0,
        "valid_provisions": [],
        "rejected_provisions": [],
        "generated_chunks": [],
        "successfully_indexed_chunks": 0,
        "embedding_model": EMBEDDING_MODEL_NAME,
        "embedding_dimension": get_embedding_dimension(),
        "collection_name": collection_name,
        "persistence_directory": str(CHROMA_PERSIST_DIR),
        "success": False,
        "failure_reason": None,
    }
    try:
        inventory_path = KNOWLEDGE_BASE_DIR / "provision_inventory.md"
        if not inventory_path.exists():
            raise FileNotFoundError(f"Provision inventory not found: {inventory_path}")
        provisions = parse_provision_inventory(inventory_path)
        report["inventory_records_encountered"] = len(provisions)
        valid_provisions: List[Dict[str, Any]] = []
        rejected_provisions: List[Dict[str, Any]] = []
        seen_prov_ids = set()
        for prov in provisions:
            if is_provision_valid(prov, KNOWN_JURISDICTIONS):
                prov_id = prov.get("id", "")
                if prov_id not in seen_prov_ids:
                    seen_prov_ids.add(prov_id)
                    valid_provisions.append(prov)
                else:
                    rejected_provisions.append(prov)
            else:
                rejected_provisions.append(prov)
        chunks = build_chunks_from_provisions(valid_provisions)
        report["generated_chunks"] = [
            {
                "id": c["id"],
                "text_preview": c["text"][:60] + ("..." if len(c["text"]) > 60 else ""),
                "metadata_keys": sorted(c["metadata"].keys()),
            }
            for c in chunks
        ]
        if not chunks:
            raise ValueError("No valid chunks generated from provisions")
        chunk_texts = [c["text"] for c in chunks]
        embeddings = embed_batch(chunk_texts)
        expected_dim = get_embedding_dimension()
        if len(embeddings) != len(chunks):
            raise ValueError(
                f"Embedding count mismatch: {len(embeddings)} generated, "
                f"{len(chunks)} expected for {len(chunks)} chunks"
            )
        for i, (emb, chunk) in enumerate(zip(embeddings, chunks)):
            if len(emb) != expected_dim:
                raise ValueError(
                    f"Embedding dimension mismatch at index {i}: "
                    f"got {len(emb)}, expected {expected_dim} "
                    f' (chunk ID: {chunk["id"]})'
                )
        rebuild_id = str(uuid.uuid4())
        temp_collection_name = f"{collection_name}_rebuild_{rebuild_id}"
        try:
            temp_collection = chroma_client.create_collection(
                name=temp_collection_name,
                metadata={"hnsw_space": "cosine"},
            )
        except Exception as e:
            raise RuntimeError(f"Failed to create temporary ChromaDB collection: {e}")
        chunk_ids = [c["id"] for c in chunks]
        chunk_embeddings = embeddings
        chunk_documents = [c["text"] for c in chunks]
        chunk_metadatas = [c["metadata"] for c in chunks]
        try:
            temp_collection.add(
                ids=chunk_ids,
                embeddings=chunk_embeddings,
                documents=chunk_documents,
                metadatas=chunk_metadatas,
            )
        except Exception as e:
            chroma_client.delete_collection(temp_collection_name)
            raise RuntimeError(f"Failed to populate temporary collection: {e}")
        # Delete the old collection (existing valid index)
        try:
            chroma_client.delete_collection(collection_name)
        except Exception:
            pass
        # Create new collection with the original name
        try:
            new_collection = chroma_client.create_collection(
                name=collection_name,
                metadata={"hnsw_space": "cosine"},
            )
        except Exception as e:
            chroma_client.delete_collection(collection_name)
            chroma_client.delete_collection(temp_collection_name)
            raise RuntimeError(f"Failed to create new collection: {e}")
        # Add chunks to the new (active) collection
        try:
            new_collection.add(
                ids=chunk_ids,
                embeddings=chunk_embeddings,
                documents=chunk_documents,
                metadatas=chunk_metadatas,
            )
        except Exception as e:
            chroma_client.delete_collection(collection_name)
            chroma_client.delete_collection(temp_collection_name)
            raise RuntimeError(f"Failed to populate new collection: {e}")
        # Delete the temporary collection – replacement is complete
        try:
            chroma_client.delete_collection(temp_collection_name)
        except Exception:
            pass
        report["success"] = True
        report["successfully_indexed_chunks"] = len(chunks)
    except Exception as e:
        report["success"] = False
        report["failure_reason"] = f"{type(e).__name__}: {e}"
        try:
            for col in chroma_client.list_collections():
                if col.name.startswith(f"{collection_name}_rebuild_"):
                    chroma_client.delete_collection(col.name)
        except Exception:
            pass
    return report
