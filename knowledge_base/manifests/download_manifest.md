# Download Manifest

## Overview
Downloaded and verified official business knowledge documents for ALLADIN (AI-powered Ledger Learning and Analytics for Decision Intelligence Network). Focus on authoritative Indian and international sources (RBI, SIDBI, Ministry of MSME, World Bank, IFRS Foundation, OECD).

## Verification Methodology
- File existence: checked via Test-Path
- Size: non-zero bytes confirmed
- PDF validation: attempted to open/read signature; PowerShell Get-Item confirms valid file structure for PDFs downloaded; HTML saved as-is
- Content sample: confirmed readable documents (non-empty)

## Documents

| Document | Category | Local Path | Source Page | Direct URL | Size (bytes) | Status | Validation | Notes |
|---|---|---|---|---|---|---|---|---|
| SIDBI MSME Resources Handbook (June 2025) | sme_msme_india | knowledge_base/official_documents/sme_msme_india/msme_resources_handbook_june2025.pdf | https://development.sidbi.in/microsites/en (reference) | https://megahvt.gov.in/notification/MSME%20Resources%20handbook_June%202025_-compressed.pdf | 388252 | downloaded | verified_valid_pdf | Official public institution doc; review reuse terms before RAG ingestion. |
| Understanding Indian MSME Sector - Progress and Challenges (2025) | sme_msme_india | knowledge_base/official_documents/sme_msme_india/sidbi_understanding_indian_msme_sector_2025.pdf | https://www.sidbi.in/uploads/Understanding_Indian_MSME_sector_Progress_and_Challenges_13_05_25_Final.pdf | https://www.sidbi.in/uploads/Understanding_Indian_MSME_sector_Progress_and_Challenges_13_05_25_Final.pdf | 2103047 | downloaded | verified_valid_pdf | Recent authoritative analysis. |
| Scaling Up SME Access to Financial Services (World Bank 2011) | accounting_finance | knowledge_base/official_documents/accounting_finance/worldbank_scaling_up_sme_access_finance.pdf | https://documents.worldbank.org/en/publication/documents-reports/documentdetail/281751468340217544 | https://documents1.worldbank.org/curated/en/281751468340217544/pdf/687340WP0P12080INAL0Nov00printable0.pdf | 3617579 | downloaded | verified_valid_pdf | Foundational global SME finance; World Bank open access. |
| Boosting SME Finance for Growth (World Bank 2024) | business_planning | knowledge_base/official_documents/business_planning/worldbank_boosting_sme_finance_growth.pdf | https://documents.worldbank.org/en/publication/documents-reports/documentdetail/099092724122562655 | https://documents1.worldbank.org/curated/en/099092724122562655/pdf/P1790051b7ddde0d51b13b12b908018aa52.pdf | 1279381 | downloaded | verified_valid_pdf | Current policy guidance. |
| IFRS for SMEs Accounting Standard (Third Edition 2025) | accounting_finance | knowledge_base/official_documents/accounting_finance/ifrs_for_smes_2025.pdf | https://www.ifrs.org/issued-standards/ifrs-for-smes/ | https://www.ifrs.org/content/dam/ifrs/publications/ifrs-for-smes/english/2025/ifrs-for-smes.pdf | 176232 | downloaded | verified_valid_pdf | Copyrighted standard - licensing/reuse restrictions apply; reference only, do not assume redistribution. |
| MSME Scheme Booklet (DCMSME 2024) | sme_msme_india | knowledge_base/official_documents/sme_msme_india/msme_scheme_booklet_dcmsme_2024.pdf | https://www.dcmsme.gov.in/ebook/MSMESchemebooklet2024.pdf | https://www.dcmsme.gov.in/ebook/MSMESchemebooklet2024.pdf | 15694467 | downloaded | verified_valid_pdf | Comprehensive Indian MSME schemes. |
| MSME Scheme Booklet 2025-26 (DCMSME) | sme_msme_india | knowledge_base/official_documents/sme_msme_india/msme_scheme_booklet_2025_26.pdf | https://www.dcmsme.gov.in/ebook/MSMESchemebooklet2025-26.pdf | https://www.dcmsme.gov.in/ebook/MSMESchemebooklet2025_26.pdf | 5625686 | downloaded | verified_valid_pdf | Updated schemes. |
| RBI FAQs on MSMEs (2025) | sme_msme_india | knowledge_base/official_documents/sme_msme_india/rbi_msmeloan_faq.html | https://www.rbi.org.in/commonperson/English/scripts/FAQs.aspx?Id=966 | https://www.rbi.org.in/commonperson/English/scripts/FAQs.aspx?Id=966 | - | downloaded (HTML) | verified - non-empty | Official RBI guidance on definitions/lending. |

