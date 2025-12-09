import os
import time
import feedparser
import tweepy

API_KEY = os.environ.get("X_API_KEY")
API_SECRET = os.environ.get("X_API_SECRET")
ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.environ.get("X_ACCESS_TOKEN_SECRET")

RSS_FEED_URL = os.environ.get("RSS_FEED_URL", "https://amosqiang.github.io/index.xml")
STATE_FILE_PATH = os.environ.get("STATE_FILE_PATH", "last_post_guid.txt")
REQUIRED_TAG = os.environ.get("REQUIRED_TAG", "X")
TWEET_FORMAT = os.environ.get("TWEET_FORMAT", "{title} {link}")


def get_last_posted_guid(file_path: str) -> str | None:
    try:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                guid = f.read().strip()
                return guid or None
        else:
            print("State file not found, assuming first run.")
            return None
    except Exception as e:
        print(f"Error reading state file {file_path}: {e}")
        return None


def update_last_posted_guid(file_path: str, guid: str) -> bool:
    try:
        with open(file_path, "w") as f:
            f.write(guid)
        print(f"Updated state file with GUID: {guid}")
        return True
    except Exception as e:
        print(f"Error writing state file {file_path}: {e}")
        return False


def post_tweet(text: str) -> str:
    if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET]):
        print("Error: Missing API credentials in environment variables.")
        return "error"

    try:
        client = tweepy.Client(
            consumer_key=API_KEY,
            consumer_secret=API_SECRET,
            access_token=ACCESS_TOKEN,
            access_token_secret=ACCESS_TOKEN_SECRET,
        )
        resp = client.create_tweet(text=text)
        print(f"Tweet posted successfully! Tweet ID: {resp.data['id']}")
        return "success"
    except tweepy.errors.TweepyException as e:
        print(f"Error posting tweet: {e}")
        if isinstance(e, tweepy.errors.Forbidden) and "duplicate" in str(e).lower():
            print("Detected duplicate tweet via 403 Forbidden.")
            return "duplicate"
        return "error"
    except Exception as e:
        print(f"An unexpected error occurred during tweeting: {e}")
        return "error"


def main() -> int:
    print("Starting blog sync process...")
    print(f"Required tag for tweeting: '{REQUIRED_TAG}' (case-insensitive)")
    print(f"Tweet format template: '{TWEET_FORMAT}'")

    last_guid = get_last_posted_guid(STATE_FILE_PATH)
    print(f"Last posted GUID from state file: {last_guid}")

    print(f"Fetching RSS feed from: {RSS_FEED_URL}")
    feed = feedparser.parse(RSS_FEED_URL)

    if feed.bozo:
        print(f"Error parsing RSS feed: {feed.bozo_exception}")
        return 1
    if not feed.entries:
        print("No entries found in the RSS feed.")
        return 0

    first_entry = feed.entries[0]
    newest_guid_in_run = (
        getattr(first_entry, "id", None)
        or getattr(first_entry, "guid", None)
        or getattr(first_entry, "link", None)
    )

    posts_to_tweet: list[dict] = []
    found_last_marker = False

    for entry in feed.entries:
        entry_guid = (
            getattr(entry, "id", None)
            or getattr(entry, "guid", None)
            or getattr(entry, "link", None)
        )
        if not entry_guid:
            title = getattr(entry, "title", "Untitled")
            print(f"Skipping entry with missing GUID/Link: {title}")
            continue

        title = getattr(entry, "title", "Untitled Post")
        link = getattr(entry, "link", "")

        if last_guid and entry_guid == last_guid:
            print(f"Found the last posted entry GUID ({last_guid}). Stop at this entry.")
            found_last_marker = True
            break

        has_required_tag = False
        if hasattr(entry, "tags") and isinstance(entry.tags, list):
            for tag_info in entry.tags:
                term = getattr(tag_info, "term", None)
                if isinstance(term, str) and term.lower() == REQUIRED_TAG.lower():
                    has_required_tag = True
                    break

        if has_required_tag:
            print(f"Found potential new post with required tag: '{title}'")
            posts_to_tweet.append(
                {
                    "guid": entry_guid,
                    "title": title,
                    "link": link,
                }
            )
        else:
            print(f"Skipping entry '{title}' (either older or lacks required tag).")

    latest_guid_to_save = None
    final_state_updated = False

    if last_guid is None:
        print("First run (or state lost).")
        if posts_to_tweet:
            newest_tagged = posts_to_tweet[0]
            print(
                "First run: Selecting only the newest post "
                f"with tag: '{newest_tagged['title']}'"
            )
            posts_to_tweet = [newest_tagged]
            latest_guid_to_save = newest_tagged["guid"]
        else:
            print(f"First run, but no posts found with the required tag '{REQUIRED_TAG}'.")
            if newest_guid_in_run:
                latest_guid_to_save = newest_guid_in_run
                print(
                    "Will attempt to update state to newest overall post GUID "
                    f"found in feed: {latest_guid_to_save}"
                )

    if posts_to_tweet:
        print(f"Found {len(posts_to_tweet)} new post(s) with tag '{REQUIRED_TAG}'.")
        for post in reversed(posts_to_tweet):
            guid = post["guid"]
            title = post["title"]
            link = post["link"]

            try:
                tweet_text = TWEET_FORMAT.format(title=title, link=link)
            except KeyError as e:
                print(
                    f"Error formatting tweet: invalid placeholder {e} "
                    f"in TWEET_FORMAT '{TWEET_FORMAT}'. Skipping '{title}'."
                )
                continue

            if len(tweet_text) > 280:
                print(
                    f"Warning: Tweet text exceeds 280 characters "
                    f"(length: {len(tweet_text)}). Truncating..."
                )
                keep = 280 - 3
                if keep > 0:
                    tweet_text = tweet_text[:keep] + "..."
                else:
                    print(
                        "Error: Cannot truncate tweet, format string might be too long. "
                        f"Skipping '{title}'."
                    )
                    continue

            print(f"Attempting to post: {tweet_text}")
            time.sleep(5)

            result = post_tweet(tweet_text)

            if result in ("success", "duplicate"):
                if result == "duplicate":
                    print("Duplicate tweet detected. Updating state as if successful.")
                if update_last_posted_guid(STATE_FILE_PATH, guid):
                    final_state_updated = True
                else:
                    print("Error updating state file! Stopping further posts.")
                    break
                wait_time = 5 if result == "duplicate" else 10
                print(f"Waiting {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(
                    f"Failed to post tweet for '{title}' due to API or other error. "
                    "Stopping further posts in this run."
                )
                break
    else:
        if last_guid is not None:
            print(
                f"No new posts found with tag '{REQUIRED_TAG}' since the last run."
            )

    if not final_state_updated and last_guid is None and latest_guid_to_save:
        print("Performing state update for first run (no tweets sent).")
        update_last_posted_guid(STATE_FILE_PATH, latest_guid_to_save)

    print("Blog sync process finished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
