from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Job Offers")

API_BASE = "https://api.varbi.com/v1"
USER_AGENT = "mcp-varbi-poc/1.0"

async def make_api_call(resource: str) -> dict[str, Any] | None:
    uri = f"{API_BASE}{resource}"

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Accept-Language": "en, *;q=0.5"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(uri, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None


@mcp.resource("resource://jobs/categories", name="Categories", description="A list of labels used to categorize published job offers.")
async def job_categories() -> str:
    """All available job categories."""
    resource = "/jobs/taxonomies/occupation-field"
    response = await make_api_call(resource)

    if not response or "data" not in response:
        return "Unable to fetch job categories."

    categories = [f"ID: {category['id']}\nName: {category['attributes']['name']}" for category in response["data"]]
    return "Here is a list of all available categories when searching for published jobs:\n\n" + "\n---\n".join(categories)

@mcp.tool()
async def get_jobs_by_category(category_id: str, limit: int) -> str:
    """Find jobs matching a given category.

    Args:
        category_id: ID for a job category.
        limit: The maximum number of jobs to return.
    """
    resource = f"/jobs?filter%5Btaxonomy%5D={category_id}&limit={limit}"
    response = await make_api_call(resource)

    if not response or "data" not in response:
        return "Unable to fetch jobs, or no jobs were found."

    jobs = [format_job_details(job) for job in response["data"]]
    return "\n---\n".join(jobs)

def format_job_details(job: dict) -> str:
    return f"""
ID: {job["id"]}
Title: {job["attributes"]["translations"]["texts"]["title"]}
Deadline: {job["attributes"]["dates"]["deadline"]}
Link to application form: {job["links"].get("apply", None)}
"""

@mcp.tool()
async def get_job_description(job_id: int) -> str:
    """Retrieves the description of a job, in HTML.

    Args:
        job_id: ID for a job.
    """
    resource = f"/jobs/{job_id}/ad"
    response = await make_api_call(resource)

    if not response or "data" not in response:
        return "Unable to fetch job description."

    return response["data"]["attributes"]["texts"]["descriptions"]["combined"]

if __name__ == "__main__":
    mcp.run(transport='stdio')