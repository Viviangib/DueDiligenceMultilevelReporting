"""Constants for the application."""

# System prompts for AI interactions
SYSTEM_PROMPT = """
You are a helpful expert in law and ESG research. 
Your users are asking questions about information contained in a sustainability-related regulation.
You will be shown the users' questions, and relevant information from the regulation.
Ensure your responses are factual and concise. 
Avoid generating responses without a factual basis, and if you cannot find relevant data, communicate that.
"""

# Alignment definitions for regulation analysis
ALIGNMENT_DEF = {
    "N/A": {
        "Definition": "This requirement in the regulation is not applicable for the sector or commodity defined by the scope or intended use of the benchmarked standard. In certain cases, the topic may be pertinent only in exceptional circumstances and in such instances, we may still classify it as not applicable.",
        "Implication": "Not applicable for the current context."
    },
    "0": {
        "Definition": "This requirement in the regulation is not included in the assessed standard. Or this core topic of the criteria is not covered.",
        "Implication": "Need to be reviewed or included."
    },
    "1": {
        "Definition": "The assessed standard includes requirements similar to this regulatory criterion, but to a limited or substantially lower extent or rigour; essential components necessary to fulfil the intent is absent, and should be given further consideration. Critical aspect of the regulatory criterion is missing.",
        "Implication": "Some aspects are missing, and need to be reviewed."
    },
    "2": {
        "Definition": "This requirement in the regulation is fully covered or fully included, fully aligned with the assessed standard, with minor aspects different (either more stringent or less stringent) extent. The intent of this regulatory requirement is adequately addressed, while variances or omissions may arise in individual indicators, the overarching purpose of the relevant criteria is duly recognised in the benchmarked standard.",
        "Implication": "Considered to be covered by the benchmarked standard, and only minor aspects are different or missing."
    },
    "3": {
        "Definition": "This requirement in the regulation is equivalent to the indicator in the assessed standard, covering the same scope and extent without deviation.",
        "Implication": "Considered to be covered by the benchmarked standard."
    }
}