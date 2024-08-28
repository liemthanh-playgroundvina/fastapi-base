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


def get_system_prompt_follow_name(input_pmt, store_name):
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

    return first_prompt + sys_prompt + web_format + latex_prompt + plot_prompt
