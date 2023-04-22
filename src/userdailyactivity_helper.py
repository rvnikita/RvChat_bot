import src.db_helper as db_helper
import src.logging_helper as logging
import src.amplitude_helper as amplitude_helper



import traceback
import configparser
import os
import datetime

config = configparser.ConfigParser(os.environ)
config_path = os.path.dirname(__file__) + '/../config/' #we need this trick to get path to config folder
config.read(config_path + 'settings.ini')

logger = logging.get_logger()

def update_userdailyactivity(user_id, command=None, usage_count=None, prompt_tokens=None, completion_tokens=None):
    try:
        amplitude_helper.track(
            user_id=user_id,
            event_type = command,
            event_properties={
                'usage_count': usage_count,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens
            }
        )

        with db_helper.session_scope() as session:
            user_daily_activity = session.query(db_helper.UserDailyActivity).filter_by(user_id=user_id, date=datetime.date.today(), command_name=command).first()

            if user_daily_activity is None:
                user_daily_activity = db_helper.UserDailyActivity(user_id=user_id, command_name=command, usage_count=usage_count, prompt_tokens=0, completion_tokens=0)
                session.add(user_daily_activity)
            else:
                if usage_count is not None:
                    user_daily_activity.usage_count += usage_count

            if prompt_tokens is not None:
                user_daily_activity.prompt_tokens += prompt_tokens

            if completion_tokens is not None:
                user_daily_activity.completion_tokens += completion_tokens

            session.commit()

    except Exception as e:
            logger.error(f"Error: {traceback.format_exc()}")
        # await safe_send_message(event.chat_id, f"Error: {e}. Please try again later.")