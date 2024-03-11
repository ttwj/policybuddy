print("Please wait... Importing Libraries...")
from rich.console import Console
from rich.prompt import Prompt
from rich.text import Text
import json
import logging
import os
import re
import requests
from rich.console import Console
from rich.progress import Progress
from rich.prompt import Prompt
from rich.text import Text
import logging
import re
import fitz  # PyMuPDF
from langchain_community.document_loaders import DirectoryLoader

print("[Done] Importing Libraries")

from openai import OpenAI
# Initialize the console for rich output
console = Console()

regex_patterns = {
    "emails": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "websites": r"\b(https?://|www\.)[^\s()<>]+(?:\([\w\d]+\)|([^[:punct:]\s]|/))",
    "ISBNs": r"ISBN(?:-1[03])?:?\s*(97[89][-–\s]?\d{1,5}[-–\s]?\d{1,7}[-–\s]?\d{1,7}[-–\s]?\d{1,7}[-–\s]?\d)",
    "copyrights": r"\bCopyright\s(?:©)?\s*(\d{4})\s*(.*?)(?=\.|\n)",
    "publishers": r"(?:Published|Publisher|Printed)\s*by\s*([^\n\r.]+)",
    "phone_numbers": r"\b(?:\+?(\d{1,3}))?[-.\s]?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})\b",
    "citations": r"(Referencing\s+this\s+report|Citing\s+this\s+document|How\s+to\s+cite\s+this\s+report|Citation\s+information)[:\s]*([^\n]+)"
}


def generate_markdown_from_enhanced_reports_json(enhanced_reports_arr, research_plan):

    markdown_str = ""

    previous_section_content = "N/A"

    count = 0
    total = len(enhanced_reports_arr)
    for enhanced_report in enhanced_reports_arr:
        count += 1
        with open('prompts/generate_markdown_from_report_json.txt', 'r') as file:
                generate_report_prompt_contents = file.read()

        with console.status(f"[bold green]Please wait... Generating Markdown [{count} / {total}]", spinner="dots"): 

                messages = [
                    {
                        "role": "system",
                        "content": f"{generate_report_prompt_contents}\n\n== Research Plan == ```{research_plan}```"
                    },
                    {
                        "role": "user",
                        "content": f"```{json.dumps(enhanced_report)}```\n\n[Previous Section]: ```{previous_section_content}```\n\n[Markdown with Citations]:"
                    }
                ]

                response = openai_client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=messages,
                    temperature=0.1,
                    presence_penalty=1,
                    max_tokens=4000
                )
                output = response.choices[0].message.content
                print(output)



                markdown_str += output 
                markdown_str += "\n\n\n"
        
    return markdown_str
        

def generate_preliminary_report_from_perplexity(research_plan, perplexity_search_results):
    print(research_plan)
    print(perplexity_search_results)
    total_report_arr = []
    section_count = 0
    previous_section_content = "N/A"
    while section_count < 10:
        section_count += 1
        with console.status(f"[bold green]Please wait... Generating Initial Report... [Section {section_count}]", spinner="dots"): 
            try:
                with open('prompts/generate_report_from_search_results.txt', 'r') as file:
                    generate_report_prompt_contents = file.read()

                messages = [
                    {
                        "role": "system",
                        "content": f"{generate_report_prompt_contents}\n\n== Research Plan == ```{research_plan}```\n\nIMPORTANT: Focus on generating ONE section only. If no section left to generate, RETURN EMPTY JSON!"
                    },
                    {
                        "role": "user",
                        "content": f"```{json.dumps(perplexity_search_results)}```\n\n[Previous Section]: ```{previous_section_content}```\n\n[Section by Section Output]: Section {section_count}"
                    }
                ]

                response = openai_client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=messages,
                    temperature=0.1,
                    presence_penalty=1,
                    max_tokens=4000
                )
                output = response.choices[0].message.content
                print(output)

                preliminary_report_json = json_from_s(output)

                if (len(preliminary_report_json) == 0) or "report_content" not in output:
                    console.print("We have reached the end of the report")
                    return total_report_arr
                else:
                    previous_section_content = output
                    total_report_arr.append(preliminary_report_json)
        
            except Exception as e:
                logging.error(f"Failed to generate search queries: {str(e)}")
    
    return total_report_arr
            

def perform_pdf_search_and_metadata(query):
    """
    Performs a search for PDFs related to the query using the Serper search engine
    and extracts metadata for each PDF found.
    """


    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json',
    }
    data = json.dumps({
        'q': f'{query} filetype:pdf'
    })
    response = requests.post('https://google.serper.dev/search', headers=headers, data=data)
    if response.status_code == 200:
        search_results = response.json()
        return search_results.get('organic', [])
    else:
        console.print(f"Failed to perform PDF search for query '{query}': HTTP {response.status_code}", style="bold red")
        return []



def download_pdf(url, destination_folder):
    """
    Downloads a PDF from a given URL to a specified destination folder with a progress bar and returns the local file path.
    """
    console = Console()
    try:
        # Send a GET request with stream=True to download the content in chunks
        with requests.get(url, stream=True) as response:
            if response.status_code == 200:
                # Total size in bytes, obtained from the Content-Length header
                total_size_in_bytes = int(response.headers.get('content-length', 0))
                
                file_name = url.split('/')[-1]
                file_path = os.path.join(destination_folder, file_name)
                
                with open(file_path, 'wb') as pdf_file, Progress() as progress:
                    # Add a download task with the total size
                    task = progress.add_task("[green]Downloading PDF...", total=total_size_in_bytes)
                    
                    # Download the content in chunks
                    for chunk in response.iter_content(chunk_size=1024):
                        # Write chunk to file
                        pdf_file.write(chunk)
                        # Update the progress bar
                        progress.update(task, advance=len(chunk))
                
                console.print(f"PDF downloaded successfully: {file_path}", style="bold green")
                return file_path
            else:
                console.print(f"Failed to download PDF from '{url}': HTTP {response.status_code}", style="bold red")
                return None
    except Exception as e:
        console.print(f"Error downloading PDF from '{url}': {str(e)}", style="bold red")
        return None
    
