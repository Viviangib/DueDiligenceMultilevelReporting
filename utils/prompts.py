"""
Consolidated prompts module containing all prompt templates.
"""
from typing import Union, List, Dict, Optional


# =============================================================================
# ALIGNMENT DEFINITIONS
# =============================================================================

ALIGNMENT_DEF = """
    "Not applicable": {
        "Definition": " The regulation does not address the topic of this indicator of the assessed framework OR this indicator is out of scope of the regulation.",
        "Implication": ""
    },
    "Not aligned/Not covered": {
        "Definition": "This indicator of the assessed framework is required by the regulation, but it is missing in the assessed framework. OR the indicator of the assessed framework is required by the regulation, however, it contradicts the regulation.",
        "Implication": "The requirements in the assessed standard are not present. Need to be reviewed or included."
    },
    "Partially aligned": {
        "Definition": "This indicator of the assessed framework includes requirements similar to the regulation, but to a limited or substantially lower extent. For example,essential components necessary to fulfill the intent of the regulation is absent and critical aspects of the regulation are missing.",
        "Implication": "Some aspects are missing and need to be reviewed."
    },
    "Mostly aligned": {
        "Definition": "This indicator of the assessed framework is mostly covered by the requirements in the regulation, with minor aspects different extent (either slightly more stringent or slightly less stringent). The intent of this indicator is adequately mentioned and the overarching purpose of the indicator is duly recognized in the regulation",
        "Implication": "Considered to be covered by the benchmarked standard, and only minor aspects are different or missing."
    },
    "Fully aligned": {
        "Definition": "This indicator of the assessed framework fully matches or is equivalent to requirements in the regulation, covering the same scope and extent without deviation.",
        "Implication": "The requirement in the assessed standard is equivalent to this regulatory criterion. Considered to be fully covered by the benchmarked standard."
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
        Your task is to evaluate whether specific indicators from a voluntary sustainability standard (VSS) 
        align with the requirements of a sustainability-related regulation.

        You are provided with:
        - An **Indicator** from the VSS: This is a statement or question that needs to be assessed.
        - **Supporting Documents** from the VSS: These provide context and explanation for the indicator.
        - **Evidence from the Regulation**: These are relevant passages from the regulatory text that pertain to the indicator.

        Your goal is to assess how well the indicator, as explained by the supporting documents, meets the requirements 
        specified in the regulation.

        Follow these steps:
        1. **Rephrase the Indicator (if necessary)**: If the indicator is phrased as a question, rephrase it into a clear positive statement. 
           If it is already a statement, proceed as is.
        2. **Understand the Indicator's Context**: Use the supporting documents to gain a full understanding of the indicator's intent and requirements. 
           Focus on information that directly relates to the indicator and avoid inferring additional requirements not explicitly stated.
        3. **Comprehensive Evidence Collection**: Thoroughly review ALL provided evidence from both supporting documents and regulations. 
           Extract COMPLETE FULL PARAGRAPHS and sections EXACTLY AS WRITTEN - copy the text word-for-word without any paraphrasing or changes. 
           Each evidence item should be a substantial excerpt that provides full context and meaning. Only include evidence that is HIGHLY RELEVANT 
           and directly relates to the indicator. Quality over quantity - select fewer but more relevant evidence points rather than including 
           weakly related content. Please make numerical bullet points
        4. **Compare to the Regulation**: Using the evidence from the regulation, determine how well the indicator (with its context from the supporting documents) 
           aligns with the regulatory requirements.
        5. **Determine Alignment Level**: Based on your comparison, select the most appropriate alignment category from the provided definitions.
        6. **Justify Your Choice**: Provide a clear justification for your alignment category, citing specific evidence from both the supporting documents and the regulation.

        **Important Rules**:
        - **Evidence Citation**: If the alignment category is "Partially aligned," "Mostly aligned," or "Fully aligned," you must include at least one citation from the regulation in your evidence. 
          For "Not aligned/Not covered" or "Not applicable," you may cite only from the supporting documents if necessary. Make numerical bullet points with spacing for evidence and citations.
        - **Relevant Evidence Gathering**: Extract and cite ONLY HIGHLY RELEVANT evidence from both the supporting documents and regulations that directly 
          correlates the VSS indicator with regulatory requirements. Focus on quality over quantity - select fewer but more relevant evidence points.
          The VSS supporting documents must help explain how the indicator relates to or aligns with the regulatory requirements.
        - **Exact Text Extraction**: When citing, extract the COMPLETE FULL PARAGRAPH or entire section EXACTLY AS WRITTEN - copy word-for-word 
          without any paraphrasing, summarizing, or rewording. Each evidence item must be the original text that provides complete context. 
          Avoid short snippets or partial sentences.
        - **Accuracy in Justification**: Ensure that your justification accurately refers to the requirements of the regulation and the content of the VSS indicator and supporting documents. 
          Do not confuse or misrefer the two.
        - **Handling Insufficient Evidence**: If the evidence from the supporting documents or the regulation is unclear or insufficient to make a determination, 
          state this clearly in your justification and choose the alignment category that best reflects the available information.
       
        **Alignment Definitions**:
        {alignment_def}

        **Indicator Details**:
        - Criteria ID: {indicator_id}
        - Type: Statement
        - Indicator: {question}

        **Supporting Documents (from the VSS)**: {vss_texts}

        **Evidence from the Regulation**: {evidence}



        #OUTPUT :

        For this indicator, provide the following in your response:
        MANDATORY: Include two empty lines between each numbered section (1., 2., 3., 4., 5.) for proper formatting.
        
        STATEMENT: <original indicator>
         -two lines of space-
        EVIDENCE: List ALL relevant evidence with numbered format. Extract complete paragraphs/sections. Extract all the paragraph insetead of one reference.
        **CRITICAL**: Each evidence item MUST be a COMPLETE FULL PARAGRAPH and on a NEW LINE with a single newline (`\n`) after each numbered item to ensure Excel readability
        "(1) <COMPLETE FULL PARAGRAPH - substantial excerpt providing full context from any source>
        (2) <COMPLETE FULL PARAGRAPH - substantial excerpt providing full context from any source>
        (3) <COMPLETE FULL PARAGRAPH - substantial excerpt providing full context from any source>
        (4) <Additional COMPLETE paragraphs as found - aim for 5+ evidence points total>
        (5) <Continue numbering for all COMPLETE paragraphs found>
        (6) <Include both Supporting Documents and Regulation evidence in sequential numbering - ALL COMPLETE PARAGRAPHS>"
        If no relevant evidence is found, state "No relevant evidence found".
        Combine evidence from both Supporting Documents and Regulations in one numbered list.
        MANDATORY: Each evidence item must be a COMPLETE PARAGRAPH, not a single sentence or snippet.
        -two lines of space-
        CITATIONS: List citations with numbered format matching the evidence numbers.
        **CRITICAL**: Each citation item MUST be on a NEW LINE with a single newline (`\n`) after each numbered item to ensure Excel readability.
        "(1) {{Document Name, Page X, Section/Article Y}}
        (2) {{Document Name, Page X, Section/Article Y}}
        (3) {{Document Name, Page X, Section/Article Y}}
        (4) {{Document Name, Page X, Section/Article Y}}
        (5) {{Document Name, Page X, Section/Article Y}}
        (6) {{Document Name, Page X, Section/Article Y}}"
        Always include the document name, page number, and section/article if available. Use curly braces around each citation.
        Each citation number should correspond directly to the evidence number above.
        MANDATORY: Put each numbered citation item (1), (2), (3)... on a separate line for Excel readability.
         -two lines of space-
        ALIGNMENT CATEGORY: <chosen category>
         -two lines of space-
        JUSTIFICATION: <detailed justification>


        IMPORTANT: Do NOT use any markdown formatting (**, *, #, etc.) in your response. Use plain text only.
        
        CRITICAL INSTRUCTIONS FOR EVIDENCE:
        1. Use numbered format (1), (2), (3)... for EVIDENCE and CITATIONS sections
        2. Extract COMPLETE FULL PARAGRAPHS from regulations, not just single sentences or snippets
        3. Find and include ALL relevant evidence from the provided documents
        4. For regulations, prioritize full regulatory text over summaries
        5. Aim for as many evidence points as possible (ranging from 1 to 10) total from all sources combined but make sure they are highly relevant to the indicator.
        6. Match citation numbers exactly to evidence numbers
        7. MANDATORY: Each evidence item must be a COMPLETE PARAGRAPH, not a single sentence
        8. MANDATORY: Put each numbered evidence item (1), (2), (3)... on a NEW LINE for Excel readability
        9. MANDATORY: Put each numbered citation item (1), (2), (3)... on a NEW LINE for Excel readability
        
        Format your response exactly as follows with no asterisks or markdown:

        1. STATEMENT: ...


        2. EVIDENCE:
        (1) "..."
        (2) "..."
        (3) "..."


        3. CITATIONS:
        (1) {{Document Name, Page X, Article Y}}
        (2) {{Document Name, Page X, Article Y}}
        (3) {{Document Name, Page X, Article Y}}


        4. ALIGNMENT CATEGORY: ...


        5. JUSTIFICATION: ...

        CRITICAL: Add two empty lines between each numbered section (1., 2., 3., 4., 5.) for proper spacing and readability.
        
        EXAMPLE WITH PROPER SPACING:
        1. STATEMENT: [content]


        2. EVIDENCE: 
        (1) "[evidence content]"
        (2) "[evidence content]"
        (3) "[evidence content]"


        3. CITATIONS:
        (1) {{Document Name, Page X, Article Y}}
        (2) {{Document Name, Page X, Article Y}}
        (3) {{Document Name, Page X, Article Y}}


        4. ALIGNMENT CATEGORY: [content]


        5. JUSTIFICATION: [content]

        NOTE: you must number all these categories from statement to justification ( 1 to 5)      
        
        SAMPLE OUTPUT:
        
        1. STATEMENT: The stakeholder engagement plan has differentiated measures in place to allow for the effective participation of people or communities identified as disadvantaged or vulnerable.

2. EVIDENCE:
(1) "Member States shall ensure that companies take appropriate measures to carry out effective engagement with stakeholders, in accordance with this Article."

(2) "In consulting stakeholders, companies shall identify and address barriers to engagement and shall ensure that participants are not the subject of retaliation or retribution, including by maintaining confidentiality or anonymity."

(3) "Meaningful engagement with consulted stakeholders should take due account of barriers to engagement, ensure that stakeholders are free from retaliation and retribution, including by maintaining confidentiality and anonymity, and particular attention should be paid to the needs of vulnerable stakeholders, and to overlapping vulnerabilities and intersecting factors, including by taking into account potentially affected groupings or communities..."

(4) "Stakeholder Engagement: Basis for building strong, constructive, and responsive relationships that are essential for the successful management of a project's environmental
and social impacts. Stakeholder engagement is an on-going process that may involve, in varying degrees, the following elements: stakeholder analysis and planning, disclosure and dissemination of information, consultation and participation, grievance mechanism, and on-going reporting to affected communities. The nature, frequency, and level of effort of stakeholder engagement may vary considerably and will be commensurate with the project's risks and adverse impacts, and the project's phase of development."

(5) "Stakeholder Engagement Plan: A plan that lays out actions to conduct stakeholder engagement, with a dedicated focus on stakeholder groups that are external to the core operations of the infrastructure project, such as affected communities, local government authorities, non-governmental and other civil society organisations, local institutions, and other interested or affected parties. Where applicable, the Stakeholder Engagement Plan should include differentiated measures to allow the effective participation of those identified as disadvantaged or vulnerable. When the stakeholder engagement process depends substantially on community representatives, the project should make every reasonable effort to verify that such persons do in fact represent the views of affected communities and that they can be relied upon to faithfully communicate the results of consultations to their constituents."

(6) "Vulnerable Groups: Vulnerable people are those individuals within the project area who face a higher risk of falling into poverty compared to others in similar contexts. This group encompasses various segments of the population, including but not limited to: the elderly, the mentally and physically disabled, at-risk children and youth, ex-combatants, internally displaced people and returning refugees, HIV/AIDS-affected individuals and households, religious and ethnic minorities, and, in some societies, women."


3. CITATIONS:
(1) {{Corporate Sustainability Due Diligence Directive (EU) 2024/1760, Page 8, Article 13(1)}}

(2) {{Corporate Sustainability Due Diligence Directive (EU) 2024/1760, Page 8, Article 13(5)}}

(3) {{Corporate Sustainability Due Diligence Directive (EU) 2024/1760, Page 15, Recital 65}}

(4) {{FAST-Infra Label_Glossary, Page 22}}

(5) {{FAST-Infra Label_Glossary, Page 22}}

(6) {{FAST-Infra Label_Glossary, Page 24}}

4. ALIGNMENT CATEGORY: Fully aligned

5. JUSTIFICATION: The statement specifies the need for differentiated measures in stakeholder engagement to ensure the effective participation of disadvantaged or vulnerable communities, which is explicitly mentioned in the legal act. The VSS supporting documents clearly outline that the engagement plan must consider the vulnerabilities of certain groups, paralleling the directive's emphasis on paying particular attention to vulnerable stakeholders. Therefore, both sources align fully on the need for tailored engagement measures, leading to the conclusion that this indicator is fully aligned with the legal requirements.
        
        
        You must follow the template above for output and all the spacing and format of it.
        
        CRITICAL FOR EXCEL: Ensure each numbered item (1), (2), (3)... is on its own line within EVIDENCE and CITATIONS sections. Each evidence item must be a COMPLETE FULL PARAGRAPH providing substantial context, not just a single sentence.
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

**IMPORTANT:** Generate a report that follows this exact structure and tone:

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
