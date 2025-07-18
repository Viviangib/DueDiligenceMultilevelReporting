from typing import Union, List, Dict
import re
import json


def analysis_prompt(
    alignment_def: Union[str, Dict],
    indicator_id: str,
    vss_texts: Union[str, List[str]],
    question: str,
    evidence: Union[str, List[str]],
) -> str:

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
        3. **Compare to the Regulation**: Using the evidence from the regulation, determine how well the indicator (with its context from the supporting documents) 
           aligns with the regulatory requirements.
        4. **Determine Alignment Level**: Based on your comparison, select the most appropriate alignment category from the provided definitions.
        5. **Justify Your Choice**: Provide a clear justification for your alignment category, citing specific evidence from both the supporting documents and the regulation.

        **Important Rules**:
        - **Evidence Citation**: If the alignment category is "Partially aligned," "Mostly aligned," or "Fully aligned," you must include at least one citation from the regulation in your evidence. 
          For "Not aligned/Not covered" or "Not applicable," you may cite only from the supporting documents if necessary.
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

        **For this indicator, provide the following in your response:
        
        STATEMENT: <rephrased indicator if necessary, otherwise the original>
        EVIDENCE: <quote relevant evidence from supporting documents and regulation>
        CITATIONS: <list the source and location of each evidence>
        ALIGNMENT CATEGORY: <chosen category>
        JUSTIFICATION: <detailed justification>


        Format your response as:
        STATEMENT: ...
        EVIDENCE: ...
        CITATIONS: ...
        ALIGNMENT CATEGORY: ...
        JUSTIFICATION: ...


        """

    return analysis_prompt


def build_batch_prompt(batch, alignment_def, vss_texts):
    intro = f"""
You are a regulatory compliance expert specializing in law, ESG, and sustainability standards.

Your task is to evaluate whether specific indicators from a voluntary sustainability standard (VSS) 
align with the requirements of a sustainability-related regulation.

You are provided with:
- A list of **Indicators** from the VSS: Each is a statement or question that needs to be assessed.
- **Supporting Documents (from the VSS)**: These provide context and explanation for the indicators (applies to all indicators).
- **Evidence from the Regulation**: For each indicator, relevant passages from the regulatory text that pertain to it.

Your goal is to assess how well each indicator, as explained by the supporting documents, meets the requirements 
specified in the regulation.

Follow these steps for each indicator:
1. **Rephrase the Indicator (if necessary)**: If the indicator is phrased as a question, rephrase it into a clear positive statement. 
   If it is already a statement, proceed as is.
2. **Understand the Indicator's Context**: Use the supporting documents to gain a full understanding of the indicator's intent and requirements. 
   Focus on information that directly relates to the indicator and avoid inferring additional requirements not explicitly stated.
3. **Compare to the Regulation**: Using the evidence from the regulation, determine how well the indicator — as fully explained and contextualized by the supporting VSS documents — aligns with the regulatory requirements.

4. **Determine Alignment Level**: Based on your comparison, select the most appropriate alignment category from the provided definitions.
5. **Justify Your Choice**: Provide a clear justification for your alignment category, citing specific evidence from both the supporting documents and the regulation.

**Important Rules**:
- **CITATIONS FIELD IS STRICTLY REQUIRED**: For all alignment categories except "Not applicable" and "Not covered", you MUST include at least one citation from the regulation in the CITATIONS field. This is compulsory. If the alignment category is "Partially aligned", "Mostly aligned", or "Fully aligned", you must always provide at least one regulation citation. Only for "Not applicable" or "Not covered" may the CITATIONS field be empty or contain only VSS citations.
- **Evidence Citation**: If the alignment category is "Partially aligned," "Mostly aligned," or "Fully aligned," you must include at least one citation from the regulation in your evidence. For "Not aligned/Not covered" or "Not applicable," you may cite only from the supporting documents if necessary.
- **Accuracy in Justification**: Ensure that your justification accurately refers to the requirements of the regulation and the content of the VSS indicator and supporting documents. Do not confuse or misrefer the two.
- **Handling Insufficient Evidence**: If the evidence from the supporting documents or the regulation is unclear or insufficient to make a determination, state this clearly in your justification and choose the alignment category that best reflects the available information.

**Alignment Definitions**:
{alignment_def}

**Supporting Documents (applies to all indicators)**:
{vss_texts}

Return your results as a JSON array, one object per indicator, with the following keys:
- Indicator ID
- STATEMENT
- EVIDENCE
- CITATIONS
- ALIGNMENT CATEGORY
- JUSTIFICATION
- Alignment Label
- Alignment Definition

IMPORTANT:
- Return ONLY a valid JSON array, no explanations, no extra text, no tags, no trailing commas.
-You must return the same number of indicators results as specified from the batch. Do not miss any 
- All string values must be properly escaped for JSON (e.g., no unescaped newlines or quotes).
- If a value is a list, use a JSON array.
- If you cannot answer for an indicator, return an empty string for its fields, but keep the object in the array.
- Do not include any Markdown, HTML, or XML tags.
- The array must have exactly one object for each indicator in the batch, in the same order.
"""
    indicators_text = ""
    for i, item in enumerate(batch, 1):
        indicators_text += f"""
Indicator {i}:
- Criteria ID: {item['indicator_id']}
- Indicator: {item['question']}
- Evidence from the Regulation: {item['evidence']}
"""
    full_prompt = intro + "\n\n" + indicators_text + "\n\nOutput:"
    return full_prompt