def execute_google_pdf_search_queries_dict(pdf_search_queries_dict):
    """
    For each query, performs a PDF search, downloads the PDFs, and updates the query with the PDF search results and metadata.
    """
    # Get the current date and time in a human-readable format suitable for filenames
    datetime_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    destination_folder = 'downloaded_pdfs_' + datetime_str

    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    
    console.print(pdf_search_queries_dict)

    list_of_dictionaries = list(find_dicts_with_key(pdf_search_queries_dict, "query"))

    count = 0
    total_count = len(list_of_dictionaries)

    for pdf_search_dict in list_of_dictionaries:
        count += 1
        query = pdf_search_dict['query']
        console.print(f"[bold green]Executing search query: ```{query}``` [{count} / {total_count}]")
            
        pdf_search_dict['results'] = []
        pdf_search_results = perform_pdf_search_and_metadata(query)

        console.print(pdf_search_results)
        
        for result in pdf_search_results:
            pdf_downloaded = {
                'title': result['title'],
                'link': result['link'],
                'snippet': result['snippet'],
                'downloaded_file': None
            }
            if result['link'].endswith('.pdf'):
                downloaded_pdf_path = download_pdf(result['link'], destination_folder)
                if downloaded_pdf_path:
                    pdf_downloaded['downloaded_file'] = downloaded_pdf_path
                    pdf_search_dict['results'].append(pdf_downloaded)
            else:
                console.print(f"Warning: {result['title']} - {result['link']} is not a PDF.. Skipping")
        
    # Save metadata to a JSON file
    with open('metadata_of_pdfs_downloaded.json', 'w') as f:
        json.dump(list_of_dictionaries, f, indent=2)

    return list_of_dictionaries, destination_folder


def get_parent_dict_for_key(data, key='query', parent=None):
    """
    Recursively search for dictionaries that are parents of a specific key in the data.
    :param data: The data loaded as a Python object, can be a list or dictionary.
    :param key: The key we are looking for; defaults to 'query'.
    :param parent: The parent dictionary of the current data being processed.
    :return: Yields parent dictionaries of the specified key.
    """
    if isinstance(data, dict):
        for k, v in data.items():
            if k == key:
                yield parent  # Yield the parent dictionary if the key is found
            else:
                yield from get_parent_dict_for_key(v, key, data)  # Pass current dict as parent for next call
    elif isinstance(data, list):
        for item in data:
            yield from get_parent_dict_for_key(item, key, parent)  # Keep the same parent for list items



def find_nested_dicts_with_keys(data, key='more_facts_and_figures_required'):
    """
    Recursively search for dictionaries containing a specific key in the JSON data.
    :param data: The JSON data loaded as a Python object.
    :param key: The key we are looking for; defaults to 'more_facts_and_figures_required'.
    :return: Yields dictionaries containing the specified key.
    """
    if isinstance(data, dict):
        if key in data:
            yield data  # Yield the whole dictionary if the key is found
        else:
            for v in data.values():
                yield from find_nested_dicts_with_keys(v, key)
    elif isinstance(data, list):
        for item in data:
            yield from find_nested_dicts_with_keys(item, key)


def find_dicts_with_key(data, key='qn_with_sources'):
    """
    Recursively search for dictionaries containing a specific key in the YAML data.
    :param data: The YAML data loaded as a Python object.
    :param key: The key we are looking for; defaults to 'qn_with_sources'.
    :return: Yields dictionaries containing the specified key.
    """
    if isinstance(data, dict):
        if key in data:
            yield data  # Yield the whole dictionary if the key is found
        else:
            for v in data.values():
                yield from find_dicts_with_key(v, key)
    elif isinstance(data, list):
        for item in data:
            yield from find_dicts_with_key(item, key)


def json_from_s(s):
    match = re.findall(r'({[\s\S]+}|\[[\s\S]+\])', s)
    logging.info(f"Attempting to extract JSON, regex match {match}")
    return json.loads(match[0]) if match else None


report_guiding_questions = '''
For each section and bullet point within the output, identify specific areas of research or questions that need to be addressed. Alongside each question or research area, provide guidance on the type of sources that should be consulted to obtain reliable and authoritative information.

- **For statistical data or current status updates**: "What are the latest statistics on XXX?" (Research should be conducted using news articles from reputable outlets and recent publications from relevant industry bodies.)
  
- **For policy and regulatory insights**: "Which governments have implemented policies related to XXX?" (Focus should be on official government sources, legislative documents, and policy briefs to ensure accuracy and up-to-date information.)
  
- **For financial metrics or risk assessments**: "What is the Weighted Average Cost of Capital (WACC) or political risk rating for projects related to XXX in YYY region?" (Multilateral and research sources such as the IMF, World Bank, and Asian Development Bank (ADB) should be consulted for robust financial data and risk assessments.)

- **For technology and innovation trends**: "What are the emerging technologies in the XXX sector?" (Academic journals, patents, and whitepapers from research institutions and leading technology companies should be the primary sources for cutting-edge innovation insights.)

- **For environmental impact and sustainability analysis**: "What are the environmental impacts associated with XXX technology or practice?" (Refer to environmental impact assessments, sustainability reports from international environmental organizations, and peer-reviewed environmental studies.)

- **For case studies and best practices**: "What are some successful case studies where XXX technology has been implemented?" (Industry reports, academic case studies, and success stories published by organizations involved in similar projects should be explored for practical insights and lessons learned.)

[Example]
### Section 1:
- Detailed Pointer 1: <20-30 words: what is the goal of this section?..>
- Detailed Pointer 2: <20-30 words: what is the goal of this section?..>
...
...
    - Primary Areas of Research to Explore: <...Sources to Research on....>
        - Potential Search Queries: What is XXX, Which XXX, What are..?, ..., ... //At least 5 search queries
    - Secondary Areas of Research to Explore: <...Sources to Research on....>
        - Potential Search Queries: What is XXX, Which XXX, What are..?, ..., ... //At least 5 queries


### Section 2:
- Detailed Pointer 1: <20-30 words: what is the goal of this section?..>
- Detailed Pointer 2: <20-30 words: what is the goal of this section?..>
...
...
    - Primary Areas of Research to Explore: <...Sources to Research on....>
        - Potential Search Queries: What is XXX, Which XXX, What are..?, ..., ... // > 5 queries
    - Secondary Areas of Research to Explore: <...Sources to Research on....>
        - Potential Search Queries: What is XXX, Which XXX, What are..?, ..., // > 5 queries
...

By following these refined instructions, each section of the ouput will draw from a diverse and authoritative set of sources, ensuring a well-rounded and credible analysis. This methodical approach will enhance the robustness of the report's findings and recommendations, making it a valuable resource for stakeholders.

Important: Remember to take inspiration from sources requested by user
'''


