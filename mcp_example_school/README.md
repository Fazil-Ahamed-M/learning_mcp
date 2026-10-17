# MCP Example: School Chatbot

A small, end-to-end example of the **Model Context Protocol (MCP)**.
A command-line chatbot powered by **Grok** answers questions about students in a MySQL `school` database.
It does this by calling tools exposed by **two MCP servers**: one over **HTTP** and one over **stdio**.

```
You: What marks did student 7 get?
  [tool] get_academic_data({'sl_no': 7})

Assistant: Student 7 (Arjun Gupta) marks:
- English: 56
- Science: 66
- Business Education: 55
- Finance: 94
```

## Architecture

```
                        ┌──────────────────────────┐
                        │      Grok (xAI API)      │
                        │  picks which tool to use │
                        └────────────▲─────────────┘
                                     │ chat + tool calls
                        ┌────────────┴─────────────┐
  you ─── terminal ───▶ │      mcp_client.py       │
                        │   (command-line chatbot) │
                        └──────┬────────────┬──────┘
               HTTP            │            │          stdio
   http://127.0.0.1:8050/mcp   │            │  (client starts it as a child process)
                ┌──────────────▼───┐   ┌────▼─────────────────┐
                │ mcp_server_http  │   │  mcp_server_stdio    │
                │ get_personal_data│   │  query_database      │
                │ get_academic_data│   │  (SELECT only)       │
                └────────┬─────────┘   └─────────┬────────────┘
                         └───────────┬───────────┘
                               ┌─────▼─────┐
                               │   MySQL   │
                               │  school   │
                               └───────────┘
```

**How a question is answered**

1. The client connects to both MCP servers and asks each one for its list of tools.
2. It sends your question and the tool definitions to Grok.
3. Grok decides which tool to call (if any) and with which arguments.
4. The client runs that tool on the server that owns it and sends the result back to Grok.
5. Grok turns the result into a plain-English answer.

## The tools

| Tool | Server | Transport | Input | Returns |
|------|--------|-----------|-------|---------|
| `get_personal_data` | `mcp_server_http.py` | HTTP (streamable-http) | `sl_no` | The student's row from `personal_data` |
| `get_academic_data` | `mcp_server_http.py` | HTTP (streamable-http) | `sl_no` | The student's row from `academic_data` plus `student_name` (joined on `sl_no`) |
| `query_database` | `mcp_server_stdio.py` | stdio | `query` (SQL) | Query results as JSON. Only `SELECT` is allowed. |

The docstring of `query_database` contains the full database schema, so Grok knows how to write
correct SQL for questions like *"Who has the highest marks in science?"*.

`query_database` is read-only in two ways: it rejects any query that does not start with `SELECT`,
and it runs the query inside a MySQL `READ ONLY` transaction.

## Database

`setup_db.py` creates the `school` database with two tables and fills them with 20 synthetic students.

**personal_data**

| Column | Type |
|--------|------|
| sl_no | INT, primary key |
| student_name | VARCHAR(100) |
| student_dob | DATE |
| mother_name | VARCHAR(100) |
| mother_occupation | VARCHAR(100) |
| father_name | VARCHAR(100) |
| father_occupation | VARCHAR(100) |

**academic_data** (marks are whole numbers from 0 to 100)

| Column | Type |
|--------|------|
| sl_no | INT, primary key, references `personal_data.sl_no` |
| marks_english | INT |
| marks_science | INT |
| marks_business_education | INT |
| marks_finance | INT |

## Project structure

```
mcp_example_school/
├── setup_db.py          # creates the school database and 20 synthetic students
├── db.py                # shared MySQL connection helper (reads .env)
├── mcp_server_http.py   # MCP server over HTTP: get_personal_data, get_academic_data
├── mcp_server_stdio.py  # MCP server over stdio: query_database
├── mcp_client.py        # command-line chatbot using Grok
├── requirements.txt
└── .env                 # your secrets (not committed)
```

## Setup

**Prerequisites:** Python 3.10+, a running local MySQL server, and an xAI API key.

1. Create a virtual environment and install the dependencies:

   ```bash
   cd mcp_example_school
   python3 -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Create a `.env` file in this folder:

   ```env
   grok_api_key=your-xai-api-key
   DB_HOST=127.0.0.1
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your-mysql-password
   ```

3. Create the database and sample data:

   ```bash
   python setup_db.py
   ```

   Running it again resets the tables to the same 20 students.

## Run

You need **two terminals**. The stdio server is started by the client automatically.

**Terminal 1: start the HTTP MCP server**

```bash
python mcp_server_http.py
```

It listens on `http://127.0.0.1:8050/mcp`.

**Terminal 2: start the chatbot**

```bash
python mcp_client.py
```

Commands inside the chat: `clear` resets the conversation, `exit` or `quit` ends it.

### Things to try

| Question | Tool Grok picks |
|----------|-----------------|
| What are the personal details of student 3? | `get_personal_data` |
| What marks did student 7 get? | `get_academic_data` |
| Who has the highest marks in science? | `query_database` |
| Which students have a mother who is a doctor? | `query_database` |
| What is the class average in finance? | `query_database` |

## Model

The client uses `grok-build-0.1`, the cheapest model on the xAI API at the time of writing
($1 per million input tokens, $2 per million output tokens).
xAI's API is OpenAI-compatible, so the client uses the `openai` Python package with
`base_url="https://api.x.ai/v1"`. To use a different model, change `MODEL` in `mcp_client.py`.

## Notes

- The servers use `FastMCP` from the official MCP Python SDK. `requirements.txt` pins `mcp<2`,
  because MCP SDK 2.x renamed `FastMCP` to `MCPServer`.
- Secrets live only in `.env`, which is listed in `.gitignore`.
