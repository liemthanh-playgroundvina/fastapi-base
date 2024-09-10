# https://github.com/linexjlin/GPTs
import json
import os
from datetime import datetime

from app.core.config import settings

with open(os.path.join(settings.STATIC_URL, "files/app", "GPTs.json"), 'r') as file:
    PROMPTS = json.load(file)
    if "_list_store" in PROMPTS:
        del PROMPTS["_list_store"]


STORES = list(PROMPTS.keys())


# Base prompt
def get_system_prompt(input_pmt = None, store_name = None, chat_document_mode = False):
    first_prompt = f"""You are a Assistant chatbot.
Knowledge cutoff: 2023-10
Current date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

# System Prompt

"""
    if store_name is None:
        sys_prompt = input_pmt
    elif store_name in STORES:
        sys_prompt = PROMPTS[store_name]
    else:
        raise ValueError(f'[store_name] in messages must in {STORES}')

    # Web browser format
    web_format = """

# Tool

## URL

If in user input have [Internet_Data], please render in this format: [INFORMATION](URL).
For long citations: please render in this format: *[(HOSTNAME)](URL)*, with HOSTNAME is hostname of url.
Example of url format is: *[(Google)](https://www.google.com)*
Otherwise do not render links.
Data in [Internet_Data] is considered your knowledge, don't let users know you are using the data in it.
"""

    # Latex format
    latex_prompt = """
## Latex

Ensure LaTeX expressions in your response are properly enclosed within '$$' for block equations or '$' for inline equations.
Example:
$$
[mathematical block equations]
$$
- 1. First $[mathematical inline equations]$.
- 2. Second $[mathematical inline equations]$.
"""
    # Plot format
    plot_prompt = """
## Plot

When receiving requests related to analysis or plot/chart: Only make the plot, then give a detailed analysis of that plot.
When making plot for the user: You will generate json data format, placed in tag <PLOT></PLOT>, with the purpose of letting the user load json to create a plot with pandas.Dataframe and matplotlib.pyplot.
The format json of plot include:
- data (dict): is data of plot, it will be used to call the function 'pandas.DataFrame(data)'. Make sure the number of elements in the columns is equal.
- title (str): is title of plot, it will be used to call the function 'set_title(title)'
- xlabel (str): is x_label of plot, it will be used to call the function 'set_xlabel(title)'
- ylabel (str): is y_label of plot, it will be used to call the function 'set_ylabel(title)'

Example for plot format:
<PLOT>{
    "data": {
        "Date": ["1/6", "2/6", "3/6", "4/6", "5/6", "6/6"],
        "Gold Price": [1850, 1875, 1890, 1905, 1920, 1935]
    },
    "title": "Gold Prices Over Time from 1/6 - 6/6 (2024)",
    "xlabel": "Date",
    "xlabel": "Price (USD per ounce)"
}</PLOT>
"""
    # Chat Document Mode
    if chat_document_mode:
        doc_prompt = """
## Document

When you are provided document at <Document_Data>...<\End_Document_Data>, you will treat the information as its own and prioritize it above all else in responses.
It will never reveal or suggest that the data came from an external source or that it was provided by the user.
All answers will seamlessly integrate with the provided data as if it were your existing knowledge.
You must confidently provide responses as if it has complete understanding of the subject matter but can always ask for clarification if required.
If the answer lies outside the provided data and you doesn't know it, you will state that it does not know, ensuring that its answers are at least 90% accurate.
"""
    else:
        doc_prompt = ""

    return first_prompt + sys_prompt + web_format + latex_prompt + plot_prompt + doc_prompt


# Web search prompt
def check_web_browser_prompt():
    # System prompt
    system_prompt = f"""You are a helpful assistant chatbot.
Knowledge cutoff: 10/2023
Current date: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")} with (dd/mm/yyyy h:m:s) format"""
    system_prompt += """

# System Prompt

You are a checker query for Web Browser tool from user query input. Web browser mode will enable in the following circumstances:
- User is asking about current events or something that requires real-time information (weather, sports scores, etc.)
- User is asking about some term you are totally unfamiliar with (it might be new)
- User explicitly asks you to browse or provide links to references

The format json output include:
- web_browser_mode (bool): true when web browser mode enable
- request (dict): is {} when web_browser_mode is false. When web_browser_mode is true, it's required:
    + language (str): is language of user query input. It uses language codes according to the ISO 639-1 standard.
    + query (str): is user query input. Query must optimized can be search Google Search. Time cannot appear in the query. 
    + time (str): is the time mentioned in the query input starting from the current time with dd/mm/yyyy format (day and month can null). Time is '' if user query input does not mention time.
    + num_link (int): The number of reference links requested by the user, default is 3.

Note: Keep language text of user query input. 

Example for format GPT outputs:
{
    "web_browser_mode": true,
    "request": {
        "language": "en"
        "query": "Event",
        "time": "20/10/2020",
        "num_link": 3
    } 
}
"""
    return system_prompt

def user_prompt_checked_web_browser(user_query: str, urls: list, texts: list):
    # User prompt when have data browser
    user_prompt = """Using data was searched on the internet to answer of user query:
<Internet_Data>
"""
    for i in range(0, len(urls)):
        try:
            user_prompt += f"""- URL_{str(i + 1)}: {urls[i]}\n{texts[i].strip()}\n"""
        except:
            pass

    user_prompt += f"""<\End_Internet_Data>

User query input: {user_query}  
"""

    return user_prompt


# Chat Document Prompt For Long Context
def user_prompt_add_document_lc(user_query: str, document: str):
    user_prompt = f"""Document data provided:

<Document_Data>
{document}
<\End_Document_Data>


Please answer user query input question: {user_query}

"""

    return user_prompt
