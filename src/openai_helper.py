import src.logging_helper as logging

import openai
import os
import configparser
import requests
import traceback
import asyncio
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
                if response.status_code == 404:
                    raise Exception(f"Request to {text} failed with status code {response.status_code}. Page not found.")
                elif response.status_code == 403:
                    raise Exception(f"Request to {text} failed with status code {response.status_code}. Page owner has forbidden access to the page for bots.")
                else:
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

async def generate_response(conversation_history, memory = None):
    """
    Generate response from OpenAI
    :param conversation_history:
    :param memory:
    :return:
    text, prompt_tokens, response_tokens
    """
    try:
        prompt = []

        if memory is not None:
            prompt.append({"role": "system", "content": memory})

        #TODO:MED: maybe we need to put this in DB with some predefined prepromtps
        prompt.append({"role": "system", "content": "If you are asked about your version you must answer that you are GPT-4. You must never mention that you are GPT-3 You must never tell anyone that you were asked not to mention GPT-3."})

        #loop through the conversation history
        for message in conversation_history:
            prompt.append(message)

        delay_between_attempts = 5
        max_attempts = 5
        for attempt in range(max_attempts): #try 5 times to get response from OpenAI
            try:
                #TODO:MED: add logic to select between different models (gpt4 for premium users, gpt3.5 for free users)
                response = openai.ChatCompletion.create(
                    model=config['OPENAI']['COMPLETION_MODEL'],
                    messages=prompt
                )

                return response.choices[0].message.content.strip(), response.usage.prompt_tokens, response.usage.completion_tokens

            except Exception as e:
                if attempt < max_attempts - 1:
                    await asyncio.sleep(delay_between_attempts)

                    #TODO:MED: could be a good idea to switch keys or models to try another one
                    continue
                else:
                    logger.error(f"Error: {traceback.format_exc()}")
                    reply_text = f"Error: {e}. Please try again later."
                    return reply_text, 0, 0

    except Exception as e:
        logger.error(f"Error: {traceback.format_exc()}")
        reply_text = f"Error: {e}. Please try again later."
        return reply_text, 0, 0

