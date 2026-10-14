import tomllib


def load_questions(filename):
    with open(filename, "rb") as file:
        return tomllib.load(file)