# Initialize OpenAI and Perplexity clients
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'default_openai_api_key')
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY', 'default_perplexity_api_key')
SERPER_API_KEY = os.getenv('SERPER_API_KEY', 'default_serper_api_key')


openai_client = OpenAI(api_key=OPENAI_API_KEY)
perplexity_client = OpenAI(api_key=PERPLEXITY_API_KEY, base_url="https://api.perplexity.ai")

import time

def generate_system_prompt(user_context):
    with console.status("[bold green]Please wait... Generating system prompt. This will be used to ground the LLM and specific to your needs", spinner="dots"): 
        try:
            with open('prompts/generate_prompt_from_user_persona_goals.txt', 'r') as file:
                file_contents = file.read()
        except FileNotFoundError:
            console.print("[bold red]Error: The prompt generation file does not exist.")
            return None
        except Exception as e:
            console.print(f"[bold red]Error reading the prompt geneartion file: {str(e)}")
            return None
    
        # Convert the user context to a JSON string
        json_str = json.dumps(user_context)
        
        # Print and log the user context for transparency
        console.print("[bold magenta]User Context (as JSON):", style="bold blue")
        console.print(json_str, style="bold blue")

        # Send the JSON string to the LLM (OpenAI) for generating a comprehensive customized System Prompt
        try:

            
            response = openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "system", "content": file_contents},
                            {"role": "user", "content": f"```{json_str}```\n\nIMPORTANT: Tone of prompt must be policy-oriented, avoid superfluous language"}],
                temperature=0,
                top_p=0,
                max_tokens=4000,
                #stream=True
            )

            generated_prompt = response.choices[0].message.content
            
            '''# Stream the response and print using Rich Console
            for chunk in response:
                message = chunk.choices[0].delta.content
                if message is not None:
                    console.print(message, end="")
                    generated_prompt += message'''

            # Print and log the generated plan
            console.print("[bold magenta]Generated System Prompt:", style="bold green")
            console.print(generated_prompt, style="bold green")
            
            return generated_prompt
        except Exception as e:
            console.print(f"[bold red]Error generating the customized prompt: {str(e)}")
            return None




def execute_pplx_search(query):
    """
    Queries Perplexity with each search query and updates the queries with results and citations using direct API calls.
    """
    query_result_dict = {}
    headers = {
        'accept': 'application/json',
        'authorization': f'Bearer {PERPLEXITY_API_KEY}',
        'content-type': 'application/json',
    }
    url = "https://api.perplexity.ai/chat/completions"

   
    data = {
        "model": "pplx-7b-online",
        "messages": [{"role": "user", "content": query}],
        "return_citations": True
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()
        logging.info(f"Got result from Perplexity {response_data}")
        if response.status_code == 200:
            query_result = {
                "response": response_data['choices'][0]['message']['content'],
                "citations": response_data.get('citations', [])
            }
            return query_result
    except Exception as e:
        return None

def execute_perplexity_queries_and_update_dict(search_state_dict):
    search_queries = list(find_dicts_with_key(search_state_dict))
    print(search_queries)
    search_query_count = len(search_queries)
    count = 0
    for search_query_dict in search_queries:
        count += 1
        search_qn = search_query_dict['qn_with_sources']
        with console.status(f"[bold green]Please wait... Executing search '{search_qn}' [{count}/{search_query_count}]", spinner="dots"):
            perplexity_result = execute_pplx_search(search_qn)
            search_query_dict['search_results'] = perplexity_result
        
        console.print(search_query_dict)

    return search_state_dict

import yaml
def try_extract_yaml_as_dict(yaml_dirty_string):
    yaml_content_match = re.search(r"```yaml(.*?)```", yaml_dirty_string, re.DOTALL)

    if yaml_content_match:
        yaml_content = yaml_content_match.group(1).strip()  # Removes leading and trailing whitespace
        
        # Parse the YAML content
        try:
            parsed_yaml = yaml.safe_load(yaml_content)
            print(parsed_yaml)
            return parsed_yaml
        except yaml.YAMLError as exc:
            print("Error parsing YAML content:", exc)
            return None
    else:
        print("No YAML content found.")
        return None

def llm_generate_pdf_search_queries_from_report(preliminary_report):
    """
    Generates search queries based on the Perplexity Search Results
    """
    with console.status("[bold green]Please wait... Generating detailed PDF search queries to search for high quality reports...", spinner="dots"): 
     
        attempt = 0

        while attempt < 3:
            try:
                with open('prompts/generate_pdf_search_queries_from_report.txt', 'r') as file:
                    search_prompt_contents = file.read()

                response = openai_client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[{"role": "system", "content": search_prompt_contents},
                            {"role": "user", "content": f"Report:``{json.dumps(preliminary_report)}```\n\n[Detailed Search Queries JSON]```json:"}],
                    temperature=0.2,
                    top_p=1,
                    presence_penalty=2,
                    max_tokens=4000
                )
                output = response.choices[0].message.content
                console.print('[bold green]=== Proposed Search Plan ===')
                console.print(output)
                # Attempt to read the JSON as dictionary
                search_queries_dict = json_from_s(output)

                if search_queries_dict is None:
                    logging.warn("Warning: llm_generate_search_queries_from_report: Failed to get JSON from OpenAI, try again")
                    attempt += 1
                else:
                    return search_queries_dict
            
            except Exception as e:
                logging.error(f"Failed to generate search queries: {str(e)}")
                return None
        logging.warn("[llm_generate_search_queries_from_report] Attempted to call OpenAI > 3 times to generate search queries as YAML, failed")
        return None


