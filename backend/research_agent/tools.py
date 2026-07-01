"""Research Tools.

This module provides search and content processing utilities for the research agent,
using Tavily for URL discovery, fetching full webpage content, and PostgreSQL database access.
"""

import os
import httpx
import psycopg2
from langchain_core.tools import InjectedToolArg, tool
from markdownify import markdownify
from tavily import TavilyClient
from typing_extensions import Annotated, Literal
from psycopg2.extras import RealDictCursor
from huggingface_hub import InferenceClient

tavily_client = TavilyClient()


# PostgreSQL Connection Helper
def get_db_connection():
    """Create a PostgreSQL database connection."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("PG_HOST", "localhost"),
            port=int(os.getenv("PG_PORT", "5432")),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            database=os.getenv("PG_DATABASE"),
        )
        return conn
    except psycopg2.Error as e:
        raise Exception(f"Database connection failed: {str(e)}")


def fetch_webpage_content(url: str, timeout: float = 10.0) -> str:
    """Fetch and convert webpage content to markdown.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        Webpage content as markdown
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = httpx.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return markdownify(response.text)
    except Exception as e:
        return f"Error fetching content from {url}: {str(e)}"


@tool(parse_docstring=True)
def tavily_search(
    query: str,
    max_results: Annotated[int, InjectedToolArg] = 1,
    topic: Annotated[
        Literal["general", "news", "finance"], InjectedToolArg
    ] = "general",
) -> str:
    """Search the web for information on a given query.

    Uses Tavily to discover relevant URLs, then fetches and returns full webpage content as markdown.

    Args:
        query: Search query to execute
        max_results: Maximum number of results to return (default: 1)
        topic: Topic filter - 'general', 'news', or 'finance' (default: 'general')

    Returns:
        Formatted search results with full webpage content
    """
    # Use Tavily to discover URLs
    search_results = tavily_client.search(
        query,
        max_results=max_results,
        topic=topic,
    )

    # Fetch full content for each URL
    result_texts = []
    for result in search_results.get("results", []):
        url = result["url"]
        title = result["title"]

        # Fetch webpage content
        content = fetch_webpage_content(url)

        result_text = f"""## {title}
**URL:** {url}

{content}

---
"""
        result_texts.append(result_text)

    # Format final response
    response = f"""🔍 Found {len(result_texts)} result(s) for '{query}':

{chr(10).join(result_texts)}"""

    return response


@tool(parse_docstring=True)
def think_tool(reflection: str) -> str:
    """Tool for strategic reflection on research progress and decision-making.

    Use this tool after each search to analyze results and plan next steps systematically.
    This creates a deliberate pause in the research workflow for quality decision-making.

    When to use:
    - After receiving search results: What key information did I find?
    - Before deciding next steps: Do I have enough to answer comprehensively?
    - When assessing research gaps: What specific information am I still missing?
    - Before concluding research: Can I provide a complete answer now?

    Reflection should address:
    1. Analysis of current findings - What concrete information have I gathered?
    2. Gap assessment - What crucial information is still missing?
    3. Quality evaluation - Do I have sufficient evidence/examples for a good answer?
    4. Strategic decision - Should I continue searching or provide my answer?

    Args:
        reflection: Your detailed reflection on research progress, findings, gaps, and next steps

    Returns:
        Confirmation that reflection was recorded for decision-making
    """
    return f"Reflection recorded: {reflection}"


@tool(parse_docstring=True)
def generate_image(
    prompt: str,
    model: Annotated[str, InjectedToolArg] = "black-forest-labs/FLUX.1-schnell",
) -> str:
    """
    Generate an image from a text prompt using a Hugging Face diffusion model.

    Args:
        prompt: Description of the desired image.
        model: Hugging Face model identifier (default: FLUX.1-schnell).

    Returns:
        The file path of the saved image.
    """
    token = os.getenv("HF_TOKEN")
    if not token:
        return "❌ HF_TOKEN environment variable not set."

    client = InferenceClient(model=model, token=token)
    image = client.text_to_image(prompt)

    output_dir = "generated_images"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{output_dir}/{prompt[:50].replace(' ', '_')}.png"
    image.save(filename, format="PNG")
    return f"✅ Image saved to: {filename}"


