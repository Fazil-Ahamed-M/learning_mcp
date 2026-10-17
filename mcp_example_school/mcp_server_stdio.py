import json

from mcp.server.fastmcp import FastMCP

from db import get_connection

# Create an MCP server that talks over stdin/stdout.
# The client starts this script itself, so you never run it by hand.
mcp = FastMCP(name="school-stdio")


@mcp.tool()
def query_database(query: str) -> str:
    """Run a read-only SQL SELECT query on the MySQL `school` database and return the rows as JSON.

    Use this for questions the other tools can't answer, such as rankings, averages,
    comparisons, or searching students by name, age or parent occupation.
    Only SELECT queries are allowed.

    Schema:

    Table personal_data (one row per student)
        sl_no              INT, primary key
        student_name       VARCHAR(100), e.g. 'Aarav Sharma'
        student_dob        DATE, e.g. '2009-04-17'
        mother_name        VARCHAR(100)
        mother_occupation  VARCHAR(100), e.g. 'Teacher', 'Doctor'
        father_name        VARCHAR(100)
        father_occupation  VARCHAR(100)

    Table academic_data (one row per student, marks are integers from 0 to 100)
        sl_no                     INT, primary key, references personal_data.sl_no
        marks_english             INT
        marks_science             INT
        marks_business_education  INT
        marks_finance             INT

    Join the two tables on sl_no, e.g.
        SELECT p.student_name, a.marks_science
        FROM personal_data p JOIN academic_data a ON p.sl_no = a.sl_no

    Args:
        query: A single MySQL SELECT statement
    """
    if not query.strip().lower().startswith("select"):
        return json.dumps({"error": "Only SELECT queries are allowed."})

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                # A read-only transaction is a second safety net on top of the SELECT check
                cursor.execute("START TRANSACTION READ ONLY")
                cursor.execute(query)
                rows = cursor.fetchall()
                connection.rollback()
    except Exception as e:
        return json.dumps({"error": str(e)})

    return json.dumps(rows, default=str)  # default=str turns dates into strings


# Run the server
if __name__ == "__main__":
    mcp.run(transport="stdio")
