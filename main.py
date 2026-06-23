import logging

from glyphbound.app import GlyphboundApp
from glyphbound.log_setup import setup_logging


def main():
    setup_logging()
    logging.getLogger("glyphbound").info("=== Glyphbound starting ===")
    app = GlyphboundApp()
    app.run()


if __name__ == "__main__":
    main()