def llm_generate_pdf_search_queries(perplexity_search_results):
    """
    Generates search queries based on the Perplexity Search Results
    """
    with console.status("[bold green]Please wait... Generating detailed PDF search queries to search for high quality reports...", spinner="dots"): 
     
        attempt = 0

        while attempt < 3:
            try:
                with open('prompts/generate_pdf_search_json_from_perplexity.txt', 'r') as file:
                    search_prompt_contents = file.read()

                response = openai_client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[{"role": "system", "content": search_prompt_contents},
                            {"role": "user", "content": f"Initial Search Results: ```{json.dumps(perplexity_search_results)}```\n\n[Detailed Search Queries JSON]```json:"}],
                    temperature=0.2,
                    top_p=1,
                    presence_penalty=2,
                    max_tokens=4000
                )
                output = response.choices[0].message.content
                console.print('[bold green]=== Proposed Search Plan ===')
                console.print(output)
                # Attempt to read the JSON as dictionary
                search_queries_dict = json_from_s(output)

                if search_queries_dict is None:
                    logging.warn("Warning: llm_generate_search_queries: Failed to get JSON from OpenAI, try again")
                    attempt += 1
                else:
                    return search_queries_dict
            
            except Exception as e:
                logging.error(f"Failed to generate search queries: {str(e)}")
                return None
        logging.warn("[llm_generate_search_queries] Attempted to call OpenAI > 3 times to generate search queries as YAML, failed")
        return None


def llm_generate_search_queries(research_plan):
    """
    Generates initial search queries based on the research area.
    """
    with console.status("[bold green]Please wait... Generating detailed search queries...", spinner="dots"): 
     
        attempt = 0

        while attempt < 3:
            try:
                with open('prompts/generate_search_json_from_research_plan.txt', 'r') as file:
                    search_prompt_contents = file.read()

                response = openai_client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[{"role": "system", "content": search_prompt_contents},
                            {"role": "user", "content": f"Plan: ```{research_plan}```\n\n[JSON Format]```json:"}],
                    temperature=0,
                    presence_penalty=2,
                    max_tokens=4000
                )
                output = response.choices[0].message.content
                console.print('[bold green]=== Proposed Search Plan ===')
                console.print(output)
                # Attempt to read the YAML as dictionary
                search_queries_dict = json_from_s(output)

                if search_queries_dict is None:
                    logging.warn("Warning: llm_generate_search_queries: Failed to get JSON from OpenAI, try again")
                    attempt += 1
                else:
                    return search_queries_dict
            
            except Exception as e:
                logging.error(f"Failed to generate search queries: {str(e)}")
                return None
        logging.warn("[llm_generate_search_queries] Attempted to call OpenAI > 3 times to generate search queries as YAML, failed")
        return None

def refine_research_plan_with_user_feedback(system_prompt, initial_plan):
    #with console.status("[bold green]Please wait... refining research plan", spinner="dots"):
    #    time.sleep(3)

    console.print("\nInitial Research Plan:", style="bold green")
    console.print(initial_plan, style="yellow")
    
    updated_plan = initial_plan

    satisfied = False
    while not satisfied:
        feedback = Prompt.ask(Text("Provide feedback or type 'done' if you are satisfied. Example feedback: 'Add more details on renewable energy subsidies in the methodology section.'", style="bold magenta"))
        
        if feedback.lower() == 'done' or len(feedback.lower()) < 2:
            satisfied = True
            return updated_plan
        else:
            updated_plan = llm_refine_research_plan(system_prompt, initial_plan, feedback)
    
    return updated_plan

def llm_refine_research_plan(system_prompt, original_plan, original_plan_feedback):
    """
    Continues to refine outline & plan given the output type (e.g: Policy Memo)
    """

    output = ""
   
    console.print("[bold green] ======= Generating Refined Research Plan..... ======")
    #with console.status("[bold green]Please wait... Generating Research Plan... This will be used to guide the LLM on what search queries it should execute later", spinner="dots"):
   
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "system", "content": system_prompt + "\n\n " + report_guiding_questions + "\n\nYou will be provided [ORIGINAL PLAN] and [FEEDBACK]. Your task to take in [ORIGINAL PLAN] and enhance it with [FEEDBACK] to generate [UPDATED PLAN]. Remember to preserve essential elements of [ORIGINAL PLAN]"},
                    {"role": "user", "content": f"[ORIGINAL PLAN]```{original_plan}```\n\n[FEEDBACK]```{original_plan_feedback}```\n\n[UPDATED PLAN]:"}],
            temperature=0.8,
            top_p=1,
            presence_penalty=0,
            max_tokens=4000,
            stream=True
        )
        
         # Stream the response and print using Rich Console
        for chunk in response:
            try:
                message = chunk.choices[0].delta.content
                if message is not None:
                    console.print(message, end="")
                    output += message
            except Exception as e:
                # Sometimes chunk have issues
                pass

        return output
    
    except Exception as e:
        console.print(f"[bold red]Error generating refined research plan: {str(e)}")
    



