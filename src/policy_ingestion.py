from pathlib import Path
from typing import List, Dict
import json
import re

from pypdf import PdfReader


# ============================================================
# CONFIGURATION
# ============================================================

POLICY_PATH = Path(
    "data/policy/USGIC-CSCIndividualHealthInsurance_2017-2018.pdf"
)

OUTPUT_PATH = Path(
    "data/policy_chunks.json"
)


# ============================================================
# PDF EXTRACTION
# ============================================================

def extract_policy_pages(pdf_path: Path) -> List[Dict]:
    """
    Extract policy text page-by-page from the PDF.
    """

    reader = PdfReader(str(pdf_path))

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):

        text = page.extract_text() or ""

        text = text.strip()

        if text:
            pages.append(
                {
                    "page": page_number,
                    "text": text
                }
            )

    return pages


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_line(line: str) -> str:
    """
    Normalize whitespace in a line.
    """

    return re.sub(r"\s+", " ", line).strip()


# ============================================================
# SECTION DETECTION
# ============================================================

def detect_section(text: str, current_section: str) -> str:
    """
    Detect major policy sections only.
    """

    lines = [
        clean_line(line)
        for line in text.splitlines()
    ]

    for line in lines:

        if not line:
            continue

        upper = line.upper()

        if upper == "PROSPECTUS":
            return "Prospectus"

        if upper == "CRITICAL ILLNESS":
            return "Critical Illness"

        if upper == "WHAT WE EXCLUDE":
            return "What We Exclude"

        if "CASHLESS CLAIMS PROCESS" in upper:
            return "Cashless Claims Process"

        if upper.startswith("5. POLICY DISPUTES"):
            return "Policy Disputes"

        if "FREE LOOK" in upper:
            return "Free Look Period"

        if upper.startswith("14. CONTRIBUTION"):
            return "Contribution"

        if upper.startswith("15. MULTIPLE POLICIES"):
            return "Multiple Policies"

        if upper.startswith("19. THREE MONTH NOTICE"):
            return "Three Month Notice"

        if upper == "OMBUDSMAN":
            return "Ombudsman"

    return current_section


# ============================================================
# CHUNKING
# ============================================================

def chunk_text(
    text: str,
    page_number: int,
    section: str,
    chunk_size: int = 1500,
    overlap: int = 200,
) -> List[Dict]:
    """
    Split policy text into overlapping chunks.
    """

    chunks = []

    start = 0

    chunk_number = 1

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:

            chunks.append(
                {
                    "chunk_id": (
                        f"page_{page_number}_chunk_{chunk_number}"
                    ),
                    "page": page_number,
                    "section": section,
                    "text": chunk,
                }
            )

        if end >= len(text):
            break

        start = end - overlap

        chunk_number += 1

    return chunks


# ============================================================
# BUILD POLICY CHUNKS
# ============================================================

def build_policy_chunks(
    pdf_path: Path = POLICY_PATH
) -> List[Dict]:
    """
    Extract, section-tag and chunk the complete policy.
    """

    pages = extract_policy_pages(pdf_path)

    all_chunks = []

    current_section = "General Policy"

    for page in pages:

        page_number = page["page"]

        page_text = page["text"]

        current_section = detect_section(
            page_text,
            current_section
        )

        page_chunks = chunk_text(
            text=page_text,
            page_number=page_number,
            section=current_section,
        )

        all_chunks.extend(page_chunks)

    return all_chunks


# ============================================================
# SAVE CHUNKS
# ============================================================

def save_chunks(
    chunks: List[Dict],
    output_path: Path = OUTPUT_PATH
) -> None:
    """
    Save policy chunks as JSON.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            chunks,
            file,
            indent=2,
            ensure_ascii=False
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("Starting policy ingestion...")

    chunks = build_policy_chunks()

    pages = sorted(
        set(chunk["page"] for chunk in chunks)
    )

    sections = sorted(
        set(chunk["section"] for chunk in chunks)
    )

    # Save chunks
    save_chunks(chunks)

    print()
    print(f"Pages extracted : {len(pages)}")
    print(f"Total chunks    : {len(chunks)}")
    print(f"Output file     : {OUTPUT_PATH}")

    print()
    print("Detected sections:")
    print("=" * 60)

    for section in sections:
        print("-", section)

    print()
    print("First 3 chunks:")
    print("=" * 60)

    for chunk in chunks[:3]:

        print(
            f"Chunk ID : {chunk['chunk_id']}"
        )

        print(
            f"Page     : {chunk['page']}"
        )

        print(
            f"Section  : {chunk['section']}"
        )

        print(
            f"Text     : {chunk['text'][:300]}"
        )

        print("-" * 60)