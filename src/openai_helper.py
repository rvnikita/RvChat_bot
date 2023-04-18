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

def get_url_content(text):
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

def get_summary_from_text(content_body, content_title=None, char_limit=2000):
    print(len(content_body))

    prompt_tokens, completion_tokens = 0, 0

    openai.api_key = config['OPENAI']['KEY']

    def chunk_text(text, chunk_size=2000):
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    def generate_summary(messages):
        response = openai.ChatCompletion.create(
            model=config['OPENAI']['COMPLETION_MODEL'],
            messages=messages,
            temperature=float(config['OPENAI']['TEMPERATURE']),
            max_tokens=int(config['OPENAI']['MAX_TOKENS']),
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        return response['choices'][0]['message']['content'], response.usage.prompt_tokens, response.usage.completion_tokens

    summary = content_body

    while True:
        summary_chunks = chunk_text(summary)
        new_summary_chunks = []

        new_prompt_tokens, new_completion_tokens = 0, 0

        for i, summary_chunk in enumerate(summary_chunks):
            chunk_messages = [
                {"role": "system",
                 "content": f"Give me a takeaway summary for this text"},
                {"role": "user",
                 "content": f"Title: {content_title}"},
                {"role": "user",
                 "content": f"Content {i}:  {summary_chunk}"}
            ]

            new_summary_chunk, prompt_tokens_chunk, completion_tokens_chunk = generate_summary(chunk_messages)
            new_summary_chunks.append(new_summary_chunk)
            new_prompt_tokens += prompt_tokens_chunk
            new_completion_tokens += completion_tokens_chunk
            print(f"Generating summary... {i}")

        new_summary = " ".join(new_summary_chunks)

        if len(new_summary) <= char_limit:
            final_summary = new_summary
            prompt_tokens += new_prompt_tokens
            completion_tokens += new_completion_tokens
            break
        else:
            summary = new_summary

    return final_summary, prompt_tokens, completion_tokens

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