def llm_generate_research_plan(system_prompt, output_type, research_inspiration):
    """
    Generates detailed outline & plan given the output type (e.g: Policy Memo)
    """
   
    #with console.status("[bold green]Please wait... Generating Research Plan... This will be used to guide the LLM on what search queries it should execute later", spinner="dots"):
    output = ""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "system", "content": system_prompt + "\n\n " + report_guiding_questions + "\n\nYour task is to come up with a detailed outline of report, potential bullet points and areas of research"},
                    {"role": "user", "content": "Outline and Detailed Research Plan for " + output_type + "\n\n IMPORTANT: DO NOT BE COMPLACENT & DO NOT MAKE ANY RECOMMENDATIONS as this is just beginning of research. Be open minded & generate as many research points as possible.\n\nRemember to take inspiration from following sources requested by user: " + research_inspiration + "\n\n: Minimum 5 search queries per section in plan"}],
            temperature=0.5,
            top_p=0.5,
            presence_penalty=0.25,
            max_tokens=4000,
            stream=True
        )
        console.print(f"[bold green] ==================== Research Plan ====================")
        # Stream the response and print using Rich Console
        for chunk in response:
            try:
                message = chunk.choices[0].delta.content
                if message is not None:
                    console.print(message, end="")
                    output += message
            except Exception as e:
                # Sometimes chunk have issues
                pass

        return output
    
    except Exception as e:
        console.print(f"[bold red]Error generating the research plan: {str(e)}")

def select_from_options(console, options, prompt_message, other_message, default_choice="2"):
    """
    Prompts the user to select an option from a list or specify their own.
    
    Parameters:
    - console: The Rich console object for printing.
    - options: A list of options for the user to choose from.
    - prompt_message: The message displayed to the user when asking them to choose an option.
    - other_message: The message displayed if the user selects the "Other" option, prompting them to specify.
    - default_choice: The default choice index as a string. Defaults to "2".
    
    Returns:
    - The selected option as a string. If "Other" is selected, returns the user-specified option.
    """
    
    # Display the prompt message with the default option highlighted
    default_option = options[int(default_choice)-1]
    console.print(f"\n{prompt_message} [default: {default_option}]", style="bold magenta")
    
    # Display the options
    for idx, option in enumerate(options, start=1):
        console.print(f"{idx}) {option}", style="bold yellow")
    
    # Ask the user for their choice, using the default choice if no input is provided
    choice = Prompt.ask(Text("Enter the number corresponding to your choice", style="bold magenta"), default=default_choice)
    
    # Handle the "Other" option
    if choice == str(len(options)):  # If "Other" is selected
        other_option = Prompt.ask(Text(other_message, style="bold magenta"))
        console.print(f"Using specified value: {other_option}", style="bold green")
        return other_option
    else:
        selected_option = options[int(choice) - 1]
        
        # Notify the user if the default option is being used
        if choice == default_choice:
            console.print(f"No input provided, using default value: {selected_option}", style="bold green")
        return selected_option

import datetime
import argparse

def read_json_from_file(filename):
    """Reads user context from a given JSON file."""
    try:
        with open(filename, 'r') as file:
            user_context = json.load(file)
        return user_context
    except FileNotFoundError:
        console.print(f"File {filename} not found. Please check the filename and try again.", style="bold red")
        exit(1)



# Parsing and Preprocessing Functions
def extract_text_from_pdf(pdf_path):
    logging.debug("Extracting text from PDF")
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
    return text

def preprocess_text(text):
    logging.debug("Preprocessing text")
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    text = re.sub(r'\s+', ' ', text)     # Remove extra spaces
    return text.strip()

# Sentence Tokenization and Chunking
def split_into_sentences(text):
    logging.debug(f"Splitting text into sentences: {text}")
    nlp = English()
    nlp.add_pipe("sentencizer")
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents]

