PROMPT_TEMPLATE = """
You are a smart assistant that extracts **indicators** from a document.

---

📌 **What are indicators?**

Indicators are structured entries typically used in sustainability, compliance, climate, or ESG-related documents to assess or declare whether certain conditions, plans, or policies exist. They are meant to capture the presence, quality, or commitment to environmental, social, or governance practices.

Indicators may appear in:
- Tables
- Bullet lists
- Paragraphs
- Headings with structured values below

They often look like **questions**, but they can also be **statements**. They may contain **answer options** (like Yes/No), allow for **free text**, or link to a **file upload**.

You are expected to intelligently extract these indicators regardless of format.

---

🎯 **Your goal: Extract as many indicators as possible from the document content.**

Do NOT rely on exact headings. Field names will vary from document to document. Use your best judgment to infer proper headings and meaning, even if structure is not perfect.

for example an  extracted indicator can include: (this is just an example, the headings can be different and can be less or more)
- "ID": The unique identifier for the indicator (e.g., "E1.FG3", "MS.1PV", etc.)
- "Question": The full sentence of the indicator, rephrased as a **positive statement**. If it was originally a question, rewrite it in declarative form.
- "Answer Options": A list of possible response values, if available (e.g., ["Yes", "No", "Partial", "Plan in progress"])
- "Answer": The selected value if it's already present (use "-" if unanswered)

---

🧠 **Examples to guide you:**

📄 Example 1:  
Raw content:
ID         Field         Answer      Answer Options  
E1.FG3     Declaration   -           Yes | Project in development | No  
Does the project comply with and contribute to the country's national and subnational biodiversity strategies, goals, and action plans (or similar planning documents), and any sectorial and/or international environmental conventions to which the country is party?

➡ Output:
{{
  "ID": "E1.FG3",
  "Question": "The project complies with and contributes to the country's national and subnational biodiversity strategies and environmental conventions.",
  "Answer Options": ["Yes", "Project in development", "No"],
  "Answer": "-"
}}

📄 Example 2:  
Raw content:
ID         Field         Answer      Answer Options  
MS.YP8     Assessment    -           Yes | No | List of entity names  
Does the project have an Environmental and Social Impact Assessment (ESIA) in place?

➡ Output:
{{
  "ID": "MS.YP8",
  "Question": "The project has an Environmental and Social Impact Assessment (ESIA) in place.",
  "Answer Options": ["Yes", "No", "List of entity names"],
  "Answer": "-"
}}

📄 Example 3:  
Raw content:
ID         Field         Answer      Answer Options  
MS.1PV     Risk          -           Yes | No | No, but commit to  
Does the project have a climate risk (and resilience) assessment in place that aligns with the Task Force on Climate-related Financial Disclosure (TCFD) guidelines?

➡ Output:
{{
  "ID": "MS.1PV",
  "Question": "The project has a climate risk (and resilience) assessment in place that aligns with the Task Force on Climate-related Financial Disclosure (TCFD) guidelines.",
  "Answer Options": ["Yes", "No", "No, but commit to"],
  "Answer": "-"
}}

---

📎 **Important Instructions:**
- Field labels like "Field", "Declaration", "Assessment", etc. may vary. Generalize and infer headings as needed.
- Always rephrase indicator questions into **positive statements**.
- Extract **all indicators** from the document, not just a few.
- If no indicators are found, respond with: []

---

📤 **Expected Output Format:**
A valid **JSON array** of indicator objects, like (just an example, create json array of indicators beased on the headings in the document):

[
  {{
    "ID": "E1.FG3",
    "Question": "The project complies with and contributes to biodiversity strategies.",
    "Answer Options": ["Yes", "Project in development", "No"],
    "Answer": "-"
  }},
  ...
]

---

🧾 Begin extraction below. Only return a valid JSON array.
Document Text:
{chunk}
"""
