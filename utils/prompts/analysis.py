
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
        3. **Comprehensive Evidence Collection**: Thoroughly review ALL provided evidence from both supporting documents and regulations. 
           Extract COMPLETE FULL PARAGRAPHS and sections, not just single sentences. Each evidence item should be a substantial excerpt that provides full context and meaning. Do not stop at the first relevant piece - continue to find all applicable evidence. Please make numerical bullet points
        4. **Compare to the Regulation**: Using the evidence from the regulation, determine how well the indicator (with its context from the supporting documents) 
           aligns with the regulatory requirements.
        5. **Determine Alignment Level**: Based on your comparison, select the most appropriate alignment category from the provided definitions.
        6. **Justify Your Choice**: Provide a clear justification for your alignment category, citing specific evidence from both the supporting documents and the regulation.

        **Important Rules**:
        - **Evidence Citation**: If the alignment category is "Partially aligned," "Mostly aligned," or "Fully aligned," you must include at least one citation from the regulation in your evidence. 
          For "Not aligned/Not covered" or "Not applicable," you may cite only from the supporting documents if necessary. Make numerical bullet points with spacing for evidence and citations.
        - **Comprehensive Evidence Gathering**: Extract and cite ALL relevant evidence from both the supporting documents and regulations. Do not limit yourself to 1-2 references. 
          Look for multiple relevant passages, paragraphs, and sections that relate to the indicator. The more comprehensive the evidence, the better the analysis.
        - **Full Paragraph Extraction**: When citing, extract the COMPLETE FULL PARAGRAPH or entire section, not just a single sentence. 
          Each evidence item should be a substantial, meaningful excerpt that provides complete context. Avoid short snippets or partial sentences.
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
        5. Aim for as many evidence points as possible (ranging from 1 to 10) total from all sources combined
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
and social impacts. Stakeholder engagement is an on-going process that may involve, in varying degrees, the following elements: stakeholder analysis and planning, disclosure and dissemination of information, consultation and participation, grievance mechanism, and on-going reporting to affected communities. The nature, frequency, and level of effort of stakeholder engagement may vary considerably and will be commensurate with the project’s risks and adverse impacts, and the project’s phase of development."

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