def chunk_sentences(sentences, max_length=512):
    chunks = []
    current_chunk = ""
    current_length = 0

    for sentence in sentences:
        words = sentence.split()
        for word in words:
            # Add 1 for the space or special token
            word_length = len(word) + 1

            if current_length + word_length > max_length:
                # If the current chunk is full, add it to the chunks list
                chunks.append(current_chunk.strip())
                current_chunk = ""
                current_length = 0

            current_chunk += word + " "
            current_length += word_length

        # Add a space after each sentence, but keep track of the length
        current_chunk += " "
        current_length += 1

        if current_length > max_length:
            # In case the sentence itself was longer than max_length
            chunks.append(current_chunk.strip())
            current_chunk = ""
            current_length = 0

    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def perform_topic_extraction_for_pdf_info_dict(pdf_info_dict):

    pdf_file = pdf_info_dict['downloaded_file']

    logging.info(f"PDF File {pdf_file} loaded successfully")

    # Extract and preprocess text from PDF
    conversation_text = extract_text_from_pdf(pdf_file)

    pdf_text_split = conversation_text.split()

    text_for_regex = ' '.join(pdf_text_split[:2000])  # Use text from the first 2000 words for regex
    first_200_words_per_page = ' '.join(pdf_text_split[:200])  # First 200 words from the first 4 pages
        
    relevant_chunks = {}
    for key, pattern in regex_patterns.items():
        matches = find_relevant_citation_chunks_from_pdf_text(text_for_regex, pattern)
        if matches:
            relevant_chunks[key] = matches
            
    
    output = {
        "title": pdf_info_dict['title'],
        "link": pdf_info_dict['link'],
        "relevant_chunks": relevant_chunks,
        "first_200_words_per_page": first_200_words_per_page
    }

    #print(output)

    with console.status(f"[bold green]Please wait... Generating topics and citation for {output['title']} - {output['link']}", spinner="dots"): 
        try:
            with open('prompts/get_apa_citation_from_pdf.txt', 'r') as file:
                file_contents = file.read()
        except FileNotFoundError:
            console.print("[bold red]Error: The APA Citation prompt file does not exist.")
            return None
        except Exception as e:
            console.print(f"[bold red]Error reading the prompt geneartion file: {str(e)}")
            return None
    
        # Convert the file info a JSON string
        json_str = json.dumps(output)
        
        # Send the JSON string to the LLM to get APA citation
        try:
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo-16k",
                messages=[{"role": "system", "content": file_contents},
                            {"role": "user", "content": f"```{json_str}```"}],
                temperature=0,
                top_p=0,
                max_tokens=4000,
                #stream=True
            )
            file_metadata = json_from_s(response.choices[0].message.content)
            print(file_metadata)
        except Exception as e:
            console.print(f"[bold red] Warning: Could not extract citation & summary for {output['title']} - {output['link']}")
            return
    
        conversation_text = preprocess_text(conversation_text)
        # Apply sentence tokenization and chunking
        conversation_sentences = split_into_sentences(conversation_text)
        conversation_chunks = chunk_sentences(conversation_sentences)

        # No need to flatten chunks for topic modeling
        flat_chunks = conversation_chunks
        logging.info("Text data prepared for topic modeling")

        # Setting up and running BERTopic
        logging.info("Setting up BERTopic model")
        umap_model = UMAP(n_neighbors=5, n_components=5, random_state=42)
        hdbscan_model = HDBSCAN(min_cluster_size=3, metric='euclidean', cluster_selection_method='eom')
        topic_model = BERTopic(umap_model=umap_model, hdbscan_model=hdbscan_model, min_topic_size=3)

        logging.info("Running BERTopic model")
        topics, probs = topic_model.fit_transform(flat_chunks)

        # Get and save topic info
        logging.info("Saving topic information")
        topics_df = topic_model.get_topic_info()

        saved_csv_file = pdf_file + "_topics.csv"
        topics_df.to_csv(saved_csv_file, index=False)

        return file_metadata, topics_df


def extract_text_and_first_words_from_pdf(pdf_path):
    """Extracts text from the first 15 pages of a PDF file and the first 200 words from the first 4 pages."""
    doc = fitz.open(pdf_path)
    text_for_regex = ""
    first_200_words_per_page = []
    for num, page in enumerate(doc):
        page_text = page.get_text()
        if num < 15:  # Consider text from the first 15 pages for regex
            text_for_regex += page_text
        if num < 4:  # Only consider the first 4 pages for the first 200 words
            words = page_text.split()[:200]  # Get the first 200 words
            first_200_words_per_page.append(" ".join(words))
    return text_for_regex, first_200_words_per_page



def find_relevant_citation_chunks_from_pdf_text(text, regex, limit=10, context_words=50):
    """
    Finds and returns up to 'limit' chunks of text that match the given regex,
    including approximately 'context_words' words before and after the match for context.
    """
    matches = []
    for match in re.finditer(regex, text, re.IGNORECASE):
        start, end = match.span()
        # Convert the match start and end positions to word positions for context extraction
        words_before = text[:start].split()[-context_words:]
        words_after = text[end:].split()[:context_words]
        match_context = ' '.join(words_before + [match.group()] + words_after)
        matches.append(match_context)
        if len(matches) >= limit:
            break
    return matches


def process_google_pdf_search_results_json(json_file_path, research_plan_file):
    with open(json_file_path, 'r') as file:
        data = json.load(file)

    with open(research_plan_file, 'r') as file:
        research_plan_str = file.read()

    with open('prompts/generate_report_json_from_bertopic.txt', 'r') as file:
        bertopic_prompt = file.read()
    
    cleaned_prompt = "You are an expert policy analyst with a meticulous eye for detail, facts, figures and a balanced perspective on controversial issues\n\n" + \
                     "Given following research plan ```" + research_plan_str + "```\n\n" + bertopic_prompt
                     


    cleaned_reranked_topics = []
    for search_area in data:  # Directly iterate over the list from the JSON file
        for item in search_area['results']:
            print(item)
 
            file_metadata_dict, topics_csv_df = perform_topic_extraction_for_pdf_info_dict(item)
            for i, chunk in enumerate(get_df_chunks(topics_csv_df), 1): #Get chunks of 5
                # Convert the chunk to CSV string
                csv_string = chunk.to_csv(index=False, header=True)
                 
                print(f"Chunk {i}:\n{csv_string}")
                response = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo-16k",
                    messages=[{"role": "system", "content": cleaned_prompt + "\n\nFile Info: ```" + json.dumps(file_metadata_dict) + "```"},
                                {"role": "user", "content": csv_string}],
                    temperature=0,
                    top_p=1,
                    presence_penalty=1,
                    max_tokens=4000,
                    #stream=True
                )
                reranked_topics = json_from_s(response.choices[0].message.content)
                cleaned_reranked_topics.append(reranked_topics)
                with open(item['downloaded_file'] + "_reranked_topics.json", 'w') as json_file:
                    json.dump(cleaned_reranked_topics, json_file, indent=4)
                

        


# Function to yield DataFrame chunks
def get_df_chunks(dataframe, chunk_size=5):
    num_chunks = len(dataframe) // chunk_size + (1 if len(dataframe) % chunk_size else 0)
    
    for i in range(num_chunks):
        start_row = i * chunk_size
        end_row = start_row + chunk_size
        chunk = dataframe.iloc[start_row:end_row]
        yield chunk


