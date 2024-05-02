import traceback
from datetime import date
from typing import List

import yagmail
from munch import Munch

DEV_EMAIL = "hi.daniel.liu@gmail.com"
OAUTH_PATH = "credentials/oauth2_creds.json"


def send_email(products: List[Munch], username: str) -> None:
    product_htmls = [
        (
            '<div>'
            f'<img style="max-height: 200px;" src="{product.photo_urls.large}" />'
            f'<p><a href="https://app.im.skeepers.io/creators/campaigns/{product.id}">{product.title}</a></p>'
            '</div>'
        ) for product in products
    ]
    with yagmail.SMTP(username, oauth2_file=OAUTH_PATH) as yag:
        yag.send(
            to=username,
            subject=f"New Gifted Reviews Are Available! ({date.today()})",
            contents=(
                "<p>This is an automated message notifying you that the following gifted reviews are available:</p>"
                f"{''.join(product_htmls)}"
                "<p>Happy shopping!</p>"
            ),
        )

def send_error_report(username: str, e: Exception) -> None:
    error_report = "".join(traceback.format_tb(e.__traceback__)).replace("\n", "<br>")
    with yagmail.SMTP(username, oauth2_file=OAUTH_PATH) as yag:
        yag.send(
            to=DEV_EMAIL,
            subject=f"Skeeper Scraper encountered an error ({date.today()})",
            contents=(
                "<p>Skeepers Scraper encountered an error. The stack trace is as follows:</p>"
                f"<p>{error_report}</p>"
            ),
        )