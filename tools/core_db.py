from tools.tooling import tool
from tools.tooling import Tool
from dotenv import load_dotenv
from google import genai
from google.genai import types
import sqlite3
load_dotenv()  

# Helper function 
def query_db(sql_query):
    try:
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        return f"Error: {e}"


@tool 
def query_db(user_query):
    """
    Tool for querying basic static info: calendar, faculty, alerts, departments, and programs.
    Tool outputs data pertaining to one of the 5 categories listed above matching a users specified query. 
    """
    # Connecting to local DB
    conn = sqlite3.connect("testudo_data.db")
    cursor = conn.cursor()
    client = genai.Client()
    
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        config=types.GenerateContentConfig(
            system_instruction="""
                You are a helpful AI assistant that will generate a SQL query
                to query a local database, containing core information about
                the University of Maryland. The database has calendar, faculty,
                alerts, departments, and programs tables. 
                
                calendar has field term, which stores either Fall Semester | 2025, 
                Winter Term | 2025-26 Spring Semester | 2026, or Summer Term | 2026, 
                an events field which stores popular events like Labor Day, Spring Break,
                Last Day of Classes, and Dr. Martin Luther King Holiday, and the date of 
                each event, in the format September 1 (Monday), or for multiple days, 
                March 15-22 (Sunday-Sunday). 
    
                faculty stores a list of faculty at UMD, with field name describing their
                name in format <lastname>, <firstname>, for example: Adler, Eric. another
                field is title_department which has their title, like Professor or 
                Principal Lecturer or Adjunct Associate Professor, followed by a comma, 
                then their department. And the last field is degrees. 
    
                the departments table contains a name field, with the name of the major, and
                a url field, containing the url to go to that majors home page.
    
                the programs field contains majors and programs at UMD. it has a name field,
                url field, type field, and description field.
    
                the alerts table contains a title field, a link field, a summary field,
                and a date field in the format YYYY-MM-DD HH:MM:SS.microseconds, for example:
                2025-11-05 17:50:28.000000. 
    
                That is a description of the five tables, your job is to return an SQL query to get
                one or several rows for a certain table or tables based on the users query. You should
                try to best interpret the users need, and make sure you are returning a valid sql query
                based on fields and tables in the database. 
    
                Be sure to ONLY return the SQL query in one line, and only return one SQL row unless
                the user asks for several.
    
                Do NOT wrap the query in ```sql ```, just return the raw query.
            """
        ),
        contents=user_query
    )
    
    # print(response.text) Uncomment to show actual SQL query
    
    results = query_db(response.text)
    print(results)

TOOL_SPEC = query_db.tool_spec() 