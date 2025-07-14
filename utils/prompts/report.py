from typing import Optional

def report_generation_prompt(
    analysis_data: str,
    standard_name: str = "User Standard",
    standard_version: str = "1.0",
    standard_year: str = "2024",
    organization: str = "User Organization",
    report_date: Optional[str] = None
) -> str:
    """
    Generate a comprehensive benchmarking summary report from analysis results.
    
    Args:
        analysis_data: String representation of the Excel analysis data
        standard_name: Name of the benchmarked standard
        standard_version: Version of the standard
        standard_year: Year of publication
        organization: Name of the founding organization
        report_date: Date of report generation (defaults to current date)
    """
    
    if not report_date:
        from datetime import datetime
        report_date = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""
You are an expert regulatory compliance analyst specializing in sustainability standards and benchmarking reports. 
Your task is to generate a comprehensive benchmarking summary report based on the provided analysis data.

**REPORT REQUIREMENTS:**

1. **Format**: Generate a professional benchmarking report following the exact template structure provided
2. **Content**: Use the analysis data to populate all sections with accurate, well-structured information
3. **Tone**: Professional, objective, and analytical
4. **Citations**: Use APA citation style for all references
5. **Structure**: Follow the template exactly, including all sections and subsections

**ANALYSIS DATA TO PROCESS:**
{analysis_data}

**REPORT TEMPLATE TO FOLLOW:**

# Appendix 2: Benchmarking Summary Report Template (V1)

## Table of Contents
- General information
- Abbreviations  
- Benchmarking results
- Preliminary benchmarking summary
- Recommendations
- References
- Appendix 1: Glossary
- Appendix 2: Benchmarking process

## General information
- Standard name: {standard_name}
- Standard version and year of publication: {standard_version}, {standard_year}
- Founding parties: {organization}
- Date of this report generated: {report_date}

**About the Global Infrastructure Basel Foundation**
The Global Infrastructure Basel Foundation (GIB) is a leading organization dedicated to promoting sustainable infrastructure development through benchmarking, capacity building, and knowledge sharing.

**Disclaimer**: This report contains AI-generated content intended solely for preliminary benchmarking purposes. Global Infrastructure Basel Foundation makes no representations or warranties of any kind, express or implied, regarding the completeness, accuracy, reliability, or suitability of the information herein. This document does not constitute an official recognition or decision and should not be treated as such.

## Abbreviations
Generate a comprehensive list of abbreviations relevant to the analysis, including:
- EURD: European Union Deforestation Regulation
- VSS: Voluntary sustainability standard
- AI: Artificial Intelligence
- [Add other relevant abbreviations from the analysis]

## Benchmarking results
The preliminary benchmarking analysis evaluates whether the overall intent of relevant criteria in the European Union Deforestation Regulation (EUDR) has been incorporated into the benchmarked standard, meanwhile, it highlights specific differences at the indicator level. A round of expert review or a public consultation is required to verify the results generated.

This benchmark results are presented at the indicator level, using different labels and numberings to describe the level of alignment between the indicator in the benchmarked standard and the scope of EUDR.

### Table 1: Definition of alignment levels

| # | Label | Definition | Implication |
|---|-------|------------|-------------|
| N/A | Not applicable | This requirement in the regulation is not application for the sector or commodity defined by the scope or intended use of the benchmarked standard. In certain cases, the topic may be pertinent only in exceptional circumstances and in such instances, we may still classify it as not applicable. | |
| 0 | Not aligned/Not covered | This requirement in the regulation is not included in the assessed standard. Or this core topic of the criteria is not covered. The requirements in the assessed standard are not sufficient. | Need to be reviewed or included. |
| 1 | Partially aligned | The assessed standard includes requirements similar to this regulatory criterion, but to a limited or substantially lower extent or rigour; essential components necessary to fulfil the intent is absent, and should be given further consideration. Critical aspect of the regulatory criterion is missing. | Some aspects are missing, and need to be reviewed |
| 2 | Mostly aligned | This requirement in the regulation is fully covered or fully included, fully aligned with the assessed standard, with minor aspects different (either more stringent or less stringent) extent. The intent of this regulatory requirement is adequately addressed, while variances or omissions may arise in individual indicators, the overarching purpose of the relevant criteria is duly recognised in the benchmarked standard. | Considered to be covered by the benchmarked standard, and only minor aspects are different or missing. |
| 3 | Fully aligned | This requirement in the regulation is equivalent to the indicator in the assessed standard, covering the same scope and extent without deviation. The requirement in the assessed standard are equivalent to this regulatory criterion. | Considered to be covered by the benchmarked standard. |

## Preliminary benchmarking summary
In this section, provide an overview of the outcomes from the benchmarking analysis. This summary should be organized based on the indicators in the {standard_name}.

Generate a comprehensive table with the following structure:

**Note : There can be a 1000 indicators, you must not miss any one of them and include all of them

| Indicator ID | Indicator text | Alignment label | Justification | Evidence |
|--------------|----------------|-----------------|---------------|----------|
| [Populate with actual data from analysis] | | | | |

**Analysis Summary**: Provide a comprehensive summary of the benchmarking results, including:
- Overall alignment statistics
- Key findings and patterns
- Areas of strength and weakness
- Critical gaps identified

This analysis is limited in scope as it focuses solely on the content of certification schemes and does not extend to evaluating their implementation or real-world impacts. It includes an examination of various classes of indicators commonly used within these schemes—such as "critical," "must," "facultative must," "recommended," and those subject to a "grace period." While this categorization helps in understanding the structural emphasis and theoretical rigor of the certification criteria, it does not capture how these standards are applied or enforced in practice. Consequently, conclusions drawn from this assessment should be interpreted with caution, as they do not reflect actual compliance or effectiveness on the ground.

## Recommendations
### Potential gaps
Based on the analysis results, identify and describe:
- Critical gaps in alignment
- Areas requiring immediate attention
- Recommendations for improvement
- Priority areas for enhancement

Provide specific, actionable recommendations with clear justification based on the analysis data.

## References
Use American Psychological Association (APA) citation style for all references.

**Standard References:**

Add all the references here 

## Appendix 1: Glossary
Provide a comprehensive glossary of terms used in the analysis, including:
- Technical terms from the regulation
- Standard-specific terminology
- Industry-specific terms
- Abbreviations and acronyms

## Appendix 2: Benchmarking process

Describe the benchmarking methodology used, including:
- Data collection process
- Analysis methodology
- Quality assurance measures
- Limitations and assumptions

**INSTRUCTIONS:**
1. Process the provided analysis data thoroughly
2. Generate a complete, professional report following the exact template structure
3. Ensure all sections are properly populated with relevant information
4. Maintain professional tone and objective analysis
5. Include specific data from the analysis in the benchmarking summary table
6. Provide actionable recommendations based on the findings
7. Use proper formatting and structure throughout

Generate the complete report now.
"""

    return prompt 