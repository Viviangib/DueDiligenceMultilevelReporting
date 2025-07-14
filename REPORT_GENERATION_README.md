# Report Generation Functionality

This document describes the new report generation functionality that creates comprehensive benchmarking summary reports from analysis Excel files.

## Overview

The report generation feature takes Excel files containing analysis results (400-500 records) and generates professional benchmarking summary reports following the GIB (Global Infrastructure Basel Foundation) template format.

## Why This Approach?

✅ **Your approach is correct!** Here's why:

1. **Direct Excel Processing**: Processing the entire Excel file at once is more efficient than generating summaries per indicator
2. **Better Context**: GPT can see the full dataset and generate coherent, well-structured reports
3. **Simpler Architecture**: No need to store intermediate summaries or combine multiple reports
4. **Better Performance**: Single API call instead of multiple processing steps

## New Endpoints

### 1. File Path Endpoint

```
POST /analysis/generate-report
```

**Parameters:**

- `excel_file_path` (required): Path to the Excel file containing analysis results
- `standard_name` (optional): Name of the benchmarked standard (default: "User Standard")
- `standard_version` (optional): Version of the standard (default: "1.0")
- `standard_year` (optional): Year of publication (default: "2024")
- `organization` (optional): Name of the founding organization (default: "User Organization")

### 2. File Upload Endpoint

```
POST /analysis/generate-report-upload
```

**Parameters:**

- `excel_file` (required): Uploaded Excel file containing analysis results
- `standard_name` (optional): Name of the benchmarked standard (default: "User Standard")
- `standard_version` (optional): Version of the standard (default: "1.0")
- `standard_year` (optional): Year of publication (default: "2024")
- `organization` (optional): Name of the founding organization (default: "User Organization")

## Report Structure

The generated report follows the GIB template format and includes:

1. **General Information**

   - Standard name, version, and publication year
   - Founding parties
   - Report generation date
   - About GIB section
   - Disclaimer

2. **Abbreviations**

   - Comprehensive list of relevant abbreviations
   - Industry-specific terms

3. **Benchmarking Results**

   - Alignment level definitions (N/A, 0, 1, 2, 3)
   - Clear definitions and implications

4. **Preliminary Benchmarking Summary**

   - Comprehensive table with indicator data
   - Alignment statistics
   - Key findings and patterns
   - Areas of strength and weakness

5. **Recommendations**

   - Potential gaps identification
   - Specific, actionable recommendations
   - Priority areas for enhancement

6. **References**

   - APA citation style
   - Standard regulatory references
   - Additional relevant sources

7. **Appendices**
   - Glossary of terms
   - Benchmarking process description

## Usage Examples

### Python Script Example

```python
import requests

# Using file path endpoint
url = "http://localhost:8000/analysis/generate-report"
data = {
    "excel_file_path": "results/analysis_results_xxx.xlsx",
    "standard_name": "FSC Forest Management Standard",
    "standard_version": "FSC-STD-01-001",
    "standard_year": "2022",
    "organization": "Forest Stewardship Council"
}

response = requests.post(url, data=data)
if response.status_code == 200:
    with open("report.md", "wb") as f:
        f.write(response.content)
```

### cURL Example

```bash
# File path endpoint
curl -X POST "http://localhost:8000/analysis/generate-report" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "excel_file_path=results/analysis_results_xxx.xlsx&standard_name=FSC%20Standard"

# File upload endpoint
curl -X POST "http://localhost:8000/analysis/generate-report-upload" \
  -F "excel_file=@results/analysis_results_xxx.xlsx" \
  -F "standard_name=FSC Standard"
```

## File Structure

The implementation follows your preferred backend organization:

```
backend/
├── routers/analysis.py          # HTTP endpoints
├── controllers/analysis.py      # Business logic orchestration
├── services/analysis.py         # Core report generation logic
├── utils/prompts/report.py      # GPT prompt for report generation
└── results/                     # Generated reports stored here
```

## Technical Implementation

### 1. Prompt Engineering (`utils/prompts/report.py`)

- Comprehensive prompt that follows the exact GIB template
- Handles all report sections and formatting
- Includes proper citations and references

### 2. Service Layer (`services/analysis.py`)

- `generate_summary_report()` method
- Excel file processing with pandas
- GPT integration using existing OpenAI client
- File management and error handling

### 3. Controller Layer (`controllers/analysis.py`)

- `generate_report_controller()` function
- Input validation and error handling
- File response management

### 4. Router Layer (`routers/analysis.py`)

- Two endpoints for different use cases
- Form data handling
- File upload processing

## Testing

Run the test script to verify functionality:

```bash
python test_report_generation.py
```

This will test both endpoints with sample data.

## Error Handling

The implementation includes comprehensive error handling:

- File existence validation
- File format validation (Excel only)
- GPT API error handling
- Temporary file cleanup
- Proper HTTP status codes

## Performance Considerations

- **Large Files**: Can handle Excel files with 400-500 records efficiently
- **Memory Usage**: Processes data in chunks to avoid memory issues
- **Response Time**: Typically 30-60 seconds for comprehensive reports
- **File Cleanup**: Automatic cleanup of temporary files

## Best Practices

1. **Use the upload endpoint** for better user experience
2. **Provide meaningful standard information** for better report quality
3. **Monitor file sizes** - very large files may take longer
4. **Handle timeouts** appropriately in client applications
5. **Store generated reports** for future reference

## Future Enhancements

Potential improvements:

- Report caching to avoid regeneration
- PDF output format option
- Customizable report templates
- Batch processing for multiple files
- Report versioning and history