from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_community.document_loaders import PyPDFLoader

from paperqa import LangchainVectorStore, Docs
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

def enhance_preliminary_report_with_vector_search(preliminary_report, db):
    relevant_report_sections = list(find_nested_dicts_with_keys(preliminary_report))

    final_enhanced_report_sections = []

    for report_section in relevant_report_sections:
        console.print(f"[bold green] Enhancing section '{report_section['section_name']}' with vector search...")
        for qn in report_section['more_facts_and_figures_required']:
            with console.status(f"[bold yellow]LLM enhancing report.. Thinking: '{qn}'", spinner="dots"): 
                console.print("[bold yellow] Qn: " + qn)
                docs = db.similarity_search(qn, k=2, fetch_k=5)
                citation_json = []
                for doc in docs:
                    citation_json.append({
                        "file": doc.metadata['source'],
                        #"page": doc.metadata['page'],
                        "txt": doc.page_content
                    })

                print(citation_json)  

                # Send to LLM to enhance report section

                try:
                    with open('prompts/enhance_report_from_pdf_results.txt', 'r') as file:
                        enhance_report_prompt_contents = file.read()

                    messages = [
                        {
                            "role": "system",
                            "content": enhance_report_prompt_contents
                        },
                        {
                            "role": "user",
                            "content": f"Old Report```{json.dumps(report_section)}```\n\nNew Research```{json.dumps(citation_json)}```\n\nEnhanced Single Report Section:"
                        }
                    ]

                    response = openai_client.chat.completions.create(
                        model="gpt-4-turbo-preview",
                        messages=messages,
                        temperature=0.1,
                        top_p=1,
                        presence_penalty=0.5,
                        max_tokens=4000
                    )
                    output = response.choices[0].message.content
                    print(output)
                    enhanced_report_json = json_from_s(output)

                except Exception as e:
                    console.print("[bold red] [Warning]: Failed to enhance report section")
                    print(e)

        console.print(f"[bold green] Final Enhanced Section: {enhanced_report_json}")
        final_enhanced_report_sections.append(enhanced_report_json)

    return final_enhanced_report_sections

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="PolicyBuddy Research Plan Generator")
    parser.add_argument("-f", "--file", help="JSON file containing user context", required=False)
    parser.add_argument("-s", "--search_results", help="JSON file containing search results", required=False)
    parser.add_argument("-r", "--research_plan", help="JSON file containing final research plan", required=False)
    parser.add_argument('-p', "--prompt", help=".txt file containing system prompt", required=False)

    parser.add_argument('-pr', "--preliminary_report", help="JSON Containing Preliminary Report", required=False)
    parser.add_argument('-pdfs', "--pdf_destination_folder", help="PDF Destination Folder", required=False)
    parser.add_argument('-v', "--vector_store", help="Location to the FAISS Vector Store for PDF Embeddings")
    parser.add_argument('-er', "--enhanced_report", help="Location to the Enhanced Report JSON")

    args = parser.parse_args()

    research_plan = None

    if not args.enhanced_report:
        if not args.search_results:
            if args.file:
                # Read user context from the provided file
                user_context = read_json_from_file(args.file)
            else:
                # Interactive prompts for user input
                user_context = {}
                user_context['user_job'] = Prompt.ask(Text("What is your job role? e.g: Policy Analyst / Sustainability Consultant / Due Diligence Expert", style="bold magenta"), default="Policy Analyst")
                user_context['user_workplace'] = Prompt.ask(Text("Where are you working? Be more descriptive of your organization's role, do not input organizations' name specifically for privacy purposes.", style="bold magenta"), default="A global NGO focused on environmental advocacy")
                user_context['report_audience'] = Prompt.ask(Text("Who is this report meant for?", style="bold magenta"), default="Internal stakeholders")
                user_context['report_inspiration'] = Prompt.ask(Text("What types of reports inspire you?", style="bold magenta"), default="IPCC Assessment Reports")
                user_context['sources_focus_search'] = Prompt.ask(Text("What kind of sources would you like to focus on (e.g: Multilateral Sources, Government Sources, Central Bank Reports)"), default="Multilateral Sources (IMF, ADB, World Bank, GGGI), Government Reports, Central Bank Reports")
                user_context['sources_date_focus_search'] = Prompt.ask(Text("What year / date period you want the search to be focused on (e.g: Multilateral Sources, Government Sources, Central Bank Reports)"), default="Multilateral Sources (IMF, ADB, World Bank, GGGI), Government Reports, Central Bank Reports")

                # Ask about the type of output the user is looking for
                output_types = ["Memo", "Report", "Policy Brief", "Landscape Analysis", "Research Paper", "Other"]
                user_context['desired_output_type'] = select_from_options(console, output_types, "What type of output are you looking to produce?", "Please specify your desired output type", default_choice="2")
                
                # Select Sector of Interest with guidance
                sectors = ["Carbon Markets", "Renewable Energy", "Sustainable Agriculture", "Climate Finance", "Biodiversity", "Other"]
                user_context['sector_of_interest'] = select_from_options(console, sectors, "Select your sector of interest.", "Please specify your sector of interest. Example: Ocean Conservation", default_choice="2")
                
                # Specify Topic of Interest with an example
                user_context['topic_of_interest'] = Prompt.ask(Text(f"Specify your topic of interest within {user_context['sector_of_interest']}.", style="bold magenta"), default=f"Impact of {user_context['sector_of_interest'].lower()} on local ecosystems")
                
                # Existing Knowledge and Knowledge Gaps with examples
                user_context['existing_knowledge'] = Prompt.ask(Text("What do you already know? (Less than 200 words)", style="bold magenta"), default="N/A")
                user_context['knowledge_gaps'] = Prompt.ask(Text("What would you like to know more about? (Less than 200 words)", style="bold magenta"), default="N/A")

            if args.prompt:
                try:
                    with open(args.prompt, 'r') as file:
                        system_prompt = file.read()
                except FileNotFoundError:
                    console.print(f"Prompt File {args.prompt} not found. Please check the filename and try again.", style="bold red")
                    exit(1)
            else:
                # The rest of your existing code using the user_context
                console.print(user_context)
                system_prompt = generate_system_prompt(user_context)

            if args.research_plan:   
                try:
                    with open(args.research_plan, 'r') as file:
                        research_plan = file.read()
                    
                    console.print("Loading existing research plan: " + research_plan)

                except FileNotFoundError:
                    console.print(f"Research Plan File {args.research_plan} not found. Please check the filename and try again.", style="bold red")
                    exit(1)
                
            else:
                research_plan = llm_generate_research_plan(system_prompt, user_context['desired_output_type'], user_context['report_inspiration'])

                # Refine Plan with User Feedback
                final_plan = refine_research_plan_with_user_feedback(system_prompt, research_plan)
                console.print("\nFinal Research Plan:", style="bold green")
                console.print(final_plan, style="bold yellow")

            if args.search_results:
                search_queries_dict_with_results = read_json_from_file(args.search_results)
            else:
                # Generate Search Queries Based on the Final Research Plan
                search_queries_dict = llm_generate_search_queries(final_plan)
                print(search_queries_dict)
                console.print("===== Executing Search Queries ===", style="bold green")

                search_queries_dict_with_results = execute_perplexity_queries_and_update_dict(search_queries_dict)

            # Get the current date and time in a human-readable format suitable for filenames
            datetime_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            # Create the filename using the current date and time
            filename = f'perplexity_search_queries_results_{datetime_str}.json'

            # Write the updated dictionary to the JSON file
            with open(filename, 'w') as json_file:
                json.dump(search_queries_dict_with_results, json_file, indent=4)

        else:
            console.print("[bold green] [Expert Mode] Reading existing search queries...")
            search_queries_dict_with_results = read_json_from_file(args.search_results)

        # Based on the search results, we generate a preliminary report in JSON format, we then find more targeted search queries

        if not args.preliminary_report:
            preliminary_report = generate_preliminary_report_from_perplexity(research_plan, search_queries_dict_with_results)

            with open('preliminary_report.json', 'w') as json_file:
                json.dump(preliminary_report, json_file, indent=4)

            google_pdf_search_queries = llm_generate_pdf_search_queries_from_report(preliminary_report)
            google_pdf_search_queries_with_results, pdf_destination_folder = execute_google_pdf_search_queries_dict(google_pdf_search_queries)

            # Get the current date and time in a human-readable format suitable for filenames
            datetime_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            # Create the filename using the current date and time
            filename = f'google_pdf_search_queries_results_{datetime_str}.json'

            # Write the updated dictionary to the JSON file
            with open(filename, 'w') as json_file:
                json.dump(google_pdf_search_queries_with_results, json_file, indent=4)

        else:
            with open(args.preliminary_report, 'r') as file:
                preliminary_report = json.loads(file.read())

            pdf_destination_folder = args.pdf_destination_folder

        #print(preliminary_report)

        if not args.vector_store and not args.enhanced_report:
            console.print("[bold green] Loading PDFs into OpenAI... Please wait...")
            loader = DirectoryLoader(pdf_destination_folder, show_progress=True, use_multithreading=True, silent_errors=True)

            #print(loader)

            datetime_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            pages = loader.load_and_split()

            embeddings = OpenAIEmbeddings()
            db = FAISS.from_documents(pages, embeddings)
            db.save_local(datetime_str + "_faiss")

        else:
            embeddings = OpenAIEmbeddings()
            db = FAISS.load_local(args.vector_store, embeddings, allow_dangerous_deserialization=True)


        enhanced_reports = enhance_preliminary_report_with_vector_search(preliminary_report, db)
        
        # Write the enhanced reports to the JSON file
        with open('enhanced_report_sections.json', 'w') as json_file:
            json.dump(enhanced_reports, json_file, indent=4)
            

    else:
        with open(args.enhanced_report, 'r') as file:
            enhanced_reports = json.load(file)
        
    markdown_output = generate_markdown_from_enhanced_reports_json(enhanced_reports, research_plan)
   
    # Write the enhanced reports to the JSON file
    with open('markdown_report.md', 'w') as md_file:
        md_file.write(markdown_output)
    


    # We will then find shortcomings in the JSON

    '''
    if not args.pdf_metadata:
        
        # Given the initial search results, we will try to find very specific PDFs which deep dive into particular topic
        # Perplexity search results can only provide a high level context & lack specific citations, but can point us in right direction

        google_pdf_search_queries = llm_generate_pdf_search_queries(search_queries_dict_with_results)

        print(google_pdf_search_queries)

        google_pdf_search_queries_with_results = execute_google_pdf_search_queries_dict(google_pdf_search_queries)

         # Get the current date and time in a human-readable format suitable for filenames
        datetime_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Create the filename using the current date and time
        filename = f'google_pdf_search_queries_results_{datetime_str}.json'

        # Write the updated dictionary to the JSON file
        with open(filename, 'w') as json_file:
            json.dump(google_pdf_search_queries_with_results, json_file, indent=4)

    else:
        # Given the folder of PDFs, extract each PDF and augment to search results JSON
        process_google_pdf_search_results_json(args.pdf_metadata, args.research_plan)
    '''
    
   



    # We will continue to do more search until user is satisfied

    # Afterwards, we will generate search queries to find high quality PDF

    # Perform BERTopic Modelling on the PDFs and continue to augment the preliminary report until user is satisfied

if __name__ == "__main__":
    main()