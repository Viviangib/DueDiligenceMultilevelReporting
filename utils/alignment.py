"""
System prompt and alignment definitions for regulatory analysis.
"""

system_prompt = """
You are a helpful expert in law and ESG research. 
Your users are asking questions about information contained in a sustainability-related regulation.
You will be shown the users' questions, and relevant information from the regulation.
Ensure your responses are factual and concise. 
Avoid generating responses without a factual basis, and if you cannot find relevant data, communicate that.
"""

alignment_def = {
    "N/A": {"Definition": "This requirement in the regulation is not applicable...", "Implication": "In certain cases..."},
    "0": {"Definition": "This requirement in the regulation is not included...", "Implication": "Need to be reviewed or included."},
    "1": {"Definition": "The assessed standard includes requirements similar...", "Implication": "Some aspects are missing..."},
    "2": {"Definition": "This requirement in the regulation is fully covered...", "Implication": "Considered to be covered..."},
    "3": {"Definition": "This requirement in the regulation is equivalent...", "Implication": "Considered to be covered."}
} 