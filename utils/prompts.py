"""
Consolidated prompts module containing all prompt templates.
"""
from typing import Union, List, Dict, Optional


# =============================================================================
# ALIGNMENT DEFINITIONS
# =============================================================================

ALIGNMENT_DEF = """
    "Fully aligned": {
        "Definition": "This indicator of the assessed framework fully matches or is equivalent to requirements in the referenced document, covering the same scope, intent and content without deviation.",
        "Implication": "No action needed; considered fully covered."
    },
    "Mostly aligned": {
        "Definition": "The indicator in the assessed framework largely aligns with the referenced document, with only minor differences in scope or stringency. The intent and overarching purpose are clearly addressed.",
        "Implication": "Considered adequately covered; minor improvements may be considered."
    },
    "Partially aligned": {
        "Definition": "The indicator in the assessed framework reflects some similar intent to the referenced document but lacks essential components. Key elements required to fulfill the reference's intent are missing or insufficiently addressed.",
        "Implication": "Review the assessed framework and incorporate missing or underdeveloped aspects."
    },
    "Not aligned": {
        "Definition": "The indicator of the assessed framework contradicts or conflicts with the reference's requirements.",
        "Implication": "Review and revise the assessed framework to resolve contradictions."
    },
    "Not applicable": {
        "Definition": "The referenced document does not address the topic of this indicator of the assessed framework OR this indicator is out of scope of the referenced document.",
        "Implication": "No action required."
    }
}
"""


# =============================================================================
# ANALYSIS PROMPTS
# =============================================================================

def analysis_prompt(
    alignment_def: Union[str, Dict],
    indicator_id: str,
    vss_texts: Union[str, List[str]],
    question: str,
    evidence: Union[str, List[str]],
) -> str:
    """Generate analysis prompt for single indicator evaluation."""

    analysis_prompt = f"""
You are a regulatory compliance expert specializing in law, ESG, and sustainability standards.

Your task is to evaluate **how well an indicator (from a sustainability framework)** — together with its supporting texts from a Voluntary Sustainability Standard (VSS) — **meets the requirements of the Regulation**.

The **Regulation is the benchmark (the standard of truth)**.  
The **Indicator + VSS texts** are what you are evaluating **against** the Regulation.

---

### Step-by-Step Procedure:

1. **Rephrase the Indicator (if necessary)**  
   If the indicator is phrased as a question, rewrite it as a clear, positive statement. Otherwise, use it as-is.

2. **Understand the Indicator's Context**  
   Use the VSS supporting documents only to understand what the indicator *means* or *covers*.  
   Do **not** assess alignment based on the VSS itself — it only clarifies the indicator’s intent.  
   Alignment is determined **solely against the Regulation.**

3. **Evidence Collection**  
   Review all text provided from the supporting documents (VSS) only to interpret what the indicator means, not to judge alignment.
   Then, extract complete paragraphs or sections from the Regulation that directly address the indicator.
   Present:
   - VSS excerpts first (for context only)
   - Regulation excerpts second (for alignment assessment)
   Quality over quantity: fewer, stronger pieces of evidence are preferred.  
   Present them as **numbered items**.  
   Include **both sources** (VSS and Regulation) in the same evidence list
   Use complete, unedited paragraphs. Do not paraphrase or mix sources. 
   -Rank both evidences and their corresponding citations from most relevant to least relevant.

4. **Compare to the Regulation**  
   Analyze how the indicator — clarified by the VSS — aligns with the Regulation's requirements.  
   **Ignore any VSS language when deciding alignment. VSS text is purely explanatory and cannot be used as evidence of compliance.**
   The Regulation evidence alone determines the alignment outcome. 
   The absence of Regulation evidence means the indicator **cannot be considered aligned.**

5. **Determine the Alignment Category**  
   Choose exactly one category from the following definitions:  
   {alignment_def}  

   **Important Rule:**  
   - “Fully aligned” or “Mostly aligned” **require at least one direct Regulation citation** confirming compliance or equivalence.  
   - If no Regulation evidence is found or it only partially supports the indicator, select “Partially aligned” or “Not aligned.”  
   - Never assign higher alignment solely because the VSS explains the indicator well.

6. **Justify the Decision**  
   - Treat the **Regulation as the benchmark standard.**  
   - Explain how well the **Indicator + VSS texts** meet that regulatory requirement.  
   - Reference evidence from both:
       - Supporting documents → show what the indicator requires.
      - Regulation → show what is actually required by law.  
   - **When writing the justification, refer to the VSS only for indicator interpretation. The strength or weakness of the VSS explanation does not affect alignment — only the Regulation text does.**
   - If Regulation evidence is missing, explicitly state this and assign a conservative category ("Partially aligned" or "Not aligned").  
   - Be decisive and consistent with the evidence.

---

### Additional Rules:

- **Evidence Citation Rule:**  
  For “Partially aligned,” “Mostly aligned,” or “Fully aligned,” include at least one **Regulation citation**.  
  If no Regulation citation exists, downgrade to “Partially aligned” or “Not aligned.”  
  For “Not aligned/Not covered” or “Not applicable,” Regulation citations are optional.

- **VSS Text Quality Warning:**  
  The VSS supporting documents were retrieved via RAG. Their quality and relevance are not guaranteed.  
  VSS evidence is **contextual only** and cannot replace Regulation alignment.

- **Critical Evidence Extraction Rules:**  
  - Use complete paragraphs or sections only (no snippets).From both VSS texts (if provided) and Regulations 
  - Each numbered evidence item must be on a new line for Excel readability.  
  - Match evidence and citation numbering exactly.  
  - Include both Supporting Document and Regulation excerpts in a single combined evidence list.

- **Handling Unclear Cases:**  
  If the Regulation evidence is vague, missing, or incomplete, state that clearly and select the most conservative (lowest confidence) alignment category.

---

### Required Output Format (Plain Text Only)

1. STATEMENT: [indicator statement]


2. EVIDENCE:
(1) "[Full paragraph or section]"
(2) "[Full paragraph or section]"
(3) "[Full paragraph or section]"


3. CITATIONS:
(1) {{Document Name, Page X, Article Y}}
(2) {{Document Name, Page X, Article Y}}
(3) {{Document Name, Page X, Article Y}}


4. ALIGNMENT CATEGORY: [category]


5. JUSTIFICATION: [reasoning]

**Formatting Rules:**
- Always number sections 1–5 as above.
- Leave two blank lines between each major section (1–5).
- Each numbered evidence and citation item must be on its own line.
- Do not use any markdown (**bold**, *, #, etc.).
- Be confident and decisive — choose exactly one alignment category.

---

**Indicator Details:**
- Criteria ID: {indicator_id}
- Indicator: {question}

**Supporting Document Text (VSS):** {vss_texts}

**Regulation Text:** {evidence}
"""

    return analysis_prompt




