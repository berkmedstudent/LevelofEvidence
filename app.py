from flask import Flask, render_template, request, jsonify, send_file
import json
from evidence_grading import EvidenceGradingSystem
import pandas as pd
from io import BytesIO
import datetime
import PyPDF2
import re
import os
from flask_cors import CORS
from PyPDF2 import PdfReader
import io

app = Flask(__name__)
CORS(app)
grading_system = EvidenceGradingSystem()

@app.route('/')
def home():
    return render_template('index.html')

def extract_pdf_content(pdf_file):
    """Extract text content from a PDF file."""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_paper_info_from_pdf(text):
    """Extract relevant information from PDF text using regex patterns."""
    # Initialize default values
    paper_info = {
        "paper_id": "PDF_" + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'),
        "title": "Unknown",
        "study_type": "unknown",
        "methodology": "unknown",
        "sample_size": 0,
        "control_group": "unknown",
        "randomization": "unknown",
        "blinding": "unknown",
        "follow_up": 0,
        "statistical_analysis": "unknown",
        "risk_of_bias": "unknown",
        "consistency": "unknown",
        "directness": "unknown",
        "precision": "unknown"
    }
    
    # Extract title (usually at the beginning of the document)
    title_match = re.search(r'^(.+?)(?:\n|$)', text, re.MULTILINE)
    if title_match:
        paper_info["title"] = title_match.group(1).strip()
    
    # Extract study type with more comprehensive patterns
    study_types = {
        "randomized controlled trial": r"\b(randomized\s+controlled\s+trial|RCT)\b",
        "systematic review": r"\b(systematic\s+review|meta-analysis)\b",
        "cohort study": r"\b(cohort\s+study|prospective\s+study)\b",
        "case-control study": r"\b(case-control\s+study|retrospective\s+study)\b",
        "case series": r"\b(case\s+series|case\s+report)\b"
    }
    
    for study_type, pattern in study_types.items():
        if re.search(pattern, text.lower(), re.IGNORECASE):
            paper_info["study_type"] = study_type
            break
    
    # Extract methodology with improved patterns
    methodology_patterns = {
        "systematic review": r"\b(systematic\s+review|meta-analysis)\b",
        "cohort study": r"\b(cohort\s+study|prospective\s+study)\b",
        "case-control": r"\b(case-control\s+study|retrospective\s+study)\b",
        "cross-sectional": r"\b(cross-sectional\s+study|survey)\b",
        "observational": r"\b(observational\s+study|descriptive\s+study)\b"
    }
    
    for methodology, pattern in methodology_patterns.items():
        if re.search(pattern, text.lower(), re.IGNORECASE):
            paper_info["methodology"] = methodology
            break
    
    # Extract sample size with improved pattern
    sample_size_patterns = [
        r"(?:sample\s+size|n\s*=|participants|subjects|patients)\s*[=:]\s*(\d+)",
        r"(?:total\s+of|included|enrolled)\s+(\d+)\s+(?:patients|participants|subjects)",
        r"(?:study\s+included|study\s+enrolled)\s+(\d+)\s+(?:patients|participants|subjects)"
    ]
    
    for pattern in sample_size_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            paper_info["sample_size"] = int(match.group(1))
            break
    
    # Extract control group information with improved patterns
    control_group_patterns = {
        "yes": [
            r"\b(control\s+group|comparison\s+group)\b",
            r"\b(compared\s+with|compared\s+to)\b",
            r"\b(versus|vs\.?)\b"
        ],
        "no": [
            r"\b(no\s+control\s+group|single\s+arm|single\s+group)\b",
            r"\b(uncontrolled\s+study)\b"
        ]
    }
    
    for value, patterns in control_group_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text.lower(), re.IGNORECASE):
                paper_info["control_group"] = value
                break
    
    # Extract randomization information
    randomization_patterns = {
        "yes": [
            r"\b(randomized|randomisation|randomization)\b",
            r"\b(randomly\s+assigned|random\s+assignment)\b"
        ],
        "no": [
            r"\b(non-randomized|non-randomised)\b",
            r"\b(not\s+randomized|not\s+randomised)\b"
        ]
    }
    
    for value, patterns in randomization_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text.lower(), re.IGNORECASE):
                paper_info["randomization"] = value
                break
    
    # Extract blinding information
    blinding_patterns = {
        "double-blind": [
            r"\b(double\s*-?\s*blind|double\s*-?\s*blinded)\b",
            r"\b(double\s*-?\s*blind\s+study)\b"
        ],
        "single-blind": [
            r"\b(single\s*-?\s*blind|single\s*-?\s*blinded)\b",
            r"\b(single\s*-?\s*blind\s+study)\b"
        ],
        "no": [
            r"\b(no\s+blinding|unblinded|open\s+label)\b",
            r"\b(not\s+blinded)\b"
        ]
    }
    
    for value, patterns in blinding_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text.lower(), re.IGNORECASE):
                paper_info["blinding"] = value
                break
    
    # Extract follow-up period with improved patterns
    follow_up_patterns = [
        r"(?:follow-up|follow\s+up)\s*(?:period|time)?\s*(?:of)?\s*(\d+)\s*(?:months|years|weeks)",
        r"(?:followed\s+for|followed\s+up\s+for)\s*(\d+)\s*(?:months|years|weeks)",
        r"(?:median\s+follow-up|mean\s+follow-up)\s*(?:of)?\s*(\d+)\s*(?:months|years|weeks)"
    ]
    
    for pattern in follow_up_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            paper_info["follow_up"] = int(match.group(1))
            break
    
    # Extract statistical analysis information
    statistical_patterns = {
        "comprehensive": [
            r"\b(comprehensive\s+statistical\s+analysis)\b",
            r"\b(detailed\s+statistical\s+analysis)\b",
            r"\b(advanced\s+statistical\s+methods)\b"
        ],
        "adequate": [
            r"\b(statistical\s+analysis|statistical\s+methods)\b",
            r"\b(appropriate\s+statistical\s+analysis)\b"
        ],
        "basic": [
            r"\b(basic\s+statistical\s+analysis)\b",
            r"\b(simple\s+statistical\s+methods)\b"
        ]
    }
    
    for value, patterns in statistical_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text.lower(), re.IGNORECASE):
                paper_info["statistical_analysis"] = value
                break
    
    # Extract quality assessment information
    quality_patterns = {
        "risk_of_bias": {
            "low": r"\b(low\s+risk\s+of\s+bias|minimal\s+bias)\b",
            "moderate": r"\b(moderate\s+risk\s+of\s+bias|some\s+bias)\b",
            "high": r"\b(high\s+risk\s+of\s+bias|significant\s+bias)\b"
        },
        "consistency": {
            "high": r"\b(high\s+consistency|consistent\s+results)\b",
            "moderate": r"\b(moderate\s+consistency|somewhat\s+consistent)\b",
            "low": r"\b(low\s+consistency|inconsistent\s+results)\b"
        },
        "directness": {
            "high": r"\b(high\s+directness|direct\s+evidence)\b",
            "moderate": r"\b(moderate\s+directness|somewhat\s+direct)\b",
            "low": r"\b(low\s+directness|indirect\s+evidence)\b"
        },
        "precision": {
            "high": r"\b(high\s+precision|precise\s+estimates)\b",
            "moderate": r"\b(moderate\s+precision|somewhat\s+precise)\b",
            "low": r"\b(low\s+precision|imprecise\s+estimates)\b"
        }
    }
    
    for quality_type, levels in quality_patterns.items():
        for level, pattern in levels.items():
            if re.search(pattern, text.lower(), re.IGNORECASE):
                paper_info[quality_type] = level
                break
    
    return paper_info

