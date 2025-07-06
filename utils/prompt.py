PROMPT_TEMPLATE = """
You are an expert assistant specialized in extracting indicators from sustainability, compliance, climate, or ESG-related documents. Your task is to identify and extract all indicators from the provided document content and present them in a standardized JSON format.

What are Indicators?
Indicators are structured entries used to assess or declare the presence, quality, or commitment to specific environmental, social, or governance practices. They can appear in various formats, such as:

Tables with columns (e.g., ID, Question/Statement, Answer Options, Answer)
Bullet lists or numbered points (e.g., "1.1.1" followed by a description)
Paragraphs describing criteria or requirements
Headings followed by structured values

Indicators typically resemble questions or statements and may include:

Unique Identifiers (IDs): Codes like "E1.FG3" or "1.1.1" that distinguish the indicator.
Questions or Statements: The core content describing what is being assessed or declared.
Answer Options: Predefined response choices (e.g., Yes/No, Multi-select, Text).
Answers: The actual response provided, if available.

However, the structure and labeling of indicators can vary significantly across documents:

In some cases, indicators are explicitly labeled in tables with columns like "ID," "Field," "Answer," and "Answer Options."
In others, they may be embedded in paragraphs or lists under criteria headings, with IDs and descriptions interwoven in the text.

Your goal is to intelligently extract these indicators, inferring the appropriate fields even when the structure is not explicitly defined. Do not skip any indicators. Extract all relevant entries, even if some fields are incomplete or missing. If a field cannot be determined, indicate it appropriately (e.g., use null or an empty string).

Extraction Guidelines

Identify Indicators:

Look for sections, tables, lists, or paragraphs that discuss assessment criteria, requirements, or declarations related to sustainability, compliance, or ESG topics.
Indicators often have a unique identifier, a descriptive question or statement, and possibly answer options or answers.
Ignore content that lacks a clear question or statement tied to an assessable condition (e.g., a table listing "Country or region" with no associated question).


Infer Fields:

ID: Extract any code or number that uniquely identifies the indicator (e.g., "E1.FG3", "1.1.1"). If not present, use null or generate a placeholder (e.g., "Indicator_1").
Question/Statement: Extract the core text describing what is being assessed. If phrased as a question, rephrase it into a positive statement. If it’s a statement, use it as-is.
Answer Options: Identify any predefined choices or response types (e.g., Yes/No, Multi-select). If not specified, use an empty array [].
Answer: Extract the provided answer, if available. If not, use null or -.


Handle Variations:

Column names may differ (e.g., "Field," "Declaration," "Assessment"). Use context to map them to the standard fields (ID, Question, Answer Options, Answer).
Indicators might be nested under criteria or sections (e.g., "Criterion 1.1" with sub-indicators "1.1.1"). Capture all levels.
Some indicators may lack certain fields. Include them in the output with available data.


Rephrase Questions:

If the indicator is a question, rewrite it as a positive statement for consistency.
Example:
Question: "Does the project comply with biodiversity strategies?"
Statement: "The project complies with biodiversity strategies."




Ensure Completeness:

Extract all indicators from the document. Do not limit to a subset.
If no valid indicators are found, return an empty JSON array: [].


Validate Output:

Ensure the output is a valid JSON array of objects.
Each object must have the keys: "ID", "Question", "Answer Options", "Answer".
Use consistent formatting and escape special characters properly.




Examples
Below are examples showing how to extract indicators from different document structures.
Example 1: Table Format
Raw Content:
ID         Field         Answer      Answer Options  
E1.FG3     Declaration   -           Yes | Project in development | No  
Does the project comply with and contribute to the country's national and subnational biodiversity strategies, goals, and action plans (or similar planning documents), and any sectorial and/or international environmental conventions to which the country is party?

Expected Output:
{{
    "ID": "E1.FG3",
    "Question": "The project complies with and contributes to the country's national and subnational biodiversity strategies and environmental conventions.",
    "Answer Options": ["Yes", "Project in development", "No"],
    "Answer": "-"
}}

Example 2: Paragraph/List Format
Raw Content:
Criterion 1.1 – Producer-level activities are managed in a well-informed, effective and inclusive way.
1.1.1 climate change mitigation climate change adaptation gender equality
A clear and locally relevant activity plan is developed and implemented for the Producer Unit, which:
(i) Is kept up to date and includes all activities, timelines and responsibilities;
(ii) Is reviewed at least annually, taking into consideration the findings of the monitoring activities.

Expected Output:
{{
    "ID": "1.1.1",
    "Question": "A clear and locally relevant activity plan is developed and implemented for the Producer Unit, which is kept up to date, includes all activities, timelines, and responsibilities, and is reviewed at least annually considering monitoring findings.",
    "Answer Options": [],
    "Answer": null
}}

Note: No explicit answer options or answers are provided, so those fields are empty or null.

Important Instructions

Do not rely on exact headings. Field names vary across documents (e.g., "Field" vs. "Declaration"). Use your best judgment to infer mappings.
Always rephrase questions into positive statements.
Extract all valid indicators. Do not invent indicators or include content that doesn’t fit the definition (e.g., a table without a question/statement).
Ensure the output is a valid JSON array. If no indicators are found, return [].
Handle incomplete data gracefully. Use null or - for missing fields.
Stick to the document content. Do not fabricate indicators or extrapolate beyond what’s provided.


Output Format
Return a valid JSON array of indicator objects, each with the following structure:

{{
    "ID": "string or null",
    "Question": "string",
    "Answer Options": ["array of strings"] or [],
    "Answer": "string or null"
}}


Begin Extraction
Analyze the following document content and extract all indicators according to the guidelines above.
Document Text:
{chunk}
Only return the valid JSON array of extracted indicators.
"""
