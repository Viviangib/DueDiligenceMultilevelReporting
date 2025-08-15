
from typing import Union, List, Dict
import re
import json




# def build_batch_prompt(batch, alignment_def, vss_texts):
#     intro = f"""
# You are a regulatory compliance expert specializing in law, ESG, and sustainability standards.

# Your task is to evaluate whether specific indicators from a voluntary sustainability standard (VSS) align with the requirements of a sustainability-related regulation. The alignment is primarily determined by how well the indicators, as explained by the supporting VSS documents, meet the requirements specified in the regulation.

# You are provided with:
# - A list of **Indicators** from the VSS: Each is a statement or question that needs to be assessed. **Preserve the original text of the indicators completeley.**
# - **Supporting Documents (from the VSS)**: These provide context and explanation for the indicators (applies to all indicators). Use these to understand the intent and requirements of each indicator.
# - **Evidence from the Regulation**: For each indicator, relevant passages from the regulatory text that pertain to it. **The regulation is of primary importance in determining alignment.**

# Your goal is to assess how well each indicator, as fully explained and contextualized by the supporting VSS documents, aligns with the regulatory requirements. 

# **Important Rules**:
# - **Alignment Focus**: Alignment is determined by how well the indicator (with its context from the supporting documents) meets the requirements of the regulation. The supporting documents are only for understanding the indicator's context; they do not determine alignment on their own.
# -if there is no evidence or citation from the supporting documents then the alignment category should be "Not aligned/Not covered". However , if the regulation doesnt contain the indicator then it should be "Not applicable".
# - **Preserve Original Text**: If an indicator is phrased as a question, retain it as such. Do not convert it into a statement and dont change anything. Print it as it is.
# - **Evidence and Citations**:
#   - **Evidence**: Must consist of direct excerpts from the supporting documents (VSS∏) and the regulation that are relevant to the indicator. Select the most relevant and concise excerpts.
#   - **Citations**: Must include specific references from both the supporting documents and the regulation. For alignment categories "Partially aligned,"
#   "Mostly aligned," or "Fully aligned," at least one citation from the regulation is required. 
#   - If possible, provide specific details about the source (e.g., section, page, or paragraph). If not feasible, indicate the document name.
# - **Handling Duplicate IDs**: If indicators have duplicate IDs, treat each as a unique instance based on their position in the batch.
# - **Justification**: Clearly explain how the evidence from both the supporting documents and the regulation supports the chosen alignment category. Explicitly refer to the evidence in your explanation. Note that this is the AI's interpretation, and subject matter experts will review it.
# **Output Format**: Return a valid JSON object with the required fields. Do NOT include Markdown (e.g., **, *, #), HTML, or XML tags. Ensure all string values are properly escaped for JSON. Add extra newlines between evidence excerpts for readability

# **Alignment Definitions**:
# {alignment_def}

# **Supporting Documents (VSS documents) (applies to all indicators)**:
# {vss_texts}

# Follow these steps for each indicator:
# 1. **Understand the Indicator's Context**: Use the supporting documents to gain a full understanding of the indicator's intent and requirements. Focus on information directly related to the indicator.
# 2. **Compare to the Regulation**: Using the evidence from the regulation, determine how well the indicator — as explained by the supporting documents — aligns with the regulatory requirements.
# 3. **Determine Alignment Level**: Select the most appropriate alignment category based on the comparison.
# 4. **Justify Your Choice**: Provide a clear justification, citing specific evidence from both the supporting documents and the regulation.

# **For each indicator, provide the following in your response:**
# - STATEMENT: The original indicator text.
# - EVIDENCE: A string formatted as:
#   "From Supporting Documents: '<direct excerpt from VSS>'\nFrom Regulation: '<direct excerpt from regulation>'"
#   If no relevant evidence is found for one source, state "No relevant evidence found".
# - CITATIONS: A string formatted as:
# "Supporting Documents: '<specific reference including page and source filename if available>'\nRegulation: '<specific reference including page number and source filename compulsory(e.g., regulation document name)>'"
# Always include the page number and the source filename if available in the metadata or provided evidence.
# If no citation is available for one source, state "No citation available
#   If no citation is available for one source, state "No citation available".
# - **ALIGNMENT CATEGORY**: The chosen category.
# - **JUSTIFICATION**: A detailed justification that references the evidence and explains the alignment.

# **IMPORTANT*: Return your results as a JSON array, one object per indicator, with the following keys, Dont miss any of the keys:
# - Indicator ID
# - STATEMENT
# - EVIDENCE
# - CITATIONS
# - ALIGNMENT CATEGORY
# - JUSTIFICATION
# - Alignment Label
# - Alignment Definition


# **Strict Rules**:
# - Do NOT use placeholder text like '<specific reference>' or '<direct excerpt>'. If no evidence or citation is found, explicitly state "No relevant evidence found" or "No citation available" as appropriate.
# - For "Mostly aligned," "Partially aligned," or "Fully aligned," you MUST provide at least one specific citation from the regulation with a valid page or section reference. If no such citation exists, the alignment MUST be "Not aligned/Not covered" or "Not applicable."


# **Additional Instructions**:
# - Return ONLY a valid JSON array, no explanations, no extra text, no tags, no trailing commas.
# - Ensure the array has exactly one object for each indicator in the batch, in the same order.
# - All string values must be properly escaped for JSON.
# - If you cannot answer for an indicator, return an empty string for its fields, but keep the object in the array.
# - Do not include any Markdown, HTML, or XML tags.

# """
#     indicators_text = ""
#     for i, item in enumerate(batch, 1):
#         indicators_text += f"""
# Indicator {i}:
# - Criteria ID: {item['indicator_id']}
# - Indicator: {item['question']}
# - Evidence from the Regulation: {item['evidence']}
# """
#     full_prompt = intro + "\n\n" + indicators_text + "\n\nOutput:"
#     return full_prompt



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



        #OUTPUT :

        For this indicator, provide the following in your response:
        Please give two lines of space between each category. (\\n\\n)
        
        STATEMENT: <original indicator>
         -two lines of space-
        EVIDENCE: A string formatted as:
        "From Supporting Documents: '<direct excerpt from VSS>' -two lines of space- From Regulation: '<direct excerpt from regulation>'"
        If no relevant evidence is found for one source, state "No relevant evidence found in [Supporting Documents/Regulation]".
        Add two newlines (\\n\\n) between the Supporting Documents and Regulation excerpts for readability.
        -two lines of space-
      - CITATIONS: A string formatted as:
        "Supporting Documents: '<source filename>, Page <number>, <section/paragraph/article or No additional details available>' two lines of space'Regulation: '<source filename>, Page <number>, <section/paragraph/article >'"
        Always include the page number and source filename. If no additional details are available, explicitly state so.e Add two newlines (\\n\\n) between the Supporting Documents and Regulation excerpts for readability.
         -two lines of space-
        ALIGNMENT CATEGORY: <chosen category>
         -two lines of space-
        JUSTIFICATION: <detailed justification>


        IMPORTANT: Do NOT use any markdown formatting (**, *, #, etc.) in your response. Use plain text only.
        
        Format your response exactly as follows with no asterisks or markdown:

        STATEMENT: ...
        EVIDENCE: ...
        CITATIONS: ...
        ALIGNMENT CATEGORY: ...
        JUSTIFICATION: ...

        Add two lines of space between each category

        """

    return analysis_prompt