import json
import re
import requests
import sys

CSRF_PATTERN = re.compile(r'<meta name="csrf-token" content="(.*?)" />')
ACCESS_TOKEN_PATTERN = re.compile(r"<meta content='(.*?)' name='[0-9a-z]{32}'>")


with open("credentials.json", "r") as f:
    credentials = json.load(f)

username = credentials["username"]
password = credentials["password"]

login_url = "https://app.im.skeepers.io/login"
search_url = "https://app.im.skeepers.io/creators/campaigns/search"
gifted_payload = (
    "https://app.im.skeepers.io/api/v3/campaigns?format=attributes&include=store"
    "&page%5Bsize%5D=9&page%5Bnumber%5D=1"
    "&filter%5Bplatform_entity_id%5D=Consumer%3A%3AUser-324408"
)
# gifted_payload = "https://app.im.skeepers.io/api/v3/campaigns?format=attributes&include=store&page%5Bsize%5D=81&page%5Bnumber%5D=1"

with requests.Session() as s:
    s.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
        }
    )

    print("Logging in...")
    login_page = s.get(login_url)
    try:
        csrf_token = re.findall(CSRF_PATTERN, login_page.text)[0]
    except IndexError:
        print("No CSRF token found; exiting!")
        sys.exit(1)
    
    login_request = s.post(
        login_url,
        data={
            "authenticity_token": csrf_token,
            "sign_in[email]": username,
            "sign_in[password]": password,
        },
        allow_redirects=False,
    )

    print("Getting products...")
    search_page = s.get(search_url)
    try:
        access_token = re.findall(ACCESS_TOKEN_PATTERN, search_page.text)[0]
    except IndexError:
        print("Couldn't find access token; exiting!")
        sys.exit(1)
    
    gifted_content = s.get(gifted_payload, headers={"Access-Token": access_token})
    gifted_products = json.loads(gifted_content.text)
    product_title_by_id = {product["id"]: product["title"] for product in gifted_products}

    with open("ids.json", "r+") as f:
        ids = product_title_by_id.keys()
        previous_ids = set(json.load(f))
        f.seek(0)
        json.dump(list(ids), f)
        f.truncate()

    if new_ids := ids - previous_ids:
        print("Got new products!")
        new_titles = [product_title_by_id[new_id] for new_id in new_ids]
