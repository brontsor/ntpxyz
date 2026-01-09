"""Telegram sender

Public Functions
----------------
send_to_telegram : takes image, sends it to Telegram

Notes
-----
There are some limitations noted in the function documentation below

See Also
--------

"""

from __future__ import annotations

import json

import requests


def send_to_telegram(
    telegram_token: str, chat_id: str, image_path: str, caption: str
) -> tuple[bool, str]:
    """takes image, sends it to Telegram

    png images are accepted reliably
    pdf files are usually too large
    svg is untested

    Does not currenly have any retry/abort/fail logic, this function is slated for
    refactoring.

    In pyproject.toml, we set max-returns = 8 to silence ruff errors for this function

    Args:
        telegram_token : a valid Telegram token
        chat_id : a valid Telegram Chat ID
        image_path : the path to the image that we want to send
        caption : the caption for the image

    Returns:
        bool: true on success, false on failure
        str: error code on failure
        We catch:
            HTTP response codes != 200
            Telegram API errors embedded in json response
            FileNotFoundError, if image_path is invalid
            PermissionsError, if image_path is restricted from the runtime user
            requests.RequestsException, if requests has an issue
            json.JSONDecodeError, if json decoding has an issue

    Raises:
        None
    """
    url: str = f"https://api.telegram.org/bot{telegram_token}/sendPhoto"
    http_error_code = 200

    try:
        with open(image_path, "rb") as photo:
            response = requests.post(
                url,
                data={"chat_id": chat_id, "caption": caption},
                files={"photo": photo},
            )
        if response.status_code != http_error_code:
            return (False, f"HTTP error: {response.status_code} - {response.text}")
        response_data = response.json()
        if response_data.get("ok", False):
            return True, "Image sent sucessfully"
        else:
            return False, (
                "Telegram API error: "
                f"{response_data.get('description', 'Unknown error')}"
            )

    # filesystem errors
    except FileNotFoundError:
        return False, f"Image file not found: {image_path!r}"
    except PermissionError:
        return False, f"Permission denied to image: {image_path!r}"
    # network and json errors
    except json.JSONDecodeError:
        return False, "Invalid JSON response from Telegram"
    except requests.RequestException as e:
        return False, f"Network error: {str(e)!r}"
    except Exception as e:
        return False, f"General Error {str(e)!r}"