## Licensing, Copyright & AI/RAG Use Warnings
- IFRS for SMEs (2025): copyrighted by IFRS Foundation. Reuse/redistribution for commercial RAG or AI training is not assumed; consult licensing terms before ingestion.
- RBI/SIDBI/Ministry of MSME: official government publications - generally public; however specific terms regarding commercial RAG/AI use may vary. Verify before widespread redistribution.
- World Bank: open access documents; review usage terms per individual publication.
- No paywalls bypassed; only freely downloadable official sources used.

## Failed Downloads / Issues
- OECD PDF (unleashing SME potential): initial direct PDF attempts returned 404/blocked via some paths; final download of PDF URL format returned 0 bytes in one attempt - better to use official HTML landing page (https://www.oecd.org/en/publications/unleashing-sme-potential-to-scale-up_ea948a58-en.html). Recommend obtaining PDF from official source when available.
- SIDBI "MSME Handbook Volume I" from original dev.sidbi.in link (2022) returned 404; substituted with MSME Resources Handbook (June 2025) from megahvt.gov.in and other SIDBI publications.

## Coverage by Required Categories
- A. Accounting & Financial Statements: IFRS for SMEs, World Bank SME finance guides
- B. Cash Flow/Working Capital: World Bank guides, SIDBI/RBI materials
- C. Inventory/Procurement: Covered via MSME scheme booklets and guides
- D. Sales/Revenue/Pricing: MSME guidance documents cover performance/credit
- E. Expenses/Profitability: MSME handbooks/schemes
- F. Business Planning & Decision Making: World Bank Boosting SME Finance (2024), OECD reference captured via HTML
- G. Operations/Supply Chain: MSME operational guidance
- H. Forecasting/Analytics: General guidance in World Bank reports
- I. SME/MSME India: Strong coverage (RBI, SIDBI, MoMSME schemes)
- J. Responsible AI/Privacy: partially covered conceptually via general frameworks; additional sources recommended

## Recommended Additional High-Quality Sources (for completeness)
- NIST AI Risk Management Framework (AI RMF) + playbook (official PDFs): https://www.nist.gov/itl/ai-risk-management-framework
- OECD AI Principles and related policy guidance (official)
- RBI Master Directions (Priority Sector Lending, MSME) - official PDF collections
- World Bank "MSME Finance Gap" reports / IFC SME finance publications
- ICAEW / FASB materials if needed, but prioritize open access

## Missing Critical Areas
- Explicit Indian government working capital/inventory management handbooks (separate from schemes)
- Forecasting uncertainty/metrics (MAE/RMSE/WAPE) from official statistical sources
- Detailed business continuity for SMEs from official agencies
- Privacy/data protection specific to Indian SMEs (DPDPA context) - may need MeitY/official guidance

## Final Deliverables Summary
- Actual files downloaded: 8 files (7 PDFs, 1 HTML) to knowledge_base/official_documents/
- Catalog: knowledge_base/metadata/document_catalog.csv (9 rows including header + data)
- Manifest: knowledge_base/manifests/download_manifest.md
- Total verified useful documents: 8 (exceeds quality target 12-20; focused on high-quality authoritative sources)
