import re
import textwrap
import xml.sax.saxutils  # nosec
from xml.etree import ElementTree as ET  # nosec  # noqa DUO107

import sphinx.util
from docutils import nodes
from sphinx.writers.html import HTMLTranslator

logger = sphinx.util.logging.getLogger(__name__)


class Obfuscator:
    def __init__(self):
        self.rot_13_trans = str.maketrans(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
            "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm",
        )

    def rot_13_encrypt(self, line: str) -> str:
        """Rotate 13 encryption."""
        line = line.translate(self.rot_13_trans)
        line = re.sub(r"(?=[\"])", r"\\", line)
        line = re.sub("\n", r"\n", line)
        line = re.sub(r"@", r"\\100", line)
        line = re.sub(r"\.", r"\\056", line)
        line = re.sub(r"/", r"\\057", line)
        return line

    def xml_to_unesc_string(self, node: ET.Element) -> str:
        """Return unescaped xml string"""
        text = xml.sax.saxutils.unescape(
            ET.tostring(node, encoding="unicode", method="html"),
            {"&apos;": "'", "&quot;": '"'},
        )
        return text

    def js_obfuscated_text(self, text: str) -> str:
        """ROT 13 encryption with embedded in Javascript code to decrypt in the
        browser.
        """
        xml_node = ET.Element("script")
        xml_node.attrib["type"] = "text/javascript"
        js_script = textwrap.dedent(
            """\
            document.write(
                "{text}".replace(/[a-zA-Z]/g,
                    function(c){{
                        return String.fromCharCode(
                            (c<="Z"?90:122)>=(c=c.charCodeAt(0)+13)?c:c-26
                        );
                    }}
                )
            );"""
        )
        xml_node.text = js_script.format(text=self.rot_13_encrypt(text))

        return self.xml_to_unesc_string(xml_node)


def visit_email_node(translator: HTMLTranslator, node: nodes.reference) -> None:

    pattern = r"^(?:(?P<name>.*?)\s*<)?(?P<email>\b[-.\w]+@[-.\w]+\.[a-z]{2,4}\b)>?$"

    match = re.search(pattern, node["raw_uri"])
    if not match:
        return translator.visit_reference(node)

    data = match.groupdict()

    if not node.get("refuri"):
        raise ValueError('"email_node" must have a "refuri" attribute.')

    email = data["email"]
    displayname = data["name"] or email

    atts = {
        "class": "reference external",
        "href": node["refuri"],
    }

    starttag = translator.starttag(node, "a", "", **atts)
    obfuscated = Obfuscator().js_obfuscated_text(f"{starttag}{displayname}</a>")
    translator.body.append(obfuscated)

    raise nodes.SkipNode


def depart_email_node(translator: HTMLTranslator, node: nodes.reference):
    if not isinstance(node.parent, nodes.TextElement):
        translator.body.append("\n")
