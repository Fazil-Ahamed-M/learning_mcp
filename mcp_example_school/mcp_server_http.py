from mcp.server.fastmcp import FastMCP

from db import get_connection

# Create an MCP server that listens over HTTP
mcp = FastMCP(
    name="school-http",
    host="127.0.0.1",
    port=8050,  # the client connects to http://127.0.0.1:8050/mcp
)


def fetch_one(sql: str, sl_no: int) -> dict:
    """Run a query with one sl_no parameter and return a single row."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (sl_no,))
            row = cursor.fetchone()

    if not row:
        return {"error": f"No student found with sl_no {sl_no}"}
    if "student_dob" in row:
        row["student_dob"] = str(row["student_dob"])  # dates are not JSON friendly
    return row


@mcp.tool()
def get_personal_data(sl_no: int) -> dict:
    """Get a student's personal details: name, date of birth, and parents' names and occupations.

    Args:
        sl_no: The student's serial number (1-20)
    """
    return fetch_one("SELECT * FROM personal_data WHERE sl_no = %s", sl_no)


@mcp.tool()
def get_academic_data(sl_no: int) -> dict:
    """Get a student's marks (0-100) in English, Science, Business Education and Finance, along with the student's name.

    Args:
        sl_no: The student's serial number (1-20)
    """
    sql = """
        SELECT a.sl_no, p.student_name, a.marks_english, a.marks_science,
               a.marks_business_education, a.marks_finance
        FROM academic_data a
        JOIN personal_data p ON p.sl_no = a.sl_no
        WHERE a.sl_no = %s
    """
    return fetch_one(sql, sl_no)


# Run the server
if __name__ == "__main__":
    print("Running school-http server on http://127.0.0.1:8050/mcp")
    mcp.run(transport="streamable-http")
