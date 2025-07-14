#!/usr/bin/env python3
"""
Test script for the new report generation functionality.
This script demonstrates how to use the report generation endpoints.
"""

import requests
import os
import sys

def test_report_generation_with_file_path():
    """
    Test the report generation endpoint using a file path.
    """
    print("Testing report generation with file path...")
    
    # Example Excel file path (replace with actual path)
    excel_file_path = "results/analysis_results_1db80bc0-0c06-42e4-88e2-56be0ddd257a.xlsx"
    
    if not os.path.exists(excel_file_path):
        print(f"Error: Excel file not found at {excel_file_path}")
        return
    
    url = "http://localhost:8000/analysis/generate-report"
    
    data = {
        "excel_file_path": excel_file_path,
        "standard_name": "FSC Forest Management Standard",
        "standard_version": "FSC-STD-01-001",
        "standard_year": "2022",
        "organization": "Forest Stewardship Council"
    }
    
    try:
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            # Save the report
            with open("generated_report.md", "wb") as f:
                f.write(response.content)
            print("✅ Report generated successfully! Saved as 'generated_report.md'")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_report_generation_with_file_upload():
    """
    Test the report generation endpoint using file upload.
    """
    print("\nTesting report generation with file upload...")
    
    # Example Excel file path (replace with actual path)
    excel_file_path = "results/analysis_results_1db80bc0-0c06-42e4-88e2-56be0ddd257a.xlsx"
    
    if not os.path.exists(excel_file_path):
        print(f"Error: Excel file not found at {excel_file_path}")
        return
    
    url = "http://localhost:8000/analysis/generate-report-upload"
    
    data = {
        "standard_name": "FSC Forest Management Standard",
        "standard_version": "FSC-STD-01-001",
        "standard_year": "2022",
        "organization": "Forest Stewardship Council"
    }
    
    files = {
        "excel_file": ("analysis_results.xlsx", open(excel_file_path, "rb"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    }
    
    try:
        response = requests.post(url, data=data, files=files)
        
        if response.status_code == 200:
            # Save the report
            with open("generated_report_upload.md", "wb") as f:
                f.write(response.content)
            print("✅ Report generated successfully! Saved as 'generated_report_upload.md'")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def main():
    """
    Main function to run the tests.
    """
    print("🚀 Testing Report Generation Functionality")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/docs")
        if response.status_code != 200:
            print("❌ Error: FastAPI server is not running on localhost:8000")
            print("Please start the server first with: python server.py")
            return
    except:
        print("❌ Error: Cannot connect to FastAPI server")
        print("Please start the server first with: python server.py")
        return
    
    # Run tests
    test_report_generation_with_file_path()
    test_report_generation_with_file_upload()
    
    print("\n" + "=" * 50)
    print("✅ Testing completed!")

if __name__ == "__main__":
    main() 