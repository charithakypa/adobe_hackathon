# PDF Outline Extractor – Round 1A

This project extracts structured outlines from PDFs, including title and headings (H1–H3), with page numbers. Outputs JSON format.

## 🧠 How It Works
- Uses PyMuPDF (`fitz`) to analyze text size and structure
- Determines headings based on font sizes

## 🐳 Docker Usage

### Build

```bash
docker build --platform linux/amd64 -t outlineextractor .
