"""
Import parser service.
Safely parses CSV, Excel (.xlsx), and PDF documents with strict security checks:
- No formula execution / macro execution in spreadsheets (data_only=True)
- Formula injection protection (sanitization of dangerous prefixes like =, +, -, @)
- Strict file size and row limits
- Memory-safe stream processing
"""
import csv
import io
import re
from typing import Any, Dict, List, Optional, Tuple
from app.exceptions import ValidationError

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_ROW_COUNT = 5000
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".pdf"}

DANGEROUS_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def sanitize_cell_value(val: Any) -> Any:
    """Sanitize spreadsheet cell to neutralize CSV/formula injection."""
    if isinstance(val, str):
        val_clean = val.strip()
        # If string starts with a formula character, prefix with single quote to prevent injection
        if val_clean.startswith(DANGEROUS_PREFIXES):
            return "'" + val_clean
        return val_clean
    return val


def detect_csv_delimiter(sample_text: str) -> str:
    """Detect delimiter among comma, semicolon, tab, or pipe."""
    try:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(sample_text, delimiters=[",", ";", "\t", "|"])
        return dialect.delimiter
    except Exception:
        # Fallback heuristic
        counts = {
            ",": sample_text.count(","),
            ";": sample_text.count(";"),
            "\t": sample_text.count("\t"),
            "|": sample_text.count("|"),
        }
        return max(counts, key=counts.get) if max(counts.values()) > 0 else ","


class ImportParserService:
    @staticmethod
    def validate_file_metadata(filename: str, file_bytes: bytes) -> str:
        """Validate filename extension and byte size."""
        if len(file_bytes) == 0:
            raise ValidationError("The uploaded file is empty (0 bytes).")
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise ValidationError(
                f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
            )

        lower_name = filename.lower()
        matched_ext = next((ext for ext in ALLOWED_EXTENSIONS if lower_name.endswith(ext)), None)
        if not matched_ext:
            raise ValidationError(
                f"Unsupported file format for '{filename}'. Allowed formats: .csv, .xlsx, .pdf"
            )
        return matched_ext

    @classmethod
    def parse_csv(
        cls, file_bytes: bytes, max_rows: int = MAX_ROW_COUNT
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Parse CSV content with UTF-8 / latin-1 handling and header sanitization."""
        # Try decoding with utf-8-sig (handles UTF-8 BOM), then utf-8, then latin-1
        text = None
        for enc in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                text = file_bytes.decode(enc)
                break
            except UnicodeDecodeError:
                continue

        if text is None:
            raise ValidationError("Unable to decode CSV file. Please ensure valid UTF-8 encoding.")

        lines = [line for line in text.splitlines() if line.strip()]
        if not lines:
            raise ValidationError("CSV file does not contain any readable data rows.")

        delimiter = detect_csv_delimiter("\n".join(lines[:10]))
        reader = csv.reader(lines, delimiter=delimiter)

        try:
            headers = [h.strip() for h in next(reader, [])]
        except Exception as e:
            raise ValidationError(f"Failed to parse CSV headers: {str(e)}")

        if not headers:
            raise ValidationError("No column headers found in CSV file.")

        # Clean headers
        headers = [re.sub(r"[\x00-\x1f\x7f-\x9f]", "", h) for h in headers]

        rows: List[Dict[str, Any]] = []
        for row_idx, raw_row in enumerate(reader, start=1):
            if row_idx > max_rows:
                break
            if not any(raw_row):
                continue
            row_dict: Dict[str, Any] = {}
            for h_idx, header in enumerate(headers):
                val = raw_row[h_idx] if h_idx < len(raw_row) else ""
                row_dict[header] = sanitize_cell_value(val)
            rows.append(row_dict)

        if not rows:
            raise ValidationError("CSV file contains headers but no data rows.")

        return headers, rows

    @classmethod
    def parse_xlsx(
        cls, file_bytes: bytes, sheet_name: Optional[str] = None, max_rows: int = MAX_ROW_COUNT
    ) -> Tuple[List[str], List[Dict[str, Any]], List[str]]:
        """Parse Excel .xlsx file safely using openpyxl in data_only mode (no formulas/macros executed)."""
        import openpyxl

        try:
            wb = openpyxl.load_workbook(
                filename=io.BytesIO(file_bytes),
                read_only=True,
                data_only=True,  # Crucial: evaluates formula results, does not execute code
                keep_vba=False,   # Never load VBA macros
            )
        except Exception as e:
            raise ValidationError(f"Invalid or corrupted Excel workbook: {str(e)}")

        sheet_names = wb.sheetnames
        if not sheet_names:
            raise ValidationError("Excel workbook does not contain any worksheets.")

        active_sheet_name = sheet_name if (sheet_name and sheet_name in sheet_names) else sheet_names[0]
        ws = wb[active_sheet_name]

        rows_iter = ws.iter_rows(values_only=True)
        try:
            raw_header = next(rows_iter, None)
        except Exception as e:
            raise ValidationError(f"Failed reading worksheet: {str(e)}")

        if not raw_header:
            raise ValidationError(f"Worksheet '{active_sheet_name}' is empty.")

        headers: List[str] = []
        for idx, col in enumerate(raw_header):
            if col is not None and str(col).strip():
                headers.append(str(col).strip())
            else:
                headers.append(f"Column_{idx + 1}")

        rows: List[Dict[str, Any]] = []
        for row_idx, row_values in enumerate(rows_iter, start=1):
            if row_idx > max_rows:
                break
            if not row_values or not any(v is not None for v in row_values):
                continue
            row_dict: Dict[str, Any] = {}
            for h_idx, header in enumerate(headers):
                val = row_values[h_idx] if h_idx < len(row_values) else None
                if val is not None:
                    row_dict[header] = sanitize_cell_value(val)
                else:
                    row_dict[header] = ""
            rows.append(row_dict)

        wb.close()

        if not rows:
            raise ValidationError(f"Worksheet '{active_sheet_name}' contains headers but no data rows.")

        return headers, rows, sheet_names

    @classmethod
    def parse_pdf_text(cls, file_bytes: bytes, max_pages: int = 20) -> str:
        """Extract text from PDF pages safely using pypdf."""
        import pypdf

        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        except Exception as e:
            raise ValidationError(f"Failed to open or parse PDF document: {str(e)}")

        if len(reader.pages) == 0:
            raise ValidationError("The uploaded PDF has no readable pages.")

        extracted_text_chunks: List[str] = []
        pages_to_read = min(len(reader.pages), max_pages)

        for page_idx in range(pages_to_read):
            try:
                page = reader.pages[page_idx]
                text = page.extract_text() or ""
                if text.strip():
                    extracted_text_chunks.append(f"--- Page {page_idx + 1} ---\n" + text)
            except Exception as e:
                extracted_text_chunks.append(f"--- Page {page_idx + 1} (Extraction Error: {str(e)}) ---")

        full_text = "\n\n".join(extracted_text_chunks).strip()
        if not full_text:
            raise ValidationError(
                "No readable text could be extracted from this PDF. "
                "If this is a scanned image or photograph, please use manual entry as OCR is not enabled."
            )

        return full_text
