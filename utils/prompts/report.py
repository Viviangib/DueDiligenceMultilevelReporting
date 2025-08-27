from typing import Optional
from utils.prompts.alignment import alignment_def


def report_generation_prompt(
    analysis_data: str,
    num_indicators: int,
    sustainability_framework: str = "User Standard (version 1.0, 2024)",
    legal_framework: str = "Legal Framework",
) -> str:
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
