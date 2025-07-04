"""
System prompt and alignment definitions for regulatory analysis.
"""

system_prompt = """
You are a regulatory compliance expert specializing in law, ESG, and sustainability standards.
You are evaluating whether specific indicators from a voluntary sustainability standard (VSS) conform to the requirements of a sustainability-related regulation (RAG).
You will be given:
- an **Indicator** from the VSS (sometimes phrased as a question)
- **Supporting Documents**: content of the VSS standard uploaded by the user
- **Evidence from RAG**: relevant passages retrieved from the regulation (stored in a knowledge base)

Your task is to:
- Rephrase the indicator into a clear positive statement if necessary.
- Review the Supporting Documents and Evidence from RAG.(RAG has the regulations)
- Determine how well the indicator aligns with the regulation (results from RAG), based on the provided evidence.
- Choose the most appropriate alignment category from the provided definitions.
- Justify your choice with specific evidence and citations.

Do NOT speculate or invent information. If evidence is insufficient or missing, state that clearly.
Be factual, concise, and rigorous in your analysis.
"""

alignment_def = {
    "Not applicable": {
        "Definition": "This requirement in the regulation is not applicable for the sector or commodity defined by the scope or intended use of the benchmarked standard. In certain cases, the topic may be pertinent only in exceptional circumstances and in such instances, we may still classify it as not applicable.",
        "Implication": ""
    },
    "Not aligned/Not covered": {
        "Definition": "This requirement in the regulation is not included in the assessed standard. Or this core topic of the criteria is not covered.",
        "Implication": "The requirements in the assessed standard are not present. Need to be reviewed or included."
    },
    "Partially aligned": {
        "Definition": "The assessed standard includes requirements similar to this regulatory criterion, but to a limited or substantially lower extent or rigour. Essential components necessary to fulfil the intent are absent, and should be given further consideration. A critical aspect of the regulatory criterion is missing.",
        "Implication": "Some aspects are missing and need to be reviewed."
    },
    "Mostly aligned": {
        "Definition": "This requirement in the regulation is fully included or aligned with the assessed standard, with minor aspects different (either more stringent or less stringent). The intent of this regulatory requirement is adequately addressed. While variances or omissions may arise in individual indicators, the overarching purpose of the relevant criteria is duly recognised in the benchmarked standard.",
        "Implication": "Considered to be covered by the benchmarked standard, and only minor aspects are different or missing."
    },
    "Fully aligned": {
        "Definition": "This requirement in the regulation is equivalent to the indicator in the assessed standard, covering the same scope and extent without deviation.",
        "Implication": "The requirement in the assessed standard is equivalent to this regulatory criterion. Considered to be fully covered by the benchmarked standard."
    }
}
