import functools
import json
import re
import time
from typing import List, Set

import requests
from munch import Munch
from requests import ConnectionError, HTTPError

from emailer import send_email, send_error_report
from logger import Logger

CSRF_PATTERN = re.compile(r'<meta name="csrf-token" content="(.*?)" />')
ACCESS_TOKEN_PATTERN = re.compile(r"<meta content='(.*?)' name='[0-9a-z]{32}'>")

SCRAPE_FREQUENCY_S = 15
MAX_PATTERN_ERRORS = 100
MAX_CONNECTION_ERRORS = 100

ID_PATH = "data/ids.json"
CREDENTIALS_PATH = "credentials/credentials.json"
LOGIN_URL = "https://app.im.skeepers.io/login"
SEARCH_URL = "https://app.im.skeepers.io/creators/campaigns/search"
GIFTED_PAYLOAD = (
    "https://app.im.skeepers.io/api/v3/campaigns?format=attributes&include=store"
    "&page%5Bsize%5D=81&page%5Bnumber%5D=1"
    "&filter%5Bplatform_entity_id%5D=Consumer%3A%3AUser-324408"
)


class PatternNotFoundError(Exception):
    pass

def get_html_pattern(pattern: re.Pattern[str], html: requests.Response, error_msg: str = None) -> str:
    try:
        return re.findall(pattern, html.text)[0]
    except IndexError:
        raise PatternNotFoundError(f"{error_msg}")

@functools.cache
def get_previous_ids() -> Set[str]:
    with open(ID_PATH, "r") as f:
        return set(json.load(f))

def set_previous_ids(ids: Set[str]) -> None:
    with open(ID_PATH, "w") as f:
        json.dump(list(ids), f)
    get_previous_ids.cache_clear()

def process_new_products(products: List[Munch]) -> List[Munch]:
    product_by_id = {product.id: product for product in products}
    current_ids = set(product_by_id)
    previous_ids = get_previous_ids()
    if previous_ids == current_ids:
        return []
    
    set_previous_ids(current_ids)
    new_ids = current_ids - previous_ids
    return [product_by_id[new_id] for new_id in new_ids]

def login(s: requests.Session, username: str, password: str) -> None:
    login_page = s.get(LOGIN_URL)
    s.post(
        LOGIN_URL,
        data={
            "authenticity_token": get_html_pattern(
                CSRF_PATTERN,
                login_page,
                error_msg="No CSRF token found",
            ),
            "sign_in[email]": username,
            "sign_in[password]": password,
        },
        allow_redirects=False,
    )

def scrape(credentials: Munch) -> None:
    pattern_error_count = 0
    login_error_count = 0
    needs_login = True
    with requests.Session() as s:
        s.headers["User-Agent"] = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        )

        while True:
            try:
                if needs_login:
                    Logger.log("Logging in...")
                    login(s, *credentials.skeepers.values())
                    needs_login = False

                Logger.log("Scraping...")
                search_page = s.get(SEARCH_URL)
                gifted_content = s.get(
                    GIFTED_PAYLOAD,
                    headers={
                        "Access-Token": get_html_pattern(
                            ACCESS_TOKEN_PATTERN,
                            search_page,
                            error_msg="Missing access token",
                        )
                    },
                )
                gifted_content.raise_for_status()

            except PatternNotFoundError as e:
                pattern_error_count += 1
                Logger.log(f"Regex pattern failed to match: {e}")
                if pattern_error_count >= MAX_PATTERN_ERRORS:
                    Logger.log(f"Max pattern errors reached, exiting.")
                    break
            except (ConnectionError, HTTPError) as e:
                login_error_count += 1
                needs_login = True
                Logger.log(f"Failed to reach website: {e}")
                if login_error_count >= MAX_CONNECTION_ERRORS:
                    Logger.log(f"Max connection errors reached, exiting.")
                    break
            else:
                login_error_count = 0
                pattern_error_count = 0
                gifted_products = [Munch.fromDict(product) for product in gifted_content.json()]
                new_products = process_new_products(gifted_products)
                if new_products:
                    # New products are up, send the email!
                    Logger.log("New products found! Preparing email...")
                    send_email(new_products, credentials.gmail.username)
                    Logger.log("Email sent!")
            
            time.sleep(SCRAPE_FREQUENCY_S)
                

if __name__ == "__main__":
    with open(CREDENTIALS_PATH, "r") as f:
        credentials = Munch.fromDict(json.load(f))
    try:
        scrape(credentials)
    except KeyboardInterrupt as e:
        Logger.log("Shutting down.")
    except Exception as e:
        send_error_report(credentials.gmail.username, e)
        raise
