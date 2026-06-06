## CV Verification With GitHub



CV Verification is a backend service developed to validate and analyze the skills stated in candidates' CVs. The project combines CV parsing, GitHub-based skill verification, timeline analysis, and machine learning-based classification into a single system.

---------------------------------------------------------------

## Purpose

The goal of this project is to:

-Analyze the accuracy of the skills listed in a CV
-Evaluate a candidate’s real technical competencies more objectively
-Check consistency between GitHub activity and the information provided in the CV
-Make recruitment processes more data-driven

## Features

-CV parsing (PDF and DOCX support)
-Skill extraction (LLM-based)
-Skill verification via GitHub API integration
-Timeline analysis (experience duration and consistency)
-Machine learning-based classification
-RESTful API (FastAPI)

## Technologies

-Python
-FastAPI
-LLM APIs (Anthropic)

## Installation

1. Clone this repository:
git clone https://github.com/your-username/cv-verification.git
cd cv-verification

2. Create and activate a virtual environment:
python -m venv .venv
source .venv/bin/activate  # For Windows: .venv\\Scripts\\activate

3. Install dependencies:
pip install -r requirements.txt

4. Set up environment variables:
Create a .env file and fill it as follows:
ANTHROPIC_API_KEY=your_key

Running The Application
uvicorn app.main:app --reload

