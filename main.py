import os
import json
from extractor import extract_outline

def process_all_pdfs(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pdf"):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename.replace(".pdf", ".json"))

            try:
                print(f"📄 Processing: {filename}")
                result = extract_outline(input_path)
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"✅ Saved to: {output_path}")
            except Exception as e:
                print(f"❌ Failed on {filename}: {e}")

if __name__ == "__main__":
    INPUT_DIR = "input"
    OUTPUT_DIR = "output"
    process_all_pdfs(INPUT_DIR, OUTPUT_DIR)
