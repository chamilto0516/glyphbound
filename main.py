import argparse
import logging
import sys

from glyphbound.log_setup import setup_logging


def main():
    parser = argparse.ArgumentParser(prog="glyphbound")
    parser.add_argument("--just-map", action="store_true", help="Print a generated map as ASCII and exit")
    parser.add_argument("--seed", type=int, default=None, help="RNG seed for reproducible generation")
    parser.add_argument("--floor", type=int, default=1, help="Floor level to generate (default 1)")
    parser.add_argument("--theme", type=str, default=None, help="Theme name (e.g. Catacombs, Library)")
    args = parser.parse_args()

    if args.just_map:
        from glyphbound.dungeon import generate_dungeon, dump_map_text
        dungeon = generate_dungeon(floor=args.floor, seed=args.seed, theme_name=args.theme)
        dump_map_text(dungeon)
        sys.exit(0)

    setup_logging()
    logging.getLogger("glyphbound").info("=== Glyphbound starting ===")
    from glyphbound.app import GlyphboundApp
    app = GlyphboundApp()
    app.run()


if __name__ == "__main__":
    main()
