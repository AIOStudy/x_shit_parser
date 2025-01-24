from typing import List

from modules.telegram import send_message_to_user
from modules.tweet_id_storage import TweetIdStorage
from modules.x import XAPIHandler
from settings import CHECK_RETWEETS
from utils import extract_text_from_image, get_contract_address


class XParser:
    LATEST_TWEETS_ID_PATH = "latest_tweets_id.json"

    def __init__(self):
        self.x_api_handler = XAPIHandler()
        self.tweet_id_storage = TweetIdStorage()

    def parse_account(self, username: str) -> None:
        user_id = self.x_api_handler.fetch_user_id_by_username(username)
        fetched_tweets = self.x_api_handler.fetch_user_tweets(username, user_id)

        if not fetched_tweets.get("data"):
            print(f"Нет новых твитов от {username}")
            return

        for tweet in reversed(fetched_tweets["data"]):
            if CHECK_RETWEETS and tweet.get("referenced_tweets"):
                for ref_tweet in tweet["referenced_tweets"]:
                    ref_tweet = self.x_api_handler.get_tweet_by_id(ref_tweet["id"])
                    ref_tweet_data = ref_tweet.get("data", {})

                    media = ref_tweet.get("includes", {}).get("media", [])

                    image_urls = []
                    for media_item in media:
                        if media_item.get("url"):
                            image_urls.append(media_item["url"])

                    self._process_tweet(
                        username,
                        ref_tweet_data["id"],
                        ref_tweet_data.get("note_tweet", {}).get("text")
                        or ref_tweet_data.get("text", ""),
                        image_urls,
                    )
            else:
                self.tweet_id_storage.save_last_tweet_id(username, tweet["id"])

                media = fetched_tweets.get("includes", {}).get("media", [])
                media_keys = tweet.get("attachments", {}).get("media_keys", [])

                image_urls = []
                for media_item in media:
                    if media_item["media_key"] in media_keys and media_item.get("url"):
                        image_urls.append(media_item["url"])

                self._process_tweet(
                    username,
                    tweet["id"],
                    tweet.get("note_tweet", {}).get("text") or tweet.get("text", ""),
                    image_urls,
                )

    def _process_tweet(
        self,
        username: str,
        tweet_id: str = "",
        tweet_text: str = "",
        image_urls: List[str] = [],
    ) -> None:
        if contract := get_contract_address(tweet_text):
            self._notify_contract_found(contract, username, tweet_id, "text")
            return

        for image_url in image_urls:
            image_text = extract_text_from_image(image_url)
            if contract := get_contract_address(image_text):
                self._notify_contract_found(contract, username, tweet_id, "image")

    def _notify_contract_found(
        self, contract: str, username: str, tweet_id: str, source: str
    ) -> None:
        tweet_url = f"https://x.com/{username}/status/{tweet_id}"

        if source == "text":
            message = f"Контракт найден в тексте твита: `{contract}`\n\n[Ссылка на твит]({tweet_url})"
        else:
            message = f"Контракт найден в изображении твита и может быть неправильным: `{contract}`\n\n[Ссылка на твит]({tweet_url})"

        send_message_to_user(message)
