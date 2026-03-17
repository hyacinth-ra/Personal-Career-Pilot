
# File: main.py
import asyncio
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from src.tools import search_jobs, evaluate_job_fit
from src.graph import create_job_research_graph
from langchain_core.messages import SystemMessage, HumanMessage

# MCP Imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools



load_dotenv()

async def main():
    # --- RESUME OPTION ---
    # Set to True to use the cached resume summary (saves tokens).
    # Set to False to re-read the full PDF and regenerate the summary.
    USE_CACHED_RESUME = True

    resume_cache_path = "./knowledge_base/resume_summary.txt"
    cached_resume_exists = os.path.exists(resume_cache_path)

    if USE_CACHED_RESUME and cached_resume_exists:
        resume_instruction = f"Use 'read_local_file' to read '{resume_cache_path}' to understand the user's skills."
    else:
        resume_instruction = (
            "Use 'read_local_file' to read './knowledge_base/resume.pdf' to understand the user's skills. "
            f"Then use 'save_job_results' to save a concise plain-text summary of the user's skills and experience to '{resume_cache_path}' for future use."
        )

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY")
    )
    
    # 1. Define the server parameters correctly
    server_params = StdioServerParameters(
        command="python3", # or "python" depending on your environment
        args=["mcp_servers/file_server.py"],
        env=os.environ.copy() # Passes your env vars (like GROQ_API_KEY) to the server if needed
    )

    # 2. Establish the connection (The Nervous System)
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            # 3. Load tools from the active session
            mcp_tools = await load_mcp_tools(session)
            
            # Combine local tools + MCP tools
            all_tools = [search_jobs, evaluate_job_fit] + mcp_tools
            llm_with_tools = llm.bind_tools(all_tools)
            
            # Compile the graph
            app = create_job_research_graph(llm_with_tools, all_tools)

            inputs = {
                "messages": [
                    SystemMessage(content=f"""You are a Personal Career Pilot.
                    Follow this protocol:
                    1. FIRST: {resume_instruction}
                       Then read these two files:
                       - './knowledge_base/DreamRoles.txt' to get the user's preferred job titles.
                       - './knowledge_base/DreamComps.txt' to get the user's preferred companies.
                    2. SECOND: Call 'search_jobs' ONCE FOR EACH role listed in DreamRoles.txt as a separate search query. For example, if DreamRoles.txt contains "Data Scientist", "ML Engineer", and "Software Developer", you must call 'search_jobs' three times with each title as the query. Collect all results into one combined list and remove any duplicate links.
                    3. THIRD: For each unique job in the combined list, use 'evaluate_job_fit' passing the resume text and the job snippet to get a fit score and identify missing skills. Prioritise jobs from companies listed in DreamComps.txt by adding +1 to their score.
                    4. FOURTH: From all evaluated jobs, keep only those scoring 6 or higher, sort them by fit score (highest first), and take the top 5. Use 'save_job_results' to save the ranked results.

                    When saving, use EXACTLY this Markdown format for the file content:

                    # GTA Job Search Report
                    Generated: {{today's date}}

                    ---

                    ## Rank {{N}}: {{Job Title}}
                    - **Company:** {{Company Name or "Not listed"}}
                    - **Link:** {{URL}}
                    - **Fit Score:** {{Score}}/10
                    - **Missing Skills:** {{comma-separated list, or "None"}}
                    - **Summary:** {{1-2 sentence description of the role}}

                    ---

                    Repeat the block above for each of the top 5 jobs, ordered from highest to lowest fit score. Save the file as 'job_report.md'.
                    If the search fails, try different keywords based on the resume."""),
                    HumanMessage(content="Find a job in the Greater Toronto Area that fits my background and save the details.")
                ]
            }

            # Run the graph while the session is active
            async for output in app.astream(inputs):
                for key, value in output.items():
                    print(f"--- Node: {key} ---")
                    if "messages" in value:
                        print(value["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(main())