# =============================================================================
# REPORT GENERATION PROMPTS
# =============================================================================

def report_generation_prompt(
    analysis_data: str,
    num_indicators: int,
    sustainability_framework: str = "User Standard (version 1.0, 2024)",
    legal_framework: str = "Legal Framework",
) -> str:
    """Generate report generation prompt for analysis summary."""
    return f"""
Generate a professional benchmarking analysis summary report based on the following structure:

# Benchmarking Analysis Summary



**ANALYSIS DATA TO PROCESS:**
{analysis_data}

**IMPORTANT:** Generate a report that follows this exact structure and tone with FIXED HEADINGS ONLY - no additional headings beyond those specified:

**Sustainability framework:** {sustainability_framework}
**Relevant legal framework:** {legal_framework}

## Introduction
This report presents the results of an AI-driven benchmarking analysis, comparing the sustainability framework with the relevant legal framework. The objective is to identify areas of overlap and divergence by assessing indicators in the sustainability framework against requirements of the legal framework.

## Methodology
The analysis was conducted at the indicator level. Each indicator in the sustainability framework was evaluated individually, considering its scope, intent, and content, against the relevant legal requirements. Indicators were classified into five alignment levels including "fully aligned", "mostly aligned", "partially aligned", "not aligned", and "not applicable".

## Result overview
A total of {num_indicators} indicators were assessed. The distribution of alignment levels of indicators is summarised below:

Based on the analysis data provided, calculate and present the distribution of alignment levels:
- Count how many indicators fall into each category: "Fully aligned", "Mostly aligned", "Partially aligned", "Not aligned/Not covered", "Not applicable"
- Present these numbers and percentages clearly in a detailed table format
- Provide comprehensive interpretation of what these results indicate about the overall alignment

**Provide the Results Overview in the following paragraph format (keep the percentage table but make the analysis in paragraph form):**

First, present the percentage table with the alignment distribution.

Then provide the analysis in paragraph format with ALL of the following detailed content:

**Paragraph 1 - Detailed Breakdown:**
Example :
"Of these indicators, [X] were categorized as fully aligned, while [Y] were mostly aligned with the framework. A significant portion, [Z] indicators, were partially aligned, indicating that while some components of these indicators are covered, there is room for improvement. Additionally, [W] indicators were categorized as not aligned, suggesting that they do not meet the standards of the sustainability framework. A smaller number, [V] indicators, were marked as not applicable. These results highlight that while the framework is largely adhered to, several areas could be enhanced, particularly for those partially aligned or not aligned with the criteria."

**Paragraph 2 - Strategic Assessment:**
Example :
"These results indicate that while the framework demonstrates [substantial/moderate/limited] alignment with the given legal framework, there remain several areas where improvements are possible. In particular, the [X] partially aligned and [Y] not aligned indicators highlight opportunities to strengthen coverage. Detailed indicator-level outcomes are provided in the corresponding Excel file."

**Paragraph 3 - Coverage Analysis with Specific Examples:**
Example:
"The benchmarking analysis identified robust coverage in the areas, including [specific areas like waste management, GHG emissions, forest protection, biodiversity preservation, responsible procurement, labor rights, etc.]. However, gaps remain in relation to [specific areas like climate resilience, gender equality, etc.]. These findings suggest that the [framework name] provides strong alignment in many core sustainability areas but could be enhanced to more fully reflect the breadth of requirements under the [legal framework name]."

**IMPORTANT REQUIREMENTS:**
- Write the entire Results Overview section in flowing paragraph format, not bullet points or subheadings
- Include the percentage table but make all the analysis and interpretation flow as continuous paragraphs
- MUST include ALL three paragraphs with the detailed content specified above
- MUST provide specific examples of areas with robust coverage and areas with gaps
- MUST analyze the implications of partially aligned and not aligned indicators
- MUST provide strategic assessment of overall alignment
- MUST include specific recommendations for improvement based on the analysis
- CRITICAL: Use ONLY the exact headings specified - no additional headings, subheadings, or section breaks beyond: "Benchmarking Analysis Summary", "Sustainability framework:", "Relevant legal framework:", "## Introduction", "## Methodology", "## Result overview", "## Alignment categories"

## Alignment categories
Present the following alignment categories table exactly as shown:

| Alignment level | Definition | Implication |
|----------------|------------|-------------|
| **Fully aligned** | This indicator of the assessed framework fully matches or is equivalent to requirements in the referenced document, covering the same scope, intent and content without deviation. | No action needed; considered fully covered. |
| **Mostly aligned** | The indicator in the assessed framework largely aligns with the referenced document, with only minor differences in scope or stringency. The intent and overarching purpose are clearly addressed. | Considered adequately covered; minor improvements may be considered. |
| **Partially aligned** | The indicator in the assessed framework reflects some similar intent to the referenced document but lacks essential components. Key elements required to fulfill the reference's intent are missing or insufficiently addressed. | Review the assessed framework and incorporate missing or underdeveloped aspects. |
| **Not aligned** | The indicator of the assessed framework contradicts or conflicts with the reference's requirements. | Review and revise the assessed framework to resolve contradictions. |
| **Not applicable** | The referenced document does not address the topic of this indicator of the assessed framework OR this indicator is out of scope of the referenced document. | No action required. |

**Instructions:**
- Write in a professional, analytical tone
- Use the actual analysis data to calculate real numbers and percentages
- Be specific about findings rather than generic
- Do not include template placeholders or instructional text
- Focus on substantive analysis based on the provided data
- STRICT: Use ONLY these exact headings in this exact order - NO additional headings:
  1. "Benchmarking Analysis Summary" (main title)
  2. "Sustainability framework: [framework name]" (bold)
  3. "Relevant legal framework: [legal framework name]" (bold)
  4. "## Introduction"
  5. "## Methodology" 
  6. "## Result overview"
  7. "## Alignment categories"

**IMPORTANT:** End the report with this exact disclaimer:

This summary is provided for informational purposes only and doesn't imply any official recognition. This work is part of the Due Diligence Multilevel Reporting Project managed by the Global Infrastructure Basel Foundation, and funded by the Swiss State Secretariat for Economic Affairs SECO, through the ISEAL Innovations Fund.
"""


