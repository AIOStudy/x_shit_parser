from time import sleep

from modules.parser import XParser
from settings import PARSING_INTERVAL_MINUTES


def main() -> None:
    parser = XParser()

    with open("x_usernames.txt", "r") as file:
        usernames = file.readlines()

    while True:
        for username in usernames:
            print(f"Начат парсинг аккаунта {username.strip()}")
            parser.parse_account(username.strip())
            print(f"Завершен парсинг аккаунта {username.strip()}")

        print(
            f"Парсинг завершен. Ждем {PARSING_INTERVAL_MINUTES} минут до следующего парсинга..."
        )
        sleep(PARSING_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    main()
