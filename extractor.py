import fitz  # PyMuPDF
from collections import defaultdict, Counter
import re
import math

def merge_title_lines(lines):
    # Merge all largest-font lines within the top 25% of the first page, sorted by y
    if not lines:
        return ""
    lines = sorted(lines, key=lambda l: l["y"])
    return " ".join(l["text"] for l in lines)

def is_address_block(line_objs, idx):
    # Heuristic: block of 3+ consecutive short lines = address
    count = 0
    for i in range(idx, min(idx+4, len(line_objs))):
        if len(line_objs[i]["text"]) < 25:
            count += 1
    return count >= 3

def is_heading_candidate(text, title, all_lines, line, font_size_counts, idx, line_objs):
    # Ignore lines very similar to the title
    if title and text.strip().lower() in title.strip().lower():
        return False
    # Ignore lines that are just numbers, single chars, or mostly punctuation
    if len(text.strip()) < 3:
        return False
    if re.fullmatch(r"[\d. ]+", text):
        return False
    if re.fullmatch(r"[\W_]+", text):
        return False
    # Ignore lines that are too long (likely paragraphs)
    if len(text) > 80:
        return False
    # Ignore lines that are part of a dense block (many lines with same font size on this page)
    if font_size_counts.get(line["font_size"], 0) > 10:
        return False
    # Ignore lines that are repeated on every page (headers/footers)
    if sum(1 for l in all_lines if l["text"] == text) > 2:
        return False
    # Ignore address blocks
    if is_address_block(line_objs, idx):
        return False
    # Prefer lines that are all uppercase or title case
    if not (text.isupper() or text.istitle()):
        # Allow if short and not a paragraph
        if len(text.split()) > 8:
            return False
    return True

def extract_outline(pdf_path):
    doc = fitz.open(pdf_path)

    # Step 1: Get all text spans, grouped by (page, y, font_size)
    lines = defaultdict(list)
    for page_num in range(len(doc)):
        blocks = doc[page_num].get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    y = None
                    font_size = None
                    line_spans = []
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text:
                            line_spans.append(text)
                            y = span["bbox"][1]
                            font_size = span["size"]
                    if line_spans and font_size is not None and y is not None:
                        lines[(page_num + 1, round(y, 1), round(font_size, 1))].append(" ".join(line_spans))

    if not lines:
        return {"title": "", "outline": []}

    # Step 2: Build line objects
    line_objs = []
    for (page, y, font_size), texts in lines.items():
        line_text = " ".join(texts).strip()
        if line_text:
            line_objs.append({
                "text": line_text,
                "font_size": font_size,
                "page": page,
                "y": y
            })

    # Step 3: Title = merge all largest-font lines within top 25% of first page
    first_page_lines = [l for l in line_objs if l["page"] == 1]
    if first_page_lines:
        max_font = max(l["font_size"] for l in first_page_lines)
        # Get page height from PyMuPDF (first page)
        page_height = doc[0].rect.height if len(doc) > 0 else 800
        top_cutoff = page_height * 0.25
        title_lines = [l for l in first_page_lines if l["font_size"] == max_font and l["y"] < top_cutoff]
        title = merge_title_lines(title_lines)
    else:
        title = ""

    # Step 4: Get top 4 unique font sizes
    font_sizes = sorted({l["font_size"] for l in line_objs}, reverse=True)
    h1, h2, h3, h4 = (font_sizes + [0, 0, 0, 0])[:4]  # Ensure at least 4

    # Count font size occurrences per page for density filtering
    font_size_counts = Counter(l["font_size"] for l in line_objs)

    # Step 5: Group consecutive lines with same font size and close y as one heading
    grouped_lines = []
    prev = None
    for l in line_objs:
        if prev and l["font_size"] == prev["font_size"] and l["page"] == prev["page"] and abs(l["y"] - prev["y"]) < 15:
            prev["text"] += " " + l["text"]
            prev["y"] = l["y"]
        else:
            grouped_lines.append(l.copy())
            prev = grouped_lines[-1]

    # Step 6: Categorize headings based on size and heuristics
    outline = []
    for idx, l in enumerate(grouped_lines):
        size = l["font_size"]
        level = None
        if size == h1:
            level = "H1"
        elif size == h2:
            level = "H2"
        elif size == h3:
            level = "H3"
        elif size == h4:
            level = "H4"
        if level:
            # Advanced heuristics for heading candidates
            if not is_heading_candidate(l["text"], title, grouped_lines, l, font_size_counts, idx, grouped_lines):
                continue
            outline.append({
                "level": level,
                "text": l["text"].strip(),
                "page": l["page"]
            })

    return {
        "title": title,
        "outline": outline
    }
