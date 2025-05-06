import os
import feedparser
import tweepy
import datetime
import time

# --- 配置 ---
API_KEY = os.environ.get("X_API_KEY")
API_SECRET = os.environ.get("X_API_SECRET")
ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.environ.get("X_ACCESS_TOKEN_SECRET")

RSS_FEED_URL = os.environ.get("RSS_FEED_URL", "https://amosqiang.github.io/feed.xml")
STATE_FILE_PATH = os.environ.get("STATE_FILE_PATH", "last_post_guid.txt")

# 从环境变量读取标签，默认为 "X"
REQUIRED_TAG = os.environ.get("REQUIRED_TAG", "X") 
# 从环境变量读取推文格式，提供默认值
TWEET_FORMAT = os.environ.get("TWEET_FORMAT", "{title} {link}") 

# --- 函数 ---
def get_last_posted_guid(file_path):
    try:
        with open(file_path, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print("State file not found, assuming first run or missing artifact.")
        return None
    except Exception as e:
        print(f"Error reading state file {file_path}: {e}")
        return None 

def update_last_posted_guid(file_path, guid):
    try:
        with open(file_path, 'w') as f:
            f.write(guid)
        print(f"Updated state file with GUID: {guid}")
        return True
    except Exception as e:
        print(f"Error writing state file {file_path}: {e}")
        return False

def post_tweet(text):
    """使用 Tweepy V2 API 发布推文，处理重复错误"""
    if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET]):
        print("Error: Missing API credentials in environment variables.")
        return "error" 
    
    try:
        client = tweepy.Client(
            consumer_key=API_KEY, consumer_secret=API_SECRET,
            access_token=ACCESS_TOKEN, access_token_secret=ACCESS_TOKEN_SECRET
        )
        response = client.create_tweet(text=text)
        print(f"Tweet posted successfully! Tweet ID: {response.data['id']}")
        return "success" 
    except tweepy.errors.TweepyException as e:
        print(f"Error posting tweet: {e}")
        if isinstance(e, tweepy.errors.Forbidden) and 'duplicate content' in str(e).lower():
             print("Detected duplicate tweet via 403 Forbidden.")
             return "duplicate" 
        return "error" 
    except Exception as e:
        print(f"An unexpected error occurred during tweeting: {e}")
        return "error"

# --- 主逻辑 ---
print("Starting blog sync process...")
print(f"Required tag for tweeting: '{REQUIRED_TAG}' (case-insensitive)")
print(f"Tweet format template: '{TWEET_FORMAT}'") # 打印当前使用的格式

last_posted_guid = get_last_posted_guid(STATE_FILE_PATH)
print(f"Last posted GUID from state file: {last_posted_guid}")

print(f"Fetching RSS feed from: {RSS_FEED_URL}")
feed = feedparser.parse(RSS_FEED_URL)

if feed.bozo:
    print(f"Error parsing RSS feed: {feed.bozo_exception}")
    exit(1) 
if not feed.entries:
    print("No entries found in the RSS feed.")
    exit(0) 

# --- 查找新文章逻辑 ---
newest_guid_in_this_run = feed.entries[0].get('guid', feed.entries[0].get('link')) 
posts_to_tweet = [] 
found_last_posted_marker = False 

for entry in feed.entries: 
    entry_guid = entry.get('guid', entry.get('link'))
    entry_title = entry.title
    entry_link = entry.link

    if entry_guid == last_posted_guid:
        print(f"Found the last posted entry GUID ({last_posted_guid}). Processing stops here.")
        found_last_posted_marker = True
        break 

    has_required_tag = False
    if hasattr(entry, 'tags') and isinstance(entry.tags, list):
        for tag_info in entry.tags:
            if hasattr(tag_info, 'term') and tag_info.term.lower() == REQUIRED_TAG.lower():
                has_required_tag = True
                break 

    if has_required_tag:
        print(f"Found potential new post with required tag: '{entry_title}'")
        posts_to_tweet.append({'guid': entry_guid, 'title': entry_title, 'link': entry_link})
    else:
         print(f"Skipping entry '{entry_title}' (either older or lacks required tag).")

# --- 处理首次运行 ---
latest_guid_to_save = None 
if last_posted_guid is None:
    print("First run (or state lost). Processing potentially found posts.")
    if posts_to_tweet: 
        newest_tagged_post_data = posts_to_tweet[0] 
        print(f"First run: Selecting only the newest post with tag: '{newest_tagged_post_data['title']}'")
        posts_to_tweet = [newest_tagged_post_data] 
        latest_guid_to_save = newest_tagged_post_data['guid'] 
    else:
        print(f"First run, but no posts found with the required tag '{REQUIRED_TAG}'.")
        if newest_guid_in_this_run:
             latest_guid_to_save = newest_guid_in_this_run 
             print(f"Will update state to newest overall post GUID found in feed ({latest_guid_to_save}) after run.")

# --- 发布推文 ---
final_state_updated = False 
if posts_to_tweet:
    print(f"Found {len(posts_to_tweet)} new post(s) with tag '{REQUIRED_TAG}' to tweet.")
    for post_data in reversed(posts_to_tweet): 
        guid = post_data['guid']
        title = post_data['title']
        link = post_data['link']
        
        # 使用 TWEET_FORMAT 构建推文
        try:
            tweet_text = TWEET_FORMAT.format(title=title, link=link) 
        except KeyError as e:
            print(f"Error formatting tweet: Invalid placeholder {e} in TWEET_FORMAT '{TWEET_FORMAT}'. Skipping post '{title}'.")
            continue # 跳过这篇格式错误的文章

        # 检查长度 (简单截断整个字符串)
        if len(tweet_text) > 280:
            print(f"Warning: Tweet text exceeds 280 characters (length: {len(tweet_text)}). Truncating...")
            chars_to_keep = 280 - 3 # 为 "..." 留空间
            if chars_to_keep > 0:
                tweet_text = tweet_text[:chars_to_keep] + "..."
            else: 
                print(f"Error: Cannot truncate tweet, format string might be too long. Skipping post '{title}'.")
                continue # 跳过无法截断的

        print(f"Attempting to post: {tweet_text}")
        time.sleep(5) 
        
        post_result = post_tweet(tweet_text) 
        
        if post_result == "success" or post_result == "duplicate":
             if post_result == "duplicate":
                 print("Duplicate tweet detected by API. Updating state file as if successful.")
             
             if update_last_posted_guid(STATE_FILE_PATH, guid):
                 final_state_updated = True 
             else:
                 print("Error updating state file! Further tweets might be duplicated.")
             
             wait_time = 5 if post_result == "duplicate" else 10
             print(f"Waiting {wait_time} seconds...")
             time.sleep(wait_time) 
        
        elif post_result == "error": 
             print(f"Failed to post tweet for {title} due to API or other error. Stopping further posts in this run.")
             break 
else:
    if last_posted_guid is not None:
         print(f"No new posts found with tag '{REQUIRED_TAG}' since the last run.")

# --- 首次运行状态更新 ---
if not final_state_updated and last_posted_guid is None and latest_guid_to_save:
     print(f"Performing state update for first run (no tweets sent).")
     update_last_posted_guid(STATE_FILE_PATH, latest_guid_to_save)

print("Blog sync process finished.")
exit(0)