import os
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from ddgs import DDGS
from groq import Groq


# Define the input schema
class JobSearchInput(BaseModel):
    query: str = Field(
        description="The job title or technical keywords. IMPORTANT: Extract these from the user's resume/notes in the RAG database."
    )
    location: str = Field(
        description="The target city or 'Remote'. If not specified in the conversation, check the user's 'dream_jobs.md' file."
    )



@tool
def search_jobs(query: str, location: str):
    """
    Executes a filtered search for real job postings in a given location.
    Automatically excludes common job-board spam and SEO traps.
    """
    # 1. Define the "Blacklist" of sites to ignore
    # These sites often contain repetitive ads or "hidden job" traps.
    blacklist = [
        "jooble.org",
        "ziprecruiter.com",
        "trovit.com",
        "talent.com",
        "jobrapido.com",
        "learn4good.com",
        "whatjobs.com",
    ]

    exclude_str = " ".join([f"-site:{site}" for site in blacklist])

    advanced_query = (
        f"{query} \"{location}\" "
        f"(site:greenhouse.io OR site:lever.co OR site:linkedin.com/jobs/view OR site:ca.indeed.com/viewjob) "
        f"{exclude_str}"
    )

    print(f"--- Executing Filtered Search: {advanced_query} ---")
    
    try:
        results = []
        with DDGS() as ddgs:
            response = ddgs.text(advanced_query, max_results=5)
            for r in response:
                results.append({
                    "title": r.get("title"),
                    "link": r.get("href"),
                    "snippet": r.get("body")
                })
        
        if not results:
            return "No high-quality jobs found. Try a more specific job title."
            
        return results

    except Exception as e:
        return f"Error during search: {str(e)}"

@tool
def evaluate_job_fit(resume_text: str, job_description: str) -> str:
    """
    Compares a job description against a resume using an LLM.
    Returns a JSON object with a score from 1-10 and a list of missing skills.
    """
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    prompt = f"""You are a career advisor. Score how well this candidate fits the job.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Scoring rubric:
- 9-10: Exceptional match, meets nearly all requirements
- 7-8: Strong match, meets most key requirements
- 5-6: Moderate match, some gaps
- 3-4: Weak match, significant gaps
- 1-2: Poor match, fundamental mismatch

Respond with ONLY this JSON (no other text):
{{"score": <integer 1-10>, "missing_skills": [<list of missing skills, or empty list>]}}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    return response.choices[0].message.content

tools = [search_jobs, evaluate_job_fit]