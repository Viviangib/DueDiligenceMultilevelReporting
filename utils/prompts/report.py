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
A total of {num_indicators} indicators were assessed. Based on the analysis data provided, calculate and present the distribution of alignment levels:

- Count how many indicators fall into each category: "Fully aligned", "Mostly aligned", "Partially aligned", "Not aligned/Not covered", "Not applicable"
- Present these numbers and percentages clearly
- Provide an interpretation of what these results indicate about the overall alignment

Analyze the alignment patterns and highlight:
- Areas of strong coverage (where many indicators are fully or mostly aligned)
- Areas needing improvement (where indicators are partially aligned or not aligned)
- The overall assessment of how well the sustainability framework aligns with the legal framework

Include a statement like: "These results indicate that while the framework demonstrates [substantial/moderate/limited] alignment with the given legal framework, there remain several areas where improvements are possible. Detailed indicator-level outcomes are provided in the corresponding Excel file."

## Key findings
Based on the analysis data, identify and describe:
- The main areas where the framework shows robust coverage
- The key gaps or areas needing improvement
- Specific themes or topics that emerge from the analysis

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
"""
