import pymupdf
from fastmcp import FastMCP
import os

# Initialize the server
mcp = FastMCP("Career-File-Manager")

@mcp.tool()
def read_local_file(filepath: str) -> str:
    """
    Reads a local file. Supports .pdf, .md, and .txt.
    Use this to get context from a user's resume or notes.
    """
    if not os.path.exists(filepath):
        return f"❌ Error: File not found at {filepath}"

    ext = os.path.splitext(filepath)[1].lower()

    try:
        if ext == ".pdf":
            text = []
            with pymupdf.open(filepath) as doc:
                for page in doc:
                    text.append(page.get_text())
            return "\n".join(text)
        else:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        return f"❌ Error reading {ext} file: {str(e)}"

@mcp.tool()
def save_job_results(filename: str, content: str) -> str:
    """
    Saves job search results or career drafts to a local file.
    Use this when you have found jobs and want to keep a record for the user.
    """
    # Ensure the 'output' directory exists
    output_dir = "./output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    file_path = os.path.join(output_dir, filename)
    
    try:
        with open(file_path, "w") as f:
            f.write(content)
        return f"✅ Successfully saved to {file_path}"
    except Exception as e:
        return f"❌ Failed to save file: {str(e)}"

if __name__ == "__main__":
    mcp.run()