@app.route('/grade', methods=['POST'])
def grade():
    try:
        if request.is_json:
            # Handle JSON file upload
            data = request.get_json()
            if isinstance(data, list):
                # Multiple papers
                results = []
                for paper in data:
                    grader = EvidenceGrading()
                    result = grader.grade_paper(paper)
                    results.append(result)
                return jsonify(results)
            else:
                # Single paper
                grader = EvidenceGrading()
                result = grader.grade_paper(data)
                return jsonify(result)
        else:
            # Handle form submission
            data = {
                "study_type": request.form.get('study_type'),
                "methodology": request.form.get('methodology'),
                "sample_size": request.form.get('sample_size'),
                "control_group": request.form.get('control_group'),
                "randomization": request.form.get('randomization'),
                "blinding": request.form.get('blinding'),
                "follow_up": request.form.get('follow_up'),
                "statistical_analysis": request.form.get('statistical_analysis'),
                "risk_of_bias": request.form.get('risk_of_bias'),
                "consistency": request.form.get('consistency'),
                "directness": request.form.get('directness'),
                "precision": request.form.get('precision')
            }
            grader = EvidenceGrading()
            result = grader.grade_paper(data)
            return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/process_pdf', methods=['POST'])
def process_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.pdf'):
        return jsonify({'error': 'File must be a PDF'}), 400
    
    try:
        # Read PDF content
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        
        # Extract paper information
        paper_info = extract_paper_info_from_pdf(text)
        
        # Grade the paper
        grading_system = EvidenceGradingSystem()
        grading_result = grading_system.grade_paper(paper_info)
        
        # Print debug information
        print("Paper Info:", paper_info)
        print("Grading Result:", grading_result)
        
        # Combine paper info with grading result
        result = {
            'title': paper_info.get('title', 'Not found'),
            'study_type': paper_info.get('study_type', 'Not found'),
            'methodology': paper_info.get('methodology', 'Not found'),
            'sample_size': paper_info.get('sample_size', 'Not found'),
            'control_group': paper_info.get('control_group', 'Not found'),
            'risk_of_bias': paper_info.get('risk_of_bias', 'Not found'),
            'consistency': paper_info.get('consistency', 'Not found'),
            'directness': paper_info.get('directness', 'Not found'),
            'precision': paper_info.get('precision', 'Not found'),
            'evidence_level': grading_result.get('evidence_level', 'Not graded'),
            'scores': grading_result.get('scores', {}),
            'raw_text': text[:1000]  # First 1000 characters as preview
        }
        
        print("Final Result:", result)
        return jsonify(result)
    except Exception as e:
        print("Error:", str(e))
        return jsonify({'error': f'Error processing PDF: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True) 