def get_database_schema() -> str:
    """Get the PostgreSQL database schema (tables and columns).

    This tool inspects your PostgreSQL database and returns information about all tables,
    their columns, data types, and key constraints. Use this before querying to understand
    the database structure.

    Returns:
        Formatted schema information showing tables and their structure
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()

        schema_info = "📊 **Database Schema:**\n\n"

        for (table_name,) in tables:
            schema_info += f"### Table: `{table_name}`\n"

            # Get columns for this table
            cursor.execute(
                f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """,
                (table_name,),
            )

            columns = cursor.fetchall()
            schema_info += "| Column | Type | Nullable | Default |\n"
            schema_info += "|--------|------|----------|----------|\n"

            for col_name, col_type, nullable, default in columns:
                nullable_str = "Yes" if nullable == "YES" else "No"
                default_str = default if default else "None"
                schema_info += (
                    f"| `{col_name}` | {col_type} | {nullable_str} | {default_str} |\n"
                )

            schema_info += "\n"

        cursor.close()
        conn.close()
        return schema_info

    except Exception as e:
        return f"❌ Error reading database schema: {str(e)}"


@tool(parse_docstring=True)
def execute_database_query(
    query: str, limit: Annotated[int, InjectedToolArg] = 10
) -> str:
    """Execute a SELECT query on the PostgreSQL database and return results.

    IMPORTANT: Only SELECT queries are allowed for safety. The query will be limited to
    the specified number of rows (default: 10). Use this to retrieve data about what needs
    to be updated and where.

    Args:
        query: SQL SELECT query to execute (e.g., SELECT * FROM users WHERE status = 'inactive')
        limit: Maximum number of rows to return (default: 10)

    Returns:
        Query results formatted as a table with row information
    """
    try:
        # Safety check - only allow SELECT queries
        if not query.strip().upper().startswith("SELECT"):
            return "❌ Error: Only SELECT queries are allowed. Use get_database_schema() to explore the database first."

        # Add LIMIT to query if not present
        if "LIMIT" not in query.upper():
            query += f" LIMIT {limit}"

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query)
        results = cursor.fetchall()

        if not results:
            cursor.close()
            conn.close()
            return "✅ Query executed successfully but returned no results."

        # Format results as table
        output = f"📋 **Query Results** ({len(results)} rows):\n\n"
        output += "| " + " | ".join(results[0].keys()) + " |\n"
        output += "|" + "|".join(["---"] * len(results[0])) + "|\n"

        for row in results:
            output += "| " + " | ".join(str(v) for v in row.values()) + " |\n"

        cursor.close()
        conn.close()
        return output

    except Exception as e:
        return f"❌ Error executing query: {str(e)}"


@tool(parse_docstring=True)
def analyze_data_for_updates(table_name: str, condition: str) -> str:
    """Analyze data to determine what records need to be updated and provide detailed recommendations.

    This tool helps you understand which records match specific criteria and provides
    detailed information about what needs to be updated, without making any changes.
    Use this to generate recommendations for the user.

    Args:
        table_name: Name of the table to analyze (e.g., 'customers', 'orders')
        condition: WHERE clause condition (e.g., 'status = inactive' OR 'last_order_date < 2024-01-01')

    Returns:
        Detailed analysis showing affected records and recommended updates
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get count of affected records
        count_query = f"SELECT COUNT(*) as count FROM {table_name} WHERE {condition}"
        cursor.execute(count_query)
        count_result = cursor.fetchone()
        affected_count = count_result["count"]

        # Get sample records
        sample_query = f"SELECT * FROM {table_name} WHERE {condition} LIMIT 5"
        cursor.execute(sample_query)
        sample_records = cursor.fetchall()

        output = f"🔍 **Analysis Report for `{table_name}`**\n\n"
        output += f"**Total affected records:** {affected_count}\n\n"
        output += f"**Sample records (showing up to 5):**\n\n"

        if sample_records:
            output += "| " + " | ".join(sample_records[0].keys()) + " |\n"
            output += "|" + "|".join(["---"] * len(sample_records[0])) + "|\n"
            for record in sample_records:
                output += "| " + " | ".join(str(v) for v in record.values()) + " |\n"
        else:
            output += "No records found matching this condition.\n"

        cursor.close()
        conn.close()
        return output

    except Exception as e:
        return f"❌ Error analyzing data: {str(e)}"


@tool(parse_docstring=True)
def generate_chart(chart_type: str, title: str, labels: list, datasets: list) -> dict:
    """Generate a chart for the user interface from structured data.

    Use this tool whenever the user asks for a graph, chart, profit visualization,
    comparison chart, trend analysis, or any visual data representation.

    Args:
        chart_type: Type of chart - must be 'bar', 'line', or 'pie'
        title: Descriptive title for the chart
        labels: List of category labels (e.g. ["Jan", "Feb", "Mar"] or ["Product A", "Product B"])
        datasets: List of dataset objects, each with 'label' (str), 'data' (list of numbers) and optional 'color' (hex string like "#2F6868")

    Returns:
        Structured chart data dict rendered as an interactive chart in the UI
    """
    return {
        "type": chart_type,
        "title": title,
        "labels": labels,
        "datasets": datasets,
    }
