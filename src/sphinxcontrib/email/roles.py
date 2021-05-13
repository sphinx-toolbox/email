from typing import List, Tuple

import sphinx.util
from docutils import nodes
from docutils.nodes import Node, system_message
from sphinx.util.docutils import SphinxRole

logger = sphinx.util.logging.getLogger(__name__)


class EmailNode(nodes.reference):
    pass


class EmailRole(SphinxRole):
    def run(self) -> Tuple[List[Node], List[system_message]]:
        """Role to obfuscate e-mail addresses.

        Handle addresses of the form
        "name@domain.org"
        "Name Surname <name@domain.org>"
        """

        node = EmailNode(
            self.rawtext,
            self.text,
            refuri=f"mailto:{self.text}",
            raw_uri=self.text,
        )

        return [node], []
