from typing import Optional
from utils.prompts.alignment import alignment_def


def report_generation_prompt(
    analysis_data: str,
    num_indicators: int,
    standard_name: str = "User Standard",
    standard_version: str = "1.0",
    standard_year: str = "2024",
    organization: str = "User Organization",
    report_date: Optional[str] = None,
) -> str:
    if not report_date:
        from datetime import datetime

        report_date = datetime.now().strftime("%Y-%m-%d")
    return f"""
Generate a professional benchmarking summary report for the following standard:

Standard name: {standard_name}
Standard version and year: {standard_version}, {standard_year}
Founding parties: {organization}
Date of report: {report_date}

**ANALYSIS DATA TO PROCESS:**
{analysis_data}

The analysis was performed on {num_indicators} indicators. The attached data includes alignment levels, justifications, and evidence for each indicator.


At the top of document please add a Title heading suitable with the name of the standard in mind and the benchmarking summary .

Please provide:

- An executive summary of the benchmarking results, including overall alignment statistics, key findings, and patterns.
- A summary of strengths, weaknesses, and critical gaps identified.
- Actionable recommendations for improvement.
- References (APA style).
- A glossary of key terms used in the analysis.
- A brief description of the benchmarking process and methodology.


The document must contain the following headings. Follow the desceiption provided to each one of them :

-Table of Contents

-General information :
Standard name: <user_standard_name>
Standard version and year of publishment: <user_standard_version, user_standard_year>
Founding parties: <user_org>
Date of this report generated: <report_date>

About the Global Infrastructure Basel Foundation
<SAMPLE TEXT>Disclaimer: This report contains AI-generated content intended solely for preliminary benchmarking purposes. Global Infrastructure Basel Foundation makes no representations or warranties of any kind, express or implied, regarding the completeness, accuracy, reliability, or suitability of the information herein. This document does not constitute an official recognition or decision and should not be treated as such

-Abbreviations
EURD: European Union Deforestation Regulation
VSS: Voluntary sustainability standard
AI: Artificial Intelligence
Add any other relevant abbreviations you find anywhere in the analysis data

-Benchmarking results
The preliminary benchmarking analysis to evaluate whether the overall intent of relevant criteria in the European Union Deforestation Regulation (EUDR) has been incorporated into the benchmarked standard, meanwhile, it highlights specific differences at the indicator level. A round of expert review or a public consultation is required to verify the results generated.
This benchmark results are presented at the indicator level, using different labels and numberings to describe the level of alignment between the indicator in the benchmarked standard and the scope of EUDR
This is the benchmarking criteria used {alignment_def}. State in report generally with the help of table or whatever.


-Preliminary benchmarking summary:

In this section, provide an overview of the outcomes from the benchmarking analysis is presented. This summary is organised based on the indicators in the 
This analysis is limited in scope as it focuses solely on the content of certification schemes and does not extend to evaluating their 
implementation or real-world impacts. It includes an examination of various classes of indicators commonly used within these schemes—such as 
“critical,” “must,” “facultative must,” “recommended,” and those subject to a “grace period.” While this categorization helps in 
understanding the structural emphasis and theoretical rigor of the certification criteria, it does not capture how these standards are 
applied or enforced in practice. Consequently, conclusions drawn from this assessment should be interpreted with caution, as they do not 
reflect actual compliance or effectiveness on the ground. So considering these instructions provide a preliminary benchmarking summary.
Also give the general analysis data headings from below so that the user can know about the headings and how everything went about.
You can add some sample data from the analysis data in the form of table just to highlight. Do highlight the total number of indicators
: {num_indicators}


<user_standard_name>.
Indicator ID
Indicator text
Alignment level
Justification
Evidence
<file_benchmarking_results>


-- Recommendations
Potential gaps, or any recommendation like this 

--References
Provide all references from the analysis data.


-Glossary 
provide the glossary from the analysis data

-Benchmarking process
highlight the benchmarking process

Do **not** include any instructional or template headings. Write the report as a finished, professional document, not as a template to be filled in.
"""
