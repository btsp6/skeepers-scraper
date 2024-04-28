from typing import List

import yagmail
from munch import Munch

OAUTH_PATH = "credentials/oauth2_creds.json"


def send_email(products: List[Munch], username: str) -> None:
    product_htmls = []
    for product in products:
        product_htmls.append(
            '<div>'
            f'<img style="max-height: 200px;" src="{product.photo_urls.large}" />'
            f'<p><a href="https://app.im.skeepers.io/creators/campaigns/{product.id}">{product.title}</a></p>'
            '</div>'
        )
    html = (
        "<p>This is an automated message notifying you that the following gifted reviews are available:</p>"
        f"{''.join(product_htmls)}"
        "<p>Happy shopping!</p>"
    )
    with yagmail.SMTP(username, oauth2_file=OAUTH_PATH) as yag:
        yag.send(
            to=username,
            subject="New Gifted Reviews Are Available!",
            contents=html,
        )