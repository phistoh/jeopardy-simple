import argparse
import sys

from PySide6.QtWidgets import QApplication

from game import Game

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "config",
        nargs="?",
        default="config.toml",
        help="Path to the TOML configuration file",
    )
    args = parser.parse_args()

    app = QApplication(sys.argv)

    game = Game(args.config)
    game.window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()