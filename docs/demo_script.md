# 10-Minute Hackathon Demo Script: Agentic SOV Cleansing

This script provides a structured walkthrough designed for judges and evaluators to demonstrate the end-to-end capabilities of the **Agentic SOV Cleansing & Intelligence System**.

---

## ⏱️ Minute 0:00 - 1:30 | Problem & Architecture Overview
1. **The Core Business Problem:**
   * Commercial Property & Casualty (P&C) Statement of Values (SOV) spreadsheets arrive in chaotic, inconsistent structures (non-standard column names, offset header rows, merged title banners, currency signs, negative values).
   * Manual analyst cleansing takes hours per submission, creating pricing bottlenecks and exposure modeling errors.
2. **The 4-Agent Architecture:**
   * Point out the **Agent Workflow Diagram** on the screen:
     * **Agent 1:** Sheet Intelligence & Discovery
     * **Agent 2:** Schema Mapping (Two-Pass: RapidFuzz + Sentence-BERT Embeddings)
     * **Agent 3:** Data Quality & Reasoning (11+ Anomaly Categories)
     * **Human-in-the-Loop Gateway:** Review, Accept, Reject with Feedback, Re-reason
     * **Agent 4:** Controlled Transformation & Strict 17-Column Output Validation

---

## ⏱️ Minute 1:30 - 3:00 | Ingestion & Sheet Discovery (Agent 1)
1. **Load Sample 3 (Multi-Sheet Messy) or Sample 2 (Complex Semantic):**
   * Click **`Sample 3: Multi-Sheet & Dispersed`** (or drag and drop your own `.xlsx`/`.csv`).
   * Show that within milliseconds, Agent 1:
     * Scanned 3 worksheets (`Instructions & Notes`, `Location Schedule`, `Summary Rollup`).
     * Identified `Instructions & Notes` as **Reject** (metadata/notes).
     * Identified `Location Schedule` as **Primary** (confidence $94\%$).
     * Automatically detected that the header row is at **Row 4** (skipping the title banner and merged rows 1–3).
   * Show the raw sheet preview table highlighting row 4 as headers.

---

## ⏱️ Minute 3:00 - 5:00 | Two-Pass Schema Mapping (Agent 2)
1. **Navigate to `2. Schema Mapping` Tab:**
   * Point out the overall accuracy ($98\%$, exceeding the $74\%$ hackathon target).
   * Highlight key semantic and fuzzy mappings:
     * `Bldg Repl Cost` $\rightarrow$ `Building Value` ($98\%$ confidence, method: Fuzzy/Semantic)
     * `Fire Prot.` $\rightarrow$ `Fire Sprinklers (Y/N)` ($98\%$ confidence)
     * `Time Element BI` $\rightarrow$ `BI` ($98\%$ confidence)
     * `Levels` $\rightarrow$ `Storeys` ($98\%$ confidence)
   * Show that every mapping displays:
     * Confidence percentage badge
     * Resolution method (`exact`, `fuzzy`, `semantic`, `llm`)
     * Plain-English domain explanation
   * Demonstrate the interactive dropdown: a human reviewer can override or adjust any mapping if needed.

---

## ⏱️ Minute 5:00 - 7:00 | Data Quality & Anomaly Detection (Agent 3)
1. **Navigate to `3. Data Quality & Profiling` Tab:**
   * Show the **Intake Quality Score** (e.g. $51/100$ on messy files, flagging that it requires human review).
   * Review the anomaly cards categorized by severity:
     * **Critical:** Negative monetary values (e.g. `-$450,000` Building Value).
     * **High:** Future year built (e.g. `2035`), non-standard sprinkler codes (`Yes`, `100%`, `NFPA 13`), floor count $< 1$.
     * **Medium:** Currency symbols and commas inside numeric values (`$1,250,000`), full state names (`California`, `Texas`).
     * **Low:** Preserved blank fields.
   * Switch to the **Completeness** subtab to display the per-field non-null percentage bars for all 17 schema fields.

---

## ⏱️ Minute 7:00 - 8:30 | Human-in-the-Loop Gateway & AI Re-reasoning
1. **Navigate to `4. Human Approval Queue` Tab:**
   * Explain **Rule C-01**: The system *never* silently mutates data without explicit human sign-off.
   * Demonstrate **Batch Approval:**
     * Click **`Approve All High Confidence (≥ 90%)`**.
     * Watch high-confidence cards transition to green "Approved" status instantly.
2. **Demonstrate AI Re-Reasoning (Bonus Feature):**
   * On an item (e.g. `State` or `Year Built`), click **`Reject`**.
   * Enter a reviewer note: *"Underwriter confirmed policy in California, keep CA abbreviation."*
   * Click **`Reject & Re-reason`**.
   * Show that the AI agent re-evaluates the item in real-time, adjusts the proposed action, and tags it as **`AI Re-reasoned`**.
3. **Execute Transformation:**
   * Click the green button **`Execute Controlled Transformation (X Approved)`**.

---

## ⏱️ Minute 8:30 - 10:00 | Cleaned SOV & Transformation Audit Log (Agent 4)
1. **Navigate to `5. Cleaned SOV & Audit` Tab:**
   * Point out the **"Downstream Schema Validation Passed (17 Required Columns)"** confirmation banner.
   * Verify the dataset preview table:
     * Contains **EXACTLY the 17 standardized columns** in strict case-sensitive order.
     * All currency symbols stripped; floats properly formatted.
     * Negative values converted to positive sums insured.
     * Missing fields preserved as empty blank cells (no zeros, no `"NaN"`).
   * Click the **`Transformation Audit Log`** subtab:
     * Show that 100% of transformations are logged with timestamp, source, target, before value, after value, confidence, and reviewer sign-off.
   * Demonstrate exports:
     * Click **`Cleaned_SOV.xlsx`** to download the clean workbook.
     * Click **`Audit_Log.xlsx`** and **`Audit_Log.json`** to download the complete audit trail.

---

## 🎯 Key Takeaways for Judges
* **Zero Silent Mutations:** Complete human control with autonomous speed.
* **Two-Pass Hybrid Engine:** Deterministic speed + Semantic embedding reasoning.
* **Strict Conformance:** Guaranteed downstream exposure model compatibility.
* **Full Auditability:** Every single cell modification is explained, justified, and logged.
