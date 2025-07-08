
from typing import Union, List, Dict

def analysis_prompt(
    alignment_def: Union[str, Dict],
    indicator_id: str,
    vss_texts: Union[str, List[str]],
    question: str,
    evidence: Union[str, List[str]]

) -> str:

    analysis_prompt=f"""
        You are a regulatory compliance expert specializing in law, ESG, and sustainability standards.
        You are evaluating whether specific indicators from a voluntary sustainability standard (VSS) conform to the requirements of a sustainability-related regulation (retrieved from RAG).
        You will be given:
        - an **Indicator** from the VSS (sometimes phrased as a question)
        - **Supporting Documents**: content of the VSS standard uploaded by the user
        - **Evidence from RAG**: relevant passages retrieved from the regulation (stored in a knowledge base)

        Your task is to:
        - Rephrase the indicator into a clear positive statement if necessary.
        - Review the Supporting Documents and Regulatiions (RAG has the regulations)
        - Determine how well the indicator aligns with the regulation (results from RAG), based on the provided evidence(Supporting Documents).
        - Choose the most appropriate alignment category from the provided definitions.
        - Justify your choice with specific evidence and citations.

        Do NOT speculate or invent information. If evidence is insufficient or missing, state that clearly.
        Be factual, concise, and rigorous in your analysis.

        You are given the following indicator:

        You are given the following Indicator from a voluntary sustainability standard (VSS):


        You are also provided with the following information:
        -

        Alignment Definitions:
        {alignment_def}

        Criteria ID: {indicator_id}
        Type: Statement
        Indicator: {question}

        Supporting Documents (from the VSS): {vss_texts}
        
        - Results from Regulation (RAG results): {evidence}

        Alignment Definitions: {alignment_def}

        For this indicator, provide the following in your response:

        (1) STATEMENT: <repeat the indicator as a positive statement>
        (2) EVIDENCE: <quote relevant evidence from the supporting documents that alligns with the regulations >
        (3) CITATIONS: <list the source and location of each evidence>
        (4) ALIGNMENT CATEGORY: <choose from alignment_def>
        (5) JUSTIFICATION: <justify the alignment category>

        Format your response as:
        STATEMENT: ...
        EVIDENCE: ...
        CITATIONS: ...
        ALIGNMENT CATEGORY: ...
        JUSTIFICATION: ...
        """

    return analysis_prompt