# =============================================================================
# INDICATOR EXTRACTION PROMPTS
# =============================================================================

INDICATOR_PROMPT = """

You are an expert assistant specialized in extracting indicators from sustainability, compliance, climate, or ESG-related documents. Your task is to identify and extract all indicators from the provided document content and present them in a standardized JSON format.


### What are Indicators?
Indicators are structured entries used to assess or declare the presence, quality, or commitment to specific environmental, social, or governance practices. They:
- Are questions (e.g., "Does the project have an ESIA?") or statements (e.g., "The project has an ESIA.") that evaluate a specific, actionable, or measurable condition.
- Must have an explicit, valid ID directly associated with the question or statement.
- May include predefined answer options (e.g., Yes/No) and answers, if provided.

### Valid IDs
Valid IDs must:
✅ Be explicitly present in the document text, directly adjacent to or within the same structural element (e.g., table row, list item, or paragraph) as the indicator's question or statement.
✅ Match one of these patterns:
   - Hierarchical numbers: e.g., 1.1, 1.1.1, 2.3.4 (must include at least one dot).
   - Letter-number combinations: e.g., E1.FG3, A-12, G4.2.
✅ Be clearly tied to an assessable condition (e.g., a question or statement about a policy, action, or outcome).

Invalid IDs:
❌ Single numbers (e.g., 3, 8, 5) or standalone letters (e.g., A, B).
❌ Document metadata, version numbers (e.g., V1.4EN), or unrelated codes (e.g., A-1-S-B-F).
❌ IDs not directly associated with a question or statement (e.g., table row numbers, section labels).


### What are NOT Indicators?
Exclude content that:
- Defines categories or terms (e.g., "HCV1: Species Diversity: Concentrations of biodiversity...") without assessing an action or outcome.
- Lacks a question or statement tied to an assessable condition (e.g., a table listing "Country" without a related question).
- Is narrative, background, or descriptive text without a measurable outcome.
- Lacks an explicit, valid ID directly tied to the question or statement.


IDs must not be generic words, placeholders, or fabricated by the assistant must be excluded. Dont make an ID out of anything. 
Make sure you dont create one for a statement you think might follow the indicator criteria.


Appear in various formats, such as:

Tables (e.g., columns labeled ID, Question, Answer, Answer Options).

Bullet lists or numbered points (e.g., "1.1.1" followed by a description).

Paragraphs describing requirements or criteria.

Headings with structured values.

Key Characteristics of Indicators:
They imply an assessable condition (e.g., a policy exists, an action is taken, a standard is met).


They are often tied to compliance, performance, or commitment in sustainability or ESG contexts.
They are actionable or measurable, meaning they can be evaluated with a response (e.g., Yes/No, text description, or evidence).


### Extraction Guidelines
1. **Identify Indicators**:
   - Look for sections, tables, lists, or paragraphs containing questions or statements assessing specific actions, commitments, or conditions related to sustainability, compliance, or ESG topics.
   - Ensure the content implies an assessable condition (e.g., "The project has a plan" or "Does the project have a plan?").
   - Only extract indicators with an explicit, valid ID in the same structural element (e.g., same table row, list item, or paragraph).

2. **Extract Fields**:
   - **ID**: Extract the exact ID as it appears, ensuring it matches the valid patterns and is directly tied to the indicator. Do not infer, fabricate, or reassign IDs from other parts of the document.
   - **Question/Statement**: Extract the full question or statement exactly as written. Do not rephrase, summarize, or convert between question and statement. Preserve its original form
   - **Answer Options**: Extract predefined response choices (e.g., ["Yes", "No"]). Use [] if none are specified.
   - **Answer**: Extract the provided answer, if any. Use null if missing.

3. **Handle Variations**:
   - Map varying column names (e.g., "Field," "Declaration") to standard fields (ID, Question, Answer Options, Answer) based on context.
   - Capture nested indicators (e.g., "1.1.1" under "Criterion 1.1").
   - Include incomplete indicators if they meet the criteria (e.g., have a valid ID and question/statement).

4. **Deduplication**:
   - Remove duplicates by comparing both ID and Question (case-insensitive, normalized text). Keep only the first instance of an indicator with identical ID and Question


Infer Fields:

ID: Only extract indicators that have an explicit, adjacent ID clearly visible in the document (in the same line, heading, table row, or directly preceding/following the indicator text).
If no such ID is present, do not extract the indicator. Indicators without an ID are not considered valid and must be ignored.
Never fabricate, guess, or infer an ID, and never associate an ID from elsewhere in the document.

Question/Statement: Extract the full question or statement exactly as written. Do not rephrase, summarize, or convert between question and statement. Preserve its original form

Answer Options: Identify predefined response types (e.g., Yes/No, Multi-select). Use [] if none are specified.

Answer: Extract the provided answer, if any. Use null or - if missing.



Column names may vary (e.g., "Field," "Declaration"). Map them to standard fields (ID, Question, Answer Options, Answer) using context.
Capture nested indicators (e.g., "1.1.1" under "Criterion 1.1").
Include incomplete indicators with available data, but ensure they meet the indicator criteria.


Example: "Does the project comply with biodiversity strategies?"


Ensure Completeness:

Extract all indicators from the document. Do not limit to a subset.
If no valid indicators are found, return an empty JSON array: [].


Validate Output:

Ensure the output is a valid JSON array of objects.
Each object must have the keys: "ID", "Question", "Answer Options", "Answer".
Use consistent formatting and escape special characters properly.

Remove duplicates: If two indicators have the same "ID" and identical "Question", include only one instance in the output. Do not repeat the same indicator.


Examples
Below are examples showing how to extract indicators from different document structures.
Example 1: Table Format
Raw Content:
ID         Field         Answer      Answer Options  
E1.FG3     Declaration   -           Yes | Project in development | No  
Does the project comply with and contribute to the country's national and subnational biodiversity strategies, goals, and action plans (or similar planning documents), and any sectorial and/or international environmental conventions to which the country is party?

Expected Output:
{{
    "ID": "E1.FG3",
    "Question": "The project complies with and contributes to the country's national and subnational biodiversity strategies and environmental conventions.",
    "Answer Options": ["Yes", "Project in development", "No"],
    "Answer": "-"
}}

Example 2: Paragraph/List Format
Raw Content:
Criterion 1.1 – Producer-level activities are managed in a well-informed, effective and inclusive way.
1.1.1 climate change mitigation climate change adaptation gender equality
A clear and locally relevant activity plan is developed and implemented for the Producer Unit, which:
(i) Is kept up to date and includes all activities, timelines and responsibilities;
(ii) Is reviewed at least annually, taking into consideration the findings of the monitoring activities.

Expected Output:
{{
    "ID": "1.1.1",
    "Question": "A clear and locally relevant activity plan is developed and implemented for the Producer Unit, which is kept up to date, includes all activities, timelines, and responsibilities, and is reviewed at least annually considering monitoring findings.",
    "Answer Options": [],
    "Answer": null
}}

Note: No explicit answer options or answers are provided, so those fields are empty or null.

Important Instructions

Do not rely on exact headings. Field names vary across documents (e.g., "Field" vs. "Declaration"). Use your best judgment to infer mappings.
+ Do not rephrase questions or statements at all. Extract them as-is — retain their original form as either a question or a statement.
Extract all valid indicators. Do not invent indicators or include content that doesn't fit the definition (e.g., a table without a question/statement).
Ensure the output is a valid JSON array. If no indicators are found, return [].
Handle incomplete data gracefully. Use null or - for missing fields.
Stick to the document content. Do not fabricate indicators or extrapolate beyond what's provided.


Output Format
Return a valid JSON array of indicator objects, each with the following structure:

{{
    "ID": "string",
    "Question": "string",
    "Answer Options": ["array of strings"] or [],
    "Answer": "string or null"
}}


Begin Extraction
Analyze the following document content and extract all indicators according to the guidelines above.
Document Text:
{chunk}
Only return the valid JSON array of extracted indicators.
"""


# =============================================================================
# LEGACY COMPATIBILITY
# =============================================================================

# For backward compatibility, maintain the old import structure
alignment_def = ALIGNMENT_DEF
