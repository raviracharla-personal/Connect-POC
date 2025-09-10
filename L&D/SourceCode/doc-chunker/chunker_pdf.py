import fitz  # PyMuPDF
import re
import json
import os
import base64
import logging
from pathlib import Path
from dotenv import load_dotenv
from openai import AzureOpenAI  

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load environment variables
load_dotenv()

# Retrieve environment variables for LLM initialization
api_key = os.getenv("AZURE_OPENAI_API_KEY")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")
print("api_key:", "****" if api_key else None)

# Initialize Azure OpenAI client
client = AzureOpenAI(
    azure_deployment="gpt-4.1",
    api_version=api_version,
    api_key=api_key,
    azure_endpoint=azure_endpoint,
    max_retries=2,
)

# Define the police-oriented prompt globally
POLICE_CAPTION_PROMPT = (
    "Describe this image as a police officer would, highlighting elements pertinent to a report, "
    "investigation, crime scene, equipment, personnel, or procedural aspect. "
    "Focus on observable facts and direct, professional language. "
    "Use clear, domain-relevant language. Avoid overly verbose or general descriptions."
)

def _encode_image(image_path):
    """Encodes an image to base64 string."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        logging.error(f"Image file not found: {image_path}")
        return None
    except Exception as e:
        logging.error(f"Error encoding image {image_path}: {e}")
        return None


def generate_caption_with_azure(client, prompt, image_b64, deployment="gpt-4.1"):
    """Generate an image caption using Azure OpenAI."""
    try:
        response = client.chat.completions.create(
            model=deployment,  # Azure deployment model name
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
                    ],
                }
            ],
            temperature=0,
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error generating caption: {e}")
        return f"Error: Failed to generate caption. {e}"


class PDFSectionExtractor:
    """Extracts structured content (text, tables, images) from a PDF."""

    def __init__(self, pdf_path: str, caption_prompt: str):
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"The file {pdf_path} was not found.")
        self.pdf_path = os.path.basename(pdf_path)
        self.doc = fitz.open(pdf_path)
        self.caption_prompt = caption_prompt

        # Metadata
        self.title = None
        self.subtitle = None

        self.content_y_start = 70
        self.content_y_end = 800

        self.section_header_regex = re.compile(
            r"^\s*(?:Section\s+(\d+):|((\d{1,2}(?:\.\d{1,2})*)))\s+(.*)", re.IGNORECASE
        )
        self.toc_title_regex = re.compile(r"^\s*Table of Contents\s*$", re.IGNORECASE)

        self.chunks = []
        self.section_title_map = {}

        self._extract_document_metadata()

    def _extract_document_metadata(self):
        if not self.doc or self.doc.page_count == 0:
            logging.warning("Empty PDF, cannot extract metadata.")
            return

        first_page = self.doc[0]
        blocks = first_page.get_text("blocks", sort=True)

        relevant_blocks = [
            block[4].strip()
            for block in blocks
            if self._is_in_content_area(block[:4]) and len(block[4].strip()) > 10
        ]

        if relevant_blocks:
            self.title = relevant_blocks[0]
            logging.info(f"Extracted Document Title: {self.title}")
            if len(relevant_blocks) > 1:
                self.subtitle = relevant_blocks[1]
                logging.info(f"Extracted Document Subtitle: {self.subtitle}")

    def _is_in_content_area(self, bbox: tuple) -> bool:
        _x0, y0, _x1, y1 = bbox
        return self.content_y_start < y0 and y1 < self.content_y_end

    def _parse_section_header(self, text: str) -> tuple | None:
        match = self.section_header_regex.match(text)
        if match:
            num_part1 = match.group(1)
            num_part2 = match.group(2)
            title = match.group(4).strip()
            number = (num_part1 if num_part1 else num_part2).strip(".")
            return number, title
        return None

    def _get_parent_info(self, section_number: str) -> tuple:
        if "." not in section_number:
            return None, None
        parent_number = ".".join(section_number.split(".")[:-1])
        parent_title = self.section_title_map.get(parent_number)
        return parent_number, parent_title

    def _convert_table_to_flattened_plain_text(self, table_data: list) -> str:
        if not table_data:
            return ""

        flattened_content = []

        for h in table_data[0]:
            cleaned_header = str(h).replace("\n", " ").strip() if h else ""
            flattened_content.append(cleaned_header)

        for row in table_data[1:]:
            for cell_value in row:
                cleaned_value = str(cell_value).replace("\n", " ").strip() if cell_value else ""
                flattened_content.append(cleaned_value)

        return "\n".join(flattened_content)

    def _finalize_section(self, section_data: dict):
        if section_data:
            section_data["content"] = re.sub(r"\n{3,}", "\n\n", section_data["content"]).strip()
            if section_data["content"] or section_data.get("has_content"):
                section_data.pop("has_content", None)
                section_data_with_metadata = {
                    "document": self.pdf_path,
                    "title": self.title,
                    "subtitle": self.subtitle,
                    **section_data,
                }
                self.chunks.append(section_data_with_metadata)

    def _generate_caption_for_image(self, image_path: str) -> str:
        image_name = Path(image_path).name
        logging.info(f"Generating caption for image: {image_name}")
        image_data = _encode_image(image_path)

        if image_data is None:
            return f"Error: Could not encode image {image_name}"

        return generate_caption_with_azure(
            client, self.caption_prompt, image_data, deployment="gpt-4.1"
        )

    def extract(self, image_dir: str = "extracted_images_updated_22082025") -> list:
        os.makedirs(image_dir, exist_ok=True)
        toc_pages = self._process_toc()
        active_section = None

        print("Starting PDF content and image extraction...")

        for page_num, page in enumerate(self.doc):
            page_number = page_num + 1
            if page_number in toc_pages:
                continue

            page_blocks = page.get_text("blocks", sort=False)
            page_images = page.get_images(full=True)
            page_tables = page.find_tables()

            elements = []

            for block in page_blocks:
                if self._is_in_content_area(block[:4]):
                    elements.append({"type": "text", "y0": block[1], "data": block})

            for img_index, img_info in enumerate(page_images):
                img_bbox = page.get_image_bbox(img_info)
                if self._is_in_content_area(img_bbox):
                    elements.append({"type": "image", "y0": img_bbox[1], "data": (img_info, img_bbox, img_index)})

            for table in page_tables:
                if self._is_in_content_area(table.bbox):
                    elements.append({"type": "table", "y0": table.bbox[1], "data": table})

            elements.sort(key=lambda x: x["y0"])

            for element in elements:
                if element["type"] == "text":
                    block = element["data"]
                    block_text = block[4]
                    header_info = self._parse_section_header(block_text.strip())

                    if header_info:
                        self._finalize_section(active_section)
                        number, title = header_info
                        self.section_title_map[number] = title
                        parent_number, parent_title = self._get_parent_info(number)

                        active_section = {
                            "type": "section",
                            "page_number": page_number,
                            "section_number": number,
                            "section_title": title,
                            "parent_section_number": parent_number,
                            "parent_section_title": parent_title,
                            "content": "",
                            "has_content": False,
                        }
                    elif active_section:
                        active_section["content"] += block_text
                        active_section["has_content"] = True

                elif element["type"] == "image":
                    img_info, img_bbox, img_index = element["data"]
                    try:
                        xref = img_info[0]
                        base_image = self.doc.extract_image(xref)
                        image_filename = f"p{page_number}_i{img_index}.{base_image['ext']}"
                        image_path = os.path.join(image_dir, image_filename)

                        with open(image_path, "wb") as f:
                            f.write(base_image["image"])

                        generated_caption = self._generate_caption_for_image(image_path)

                        img_chunk = {
                            "document": self.pdf_path,
                            "title": self.title,
                            "subtitle": self.subtitle,
                            "type": "image",
                            "page_number": page_number,
                            "payload": {"path": image_path},
                            "content": generated_caption,
                        }

                        if active_section:
                            img_chunk["section_number"] = active_section.get("section_number")
                            img_chunk["section_title"] = active_section.get("section_title")
                            img_chunk["parent_section_number"] = active_section.get("parent_section_number")
                            img_chunk["parent_section_title"] = active_section.get("parent_section_title")

                        self.chunks.append(img_chunk)

                        if active_section:
                            active_section["content"] += f"\n\n--- Image: {image_filename} ---\n\n"
                            active_section["has_content"] = True

                    except Exception as e:
                        logging.error(f"Could not process image on page {page_number}: {e}")

                elif element["type"] == "table":
                    table = element["data"]
                    extracted_data = table.extract()
                    table_plain_text = self._convert_table_to_flattened_plain_text(extracted_data)
                    if active_section:
                        active_section["content"] += table_plain_text
                        active_section["has_content"] = True

        self._finalize_section(active_section)
        print("Finished PDF content and image extraction.")
        return self.chunks

    def _process_toc(self) -> set:
        toc_pages = set()
        for page_num, page in enumerate(self.doc, 1):
            if any(self.toc_title_regex.search(b[4]) for b in page.get_text("blocks")):
                toc_content = ""
                for i in range(page_num - 1, len(self.doc)):
                    toc_page = self.doc[i]
                    is_still_toc = False
                    blocks = toc_page.get_text("blocks")
                    for block in blocks:
                        text = block[4]
                        if "..." in text and self._is_in_content_area(block[:4]):
                            cleaned_line = re.sub(r"\s*\.+\s*\d+\s*$", "", text).strip()
                            toc_content += cleaned_line + "\n"
                            is_still_toc = True
                    if is_still_toc:
                        toc_pages.add(i + 1)
                    elif i > page_num - 1 and not is_still_toc:
                        break

                self.chunks.append(
                    {
                        "document": self.pdf_path,
                        "title": self.title,
                        "subtitle": self.subtitle,
                        "type": "TOC",
                        "page_number_start": page_num,
                        "page_number_end": max(toc_pages) if toc_pages else page_num,
                        "content": toc_content.strip(),
                    }
                )
                return toc_pages
        return toc_pages

    def save_to_json(self, output_path: str):
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(self.chunks)} chunks to {output_path}")


if __name__ == "__main__":
    pdf_filename = "Edited Connect Investigation Training Manual v25.0.pdf"

    if not os.path.exists(pdf_filename):
        print(f"Error: The PDF file '{pdf_filename}' was not found.")
    else:
        output_json_filename = "extracted_content.json"
        image_output_dir = "extracted_images"

        extractor = PDFSectionExtractor(pdf_path=pdf_filename, caption_prompt=POLICE_CAPTION_PROMPT)
        extractor.extract(image_dir=image_output_dir)
        extractor.save_to_json(output_path=output_json_filename)
