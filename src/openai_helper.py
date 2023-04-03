import src.logging_helper as logging

import openai
import os
import configparser
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup

config = configparser.ConfigParser(os.environ)
config_path = os.path.dirname(__file__) + '/../config/' #we need this trick to get path to config folder
config.read(config_path + 'settings.ini')

logger = logging.get_logger()

def helper_get_url_content(text):
    # Check if the input text is a valid URL
    try:
        result = urlparse(text)
        if all([result.scheme, result.netloc]):
            # If it is a valid URL, retrieve the content from the URL
            response = requests.get(text)
            if response.status_code == 200:
                # If the request is successful, let's clean it with BeautifulSoup
                soup = BeautifulSoup(response.text, "html.parser")
                title = soup.title.get_text(separator=" ", strip=True) if soup.title else None
                body = soup.body.get_text(separator=" ", strip=True) if soup.body else None

                return title, body
            else:
                # If the request is not successful, raise an exception
                raise Exception(f"Request to {text} failed with status code {response.status_code}")
        else:
            # If it is not a valid URL, return None
            return None, None
    except ValueError:
        # If there is an error parsing the URL, return None
        return None, None

def helper_get_summary_from_text(content_body, content_title = None, ):
    #TODO:HIGH: seems like we need to move this helpers to a separate openai file
    # get openai summary from url_content
    openai.api_key = config['OPENAI']['KEY']

    # split content into chunks of 2000 chars and loop through them
    content_chunks = [content_body[i:i + 2000] for i in range(0, len(content_body), 2000)]

    summary_chunks = []

    for i, content_chunk in enumerate(content_chunks):
        chunk_messages = [
            {"role": "system",
             "content": f"Give me a takeaway summary for this text"},
            {"role": "user",
             "content": f"Title: {content_title}"},
            {"role": "user",
             "content": f"Content {i}:  {content_chunk}"}
        ]

        response = openai.ChatCompletion.create(
            model=config['OPENAI']['COMPLETION_MODEL'],
            messages=chunk_messages,
            temperature=float(config['OPENAI']['TEMPERATURE']),
            max_tokens=int(config['OPENAI']['MAX_TOKENS']),
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        if response['choices'][0]['message']['content'] is not None:
            summary_chunks.append(response['choices'][0]['message']['content'])

        #TODO:LOW: it's a good idea to edit previous message adding a dot at each iteration for Generating summary...
        print(f"Generating summary... {i}")

    #TODO:MED: summary_chunks togetter also could be bigger then maximum allowed tokes. We need to check this and maybe make another itteraction of summarization of summary by chanks.

    messages = [
        {"role": "system",
         "content": f"Give me a takeaway summary based on title and texts."},
        {"role": "user",
         "content": f"Title: {content_title}"}
    ]
    # now let's run through the summary chunks and get a summary of the summaries
    for j, summary_chunk in enumerate(summary_chunks):
        messages.append({"role": "user",
                         "content": f"Content {j}:  {summary_chunk}"})
    messages.append({"role": "user",
                     "content": f"Summary:"})

    response = openai.ChatCompletion.create(
        model=config['OPENAI']['COMPLETION_MODEL'],
        messages=messages,
        temperature=float(config['OPENAI']['TEMPERATURE']),
        max_tokens=int(config['OPENAI']['MAX_TOKENS']),
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )
    summary_of_summaries = response['choices'][0]['message']['content']

    return summary_of_summaries

def helper_get_summary_from_url(url):
    url_content_title, url_content_body = helper_get_url_content(url)
    # check if url is valid
    if url_content_body is not None:
        helper_get_summary_from_text(url_content_body)
    else:
        return None



def helper_get_answer_from_prompt(prompt):
    pass
    # try:
    #     openai.api_key = config['OPENAI']['KEY']
    #
    #     messages = [
    #         {"role": "system",
    #          "content": f"Act as a chatbot assistant and answer users question."}, #TODO:LOW: may be we need to rewrite this prompt
    #         {"role": "user",
    #          "content": f"{prompt}"}
    #     ]
    #
    #     response = openai.ChatCompletion.create(
    #         model=config['OPENAI']['COMPLETION_MODEL'],
    #         messages=messages,
    #         temperature=float(config['OPENAI']['TEMPERATURE']),
    #         max_tokens=int(config['OPENAI']['MAX_TOKENS']),
    #         top_p=1,
    #         frequency_penalty=0,
    #         presence_penalty=0,
    #     )
    #     if response['choices'][0]['message']['content'] is not None:
    #         return response['choices'][0]['message']['content']
    #     else:
    #         return None
    # except Exception as e:
    #     logger.error(e)
    #     return None