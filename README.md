# GPT-4 Telegram Chatbot
This script allows you to create a Telegram chatbot that responds to user messages using the GPT-4 language model. The chatbot works by fetching the last X messages in a conversation and generating a response based on the conversation history.

Demo: http://t.me/rvnikita_public
Author blog: http://t.me/rvnikita_blog

## How to generate a session string
To avoid confirming your account with a code every time the script is launched, you can generate a session string and store it as an environment variable. To generate the session string, run the generate_session_string() function in the script.

## Environment Variables
The following environment variables are required for the script to work:

API_ID: Your Telegram API ID
API_HASH: Your Telegram API Hash
PHONE_NUMBER: Your Telegram account phone number (e.g., +1234567890)
OPENAI_API_KEY: Your OpenAI API Key (make sure you have access to the GPT-4 model or swith to the GPT-3.5 model)
TELEGRAM_SESSION_STRING: The session string generated using the generate_session_string() function

## How to use
### Install the required dependencies:
```
pip install -r requirements.txt
```

### Set the environment variables with the appropriate values:
```
export API_ID=your_api_id
export API_HASH=your_api_hash
export PHONE_NUMBER=your_phone_number
export OPENAI_API_KEY=your_openai_api_key
export TELEGRAM_SESSION_STRING=your_telegram_session_string
exporr LOGGING_CHAT_ID=your_logging_chat_id
```
### Run the dispatcher.py script:
```
python dispatcher.py
```
The script will connect to your Telegram account and start listening for new messages. When a new message is received, it will generate a response using the GPT-4 language model and send it to the user.
