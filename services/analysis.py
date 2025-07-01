import logging
import pandas as pd
from sqlalchemy.orm import Session
from models.indicator import Indicator
from utils.alignment import alignment_def, system_prompt
from vector_store.pinecone_store import rag_search
from openai import AsyncOpenAI
import uuid
import os

# Configure logging
logger = logging.getLogger(__name__)

class AnalysisService:
    async def run_analysis(self, db: Session, vss_paths: list[str]) -> str:
        """
        For each of 20 indicators from the DB, use RAG (Pinecone) to search the standard,
        pass the results and supporting docs to GPT-4, and save the results to Excel.
        """
        logger.info("Starting analysis service")
        
        # 1. Get 20 indicators from DB
        logger.info("Fetching 20 indicators from database")
        indicators = db.query(Indicator).limit(20).all()
        logger.info(f"Retrieved {len(indicators)} indicators from database")
        
        if not indicators:
            logger.error("No indicators found in database")
            raise Exception("No indicators found in DB.")
        
        # 2. Prepare VSS supporting docs (read all text)
        logger.info(f"Processing {len(vss_paths)} VSS files")
        vss_texts = []
        for i, path in enumerate(vss_paths):
            logger.info(f"Processing VSS file {i+1}/{len(vss_paths)}: {path}")
            ext = os.path.splitext(path)[1].lower()
            
            if ext == ".pdf":
                logger.info("Processing PDF file")
                import pdfplumber
                with pdfplumber.open(path) as pdf:
                    text = "".join(page.extract_text() or "" for page in pdf.pages)
                    vss_texts.append(text)
                    logger.info(f"PDF processed. Text length: {len(text)} characters")
            elif ext == ".docx":
                logger.info("Processing DOCX file")
                from docx import Document
                doc = Document(path)
                text = "\n".join([p.text for p in doc.paragraphs])
                vss_texts.append(text)
                logger.info(f"DOCX processed. Text length: {len(text)} characters")
            else:
                logger.warning(f"Unsupported file type: {ext}")
        
        logger.info(f"VSS processing complete. Total VSS texts: {len(vss_texts)}")
        
        # 3. For each indicator, do RAG and LLM
        logger.info("Initializing OpenAI client")
        client = AsyncOpenAI()
        results = []
        
        logger.info(f"Starting analysis of {len(indicators)} indicators")
        for idx, indicator_obj in enumerate(indicators):
            logger.info(f"Processing indicator {idx+1}/{len(indicators)}")
            
            indicator_text = indicator_obj.indicator
            logger.info(f"Indicator text: {indicator_text[:100]}...")
            
            # RAG: search Pinecone for evidence
            logger.info("Performing RAG search")
            try:
                evidence = rag_search(str(indicator_text))
                logger.info(f"RAG search completed. Found {len(evidence)} evidence pieces")
            except Exception as e:
                logger.error(f"RAG search failed: {str(e)}")
                evidence = ["RAG search failed"]
            
            # Compose prompt
            logger.info("Composing LLM prompt")
            prompt = f"""
{system_prompt}

You are given the following indicator:

Criteria ID: IND{idx+1:03d}
Type: Statement
Indicator: {indicator_text}

Supporting Documents: {vss_texts}

Evidence from RAG: {evidence}

Alignment Definitions: {alignment_def}

For this indicator, provide the following in your response:

(1) STATEMENT: <repeat the indicator as a positive statement>
(2) EVIDENCE: <quote relevant evidence from the supporting documents and RAG>
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
            logger.info("Calling GPT-4")
            try:
                response = await client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}]
                )
                content = response.choices[0].message.content if response.choices and response.choices[0].message.content else ""
                logger.info(f"GPT-4 response received. Length: {len(content)} characters")
            except Exception as e:
                logger.error(f"GPT-4 call failed: {str(e)}")
                content = "GPT-4 analysis failed"
            
            # Parse the response into columns
            logger.info("Parsing GPT-4 response")
            def extract_section(label):
                if label+":" in content:
                    return content.split(label+":")[1].split("\n")[0].strip()
                return ""
            
            alignment_category = extract_section("ALIGNMENT CATEGORY")
            logger.info(f"Extracted alignment category: {alignment_category}")
            
            result = {
                "Criteria": f"IND{idx+1:03d}",
                "ID": idx+1,
                "Type": "Statement",
                "Indicator": indicator_text,
                "GPT-4": content,
                "Alignment_Category": alignment_category
            }
            results.append(result)
            logger.info(f"Indicator {idx+1} analysis complete")
        
        logger.info(f"All indicators processed. Total results: {len(results)}")
        
        # 4. Save to Excel
        logger.info("Generating Excel file")
        output_file = f"results/analysis_results_{uuid.uuid4()}.xlsx"
        os.makedirs("results", exist_ok=True)
        
        try:
            df = pd.DataFrame(results)
            df.to_excel(output_file, index=False)
            logger.info(f"Excel file saved successfully: {output_file}")
        except Exception as e:
            logger.error(f"Excel generation failed: {str(e)}")
            raise Exception(f"Failed to generate Excel file: {str(e)}")
        
        logger.info("Analysis service completed successfully")
        return output_file 