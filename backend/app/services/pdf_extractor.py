"""
PDF Document Extractor.
Safely extracts candidate invoice/receipt metadata, dates, amounts, and line items from PDF files
with arithmetic consistency verification and untrusted text isolation.
"""
from datetime import date
import re
from typing import Any, Dict, List, Optional, Tuple
from app.services.import_normalizer import ImportNormalizer
from app.services.import_parser import ImportParserService


class PDFExtractorService:
    @classmethod
    def extract_document(cls, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Extract text and identify financial candidate fields from PDF.
        Returns candidate fields, line items, arithmetic checks, and raw text.
        """
        raw_text = ImportParserService.parse_pdf_text(file_bytes)
        clean_lines = [l.strip() for l in raw_text.splitlines() if l.strip()]

        # 1. Document / Invoice Number
        doc_number = cls._extract_doc_number(raw_text)

        # 2. Dates
        issue_date, due_date = cls._extract_dates(raw_text)

        # 3. Counterparty (Vendor / Customer)
        vendor_name, customer_name = cls._extract_parties(raw_text)

        # 4. Amounts
        subtotal, tax_amount, total_amount, currency = cls._extract_amounts(raw_text)

        # 5. Line items
        line_items = cls._extract_line_items(clean_lines)

        # 6. Arithmetic verification
        arithmetic = cls._verify_arithmetic(subtotal, tax_amount, total_amount, line_items)

        # Suggest document type
        lower_text = raw_text.lower()
        if "receipt" in lower_text or "expense" in lower_text:
            doc_type = "receipt"
        elif "invoice" in lower_text or "bill" in lower_text:
            doc_type = "invoice"
        else:
            doc_type = "unknown"

        return {
            "file_name": filename,
            "document_type": doc_type,
            "candidate_fields": {
                "document_number": {
                    "value": doc_number,
                    "confidence": "high" if doc_number else "missing",
                    "requires_review": not bool(doc_number),
                },
                "issue_date": {
                    "value": str(issue_date) if issue_date else None,
                    "confidence": "high" if issue_date else "missing",
                    "requires_review": not bool(issue_date),
                },
                "due_date": {
                    "value": str(due_date) if due_date else None,
                    "confidence": "medium" if due_date else "none",
                    "requires_review": False,
                },
                "counterparty": {
                    "vendor": vendor_name,
                    "customer": customer_name,
                    "confidence": "medium" if (vendor_name or customer_name) else "missing",
                    "requires_review": not bool(vendor_name or customer_name),
                },
                "currency": {
                    "value": currency or "USD",
                    "confidence": "high" if currency else "default",
                },
                "subtotal": {
                    "value": subtotal,
                    "confidence": "high" if subtotal is not None else "missing",
                    "requires_review": subtotal is None,
                },
                "tax_amount": {
                    "value": tax_amount or 0.0,
                    "confidence": "medium" if tax_amount is not None else "zero_assumed",
                },
                "total_amount": {
                    "value": total_amount,
                    "confidence": "high" if total_amount is not None else "missing",
                    "requires_review": total_amount is None,
                },
            },
            "line_items": line_items,
            "arithmetic_check": arithmetic,
            "raw_text_preview": raw_text[:4000],
            "disclaimer": (
                "Extracted text is untrusted. Please review and edit all fields before committing to ERP records."
            ),
        }

    @classmethod
    def _extract_doc_number(cls, text: str) -> Optional[str]:
        patterns = [
            r"(?i)(?:invoice|inv|bill|receipt|order)\s*(?:no|num|number|#)?\s*[:.\-]?\s*([a-zA-Z0-9\-_/]{3,30})",
            r"(?i)#\s*([a-zA-Z0-9\-_/]{4,25})",
        ]
        for p in patterns:
            match = re.search(p, text)
            if match:
                candidate = match.group(1).strip()
                if not candidate.lower().startswith(("date", "total", "amount", "usd", "inr")):
                    return candidate
        return None

    @classmethod
    def _extract_dates(cls, text: str) -> Tuple[Optional[date], Optional[date]]:
        normalizer = ImportNormalizer()
        issue_date: Optional[date] = None
        due_date: Optional[date] = None

        # Look for issue date
        issue_matches = re.findall(
            r"(?i)(?:invoice\s*date|bill\s*date|date|issued)[\s:]*([0-9]{1,4}[/\-.][0-9]{1,2}[/\-.][0-9]{1,4})",
            text,
        )
        for cand in issue_matches:
            d, err = normalizer.normalize_date(cand)
            if d and not err:
                issue_date = d
                break

        # Look for due date
        due_matches = re.findall(
            r"(?i)(?:due\s*date|payment\s*due)[\s:]*([0-9]{1,4}[/\-.][0-9]{1,2}[/\-.][0-9]{1,4})",
            text,
        )
        for cand in due_matches:
            d, err = normalizer.normalize_date(cand)
            if d and not err:
                due_date = d
                break

        return issue_date, due_date

    @classmethod
    def _extract_parties(cls, text: str) -> Tuple[Optional[str], Optional[str]]:
        vendor: Optional[str] = None
        customer: Optional[str] = None

        vendor_match = re.search(r"(?i)(?:from|vendor|seller|supplier)[\s:]+([^\n\r,]{3,50})", text)
        if vendor_match:
            vendor = vendor_match.group(1).strip()

        customer_match = re.search(
            r"(?i)(?:to|bill\s+to|billed\s+to|customer|client)[\s:]+([^\n\r,]{3,50})", text
        )
        if customer_match:
            customer = customer_match.group(1).strip()

        return vendor, customer

    @classmethod
    def _extract_amounts(cls, text: str) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[str]]:
        normalizer = ImportNormalizer()
        currency = "USD"
        if "₹" in text or "inr" in text.lower():
            currency = "INR"
        elif "€" in text or "eur" in text.lower():
            currency = "EUR"
        elif "£" in text or "gbp" in text.lower():
            currency = "GBP"

        # Subtotal
        subtotal = None
        sub_match = re.search(
            r"(?i)(?:subtotal|sub-total|taxable\s+value|net\s+amount)[\s:₹$€£A-Z]*([0-9,]+\.[0-9]{2})",
            text,
        )
        if sub_match:
            val, _ = normalizer.normalize_number(sub_match.group(1))
            subtotal = val

        # Tax
        tax_amt = None
        tax_match = re.search(
            r"(?i)(?:tax|vat|gst|total\s+tax)[\s:₹$€£A-Z]*([0-9,]+\.[0-9]{2})",
            text,
        )
        if tax_match:
            val, _ = normalizer.normalize_number(tax_match.group(1))
            tax_amt = val

        # Total
        total_amt = None
        total_match = re.search(
            r"(?i)(?:grand\s+total|amount\s+due|net\s+payable|(?<!sub)total)[\s:₹$€£A-Z]*([0-9,]+\.[0-9]{2})",
            text,
        )
        if total_match:
            val, _ = normalizer.normalize_number(total_match.group(1))
            total_amt = val

        return subtotal, tax_amt, total_amt, currency

    @classmethod
    def _extract_line_items(cls, lines: List[str]) -> List[Dict[str, Any]]:
        """Heuristically find line items with description, quantity, price, total."""
        normalizer = ImportNormalizer()
        items: List[Dict[str, Any]] = []

        # Regex pattern matching: <Description text> <Qty: int/float> <UnitPrice: float> <LineTotal: float>
        item_pattern = re.compile(
            r"^(?P<desc>.+?)\s+(?P<qty>[0-9]+(?:\.[0-9]+)?)\s+(?P<price>[0-9,]+\.[0-9]{2})\s+(?P<total>[0-9,]+\.[0-9]{2})$"
        )

        for line in lines:
            # Skip obvious header rows
            if any(term in line.lower() for term in ("description", "qty", "unit price", "subtotal", "total")):
                continue
            m = item_pattern.match(line.strip())
            if m:
                desc = m.group("desc").strip()
                qty, _ = normalizer.normalize_number(m.group("qty"), default=1.0)
                price, _ = normalizer.normalize_number(m.group("price"), default=0.0)
                total, _ = normalizer.normalize_number(m.group("total"), default=0.0)
                if desc and qty and price is not None and total is not None:
                    items.append({
                        "description": desc,
                        "quantity": qty,
                        "unit_price": price,
                        "line_total": total,
                    })

        return items

    @classmethod
    def _verify_arithmetic(
        cls,
        subtotal: Optional[float],
        tax_amount: Optional[float],
        total_amount: Optional[float],
        line_items: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Verify arithmetic consistency and flag discrepancies."""
        issues: List[str] = []
        is_consistent = True

        # Check subtotal + tax == total
        if subtotal is not None and total_amount is not None:
            expected_total = round(subtotal + (tax_amount or 0.0), 2)
            diff = round(abs(expected_total - total_amount), 2)
            if diff > 0.05:
                is_consistent = False
                issues.append(
                    f"Arithmetic discrepancy: Subtotal ({subtotal}) + Tax ({tax_amount or 0.0}) = {expected_total}, "
                    f"but Total is {total_amount} (difference: {diff})."
                )

        # Check line items sum
        if line_items and subtotal is not None:
            items_sum = round(sum(it.get("line_total", 0.0) for it in line_items), 2)
            diff = round(abs(items_sum - subtotal), 2)
            if diff > 0.10:
                issues.append(
                    f"Line items total ({items_sum}) does not match subtotal ({subtotal})."
                )

        return {
            "is_consistent": is_consistent,
            "discrepancy_detected": len(issues) > 0,
            "issues": issues,
            "calculated_total": round((subtotal or 0.0) + (tax_amount or 0.0), 2) if subtotal is not None else None,
        }
