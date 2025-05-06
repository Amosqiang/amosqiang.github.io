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

# 新增：定义需要包含的标签 (请修改为你想要的标签!)
# 注意：标签匹配是大小写不敏感的
REQUIRED_TAG = "X" # <--- 修改这里为你想要的标签名

# --- 函数 ---
def get_last_posted_guid(file_path):
    """从状态文件中读取上次发布的文章 GUID"""
    try:
        with open(file_path, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def update_last_posted_guid(file_path, guid):
    """将最新的 GUID 写入状态文件"""
    with open(file_path, 'w') as f:
        f.write(guid)
    print(f"Updated state file with GUID: {guid}")

def post_tweet(text):
    """使用 Tweepy V2 API 发布推文"""
    if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET]):
        print("Error: Missing API credentials in environment variables.")
        return False

    try:
        client = tweepy.Client(
            consumer_key=API_KEY, consumer_secret=API_SECRET,
            access_token=ACCESS_TOKEN, access_token_secret=ACCESS_TOKEN_SECRET
        )
        response = client.create_tweet(text=text)
        print(f"Tweet posted successfully! Tweet ID: {response.data['id']}")
        return True
    except tweepy.errors.TweepyException as e:
        print(f"Error posting tweet: {e}")
        if isinstance(e, tweepy.errors.Forbidden) and 'duplicate' in str(e).lower():
             print("Detected duplicate tweet. Skipping.")
             return False 
        return False
    except Exception as e:
        print(f"An unexpected error occurred during tweeting: {e}")
        return False

# --- 主逻辑 ---
print("Starting blog sync process...")
print(f"Required tag for tweeting: '{REQUIRED_TAG}' (case-insensitive)")

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

newest_guid_in_this_run = None
posts_found_since_last = []
found_last_posted = (last_posted_guid is None) 

for entry in feed.entries: # feed.entries 通常从新到旧排列
    entry_guid = entry.get('guid', entry.get('link'))
    entry_title = entry.title
    entry_link = entry.link

    if newest_guid_in_this_run is None:
         newest_guid_in_this_run = entry_guid 

    if entry_guid == last_posted_guid:
        print(f"Found the last posted entry GUID ({last_posted_guid}). No more new posts before this.")
        found_last_posted = True
        break 

    if not found_last_posted:
        # ******** 新增逻辑：检查标签 ********
        has_required_tag = False
        if hasattr(entry, 'tags') and isinstance(entry.tags, list):
            for tag_info in entry.tags:
                # feedparser 通常将 <category> 解析到 entry.tags
                # tag_info 是一个包含 'term', 'scheme', 'label' 的对象
                if hasattr(tag_info, 'term') and tag_info.term.lower() == REQUIRED_TAG.lower():
                    has_required_tag = True
                    print(f"Entry '{entry_title}' has the required tag '{REQUIRED_TAG}'.")
                    break # 找到一个匹配就够了

        if not has_required_tag:
             print(f"Entry '{entry_title}' does NOT have the required tag '{REQUIRED_TAG}'. Skipping.")
             continue # 跳过这篇没有所需标签的文章

        # 如果文章是新的并且包含所需标签，才将其加入待发布列表
        print(f"Entry '{entry_title}' is new and has the required tag. Adding to tweet list.")
        posts_found_since_last.append((entry_guid, entry_title, entry_link))
        # *************************************

# (首次运行处理逻辑保持不变，但也应该检查标签) - 修改如下
if not posts_found_since_last and last_posted_guid is None and feed.entries:
    latest_entry = feed.entries[0]
    entry_guid = latest_entry.get('guid', latest_entry.get('link'))
    entry_title = latest_entry.title
    entry_link = latest_entry.link

    # ******** 新增逻辑：首次运行时也检查标签 ********
    has_required_tag = False
    if hasattr(latest_entry, 'tags') and isinstance(latest_entry.tags, list):
         for tag_info in latest_entry.tags:
             if hasattr(tag_info, 'term') and tag_info.term.lower() == REQUIRED_TAG.lower():
                 has_required_tag = True
                 break

    if has_required_tag:
        print(f"First run detected. Preparing to post the latest entry (with tag): {entry_title}")
        posts_found_since_last.append((entry_guid, entry_title, entry_link))
        newest_guid_in_this_run = entry_guid 
    else:
        print(f"First run detected, but the latest entry '{entry_title}' does NOT have the required tag '{REQUIRED_TAG}'. Nothing to post.")
        # 即使首次运行没有符合条件的文章，也应该更新状态到最新一篇，防止下次重复检查
        if newest_guid_in_this_run:
             update_last_posted_guid(STATE_FILE_PATH, newest_guid_in_this_run)
    # *******************************************

if posts_found_since_last:
    print(f"Found {len(posts_found_since_last)} new post(s) with tag '{REQUIRED_TAG}' to tweet.")
    # 反转列表，使得发帖顺序是从旧到新
    for guid, title, link in reversed(posts_found_since_last):
        tweet_text = f"New Post: {title} {link}"
        if len(tweet_text) > 280:
            available_len = 280 - len(f"New Post: ... {link}")
            if available_len > 0:
                tweet_text = f"New Post: {title[:available_len]}... {link}"
            else: 
                print(f"Warning: Cannot shorten tweet sufficiently for '{title}'. Skipping.")
                continue 

        print(f"Attempting to post: {tweet_text}")
        time.sleep(5) 
        if post_tweet(tweet_text):
             update_last_posted_guid(STATE_FILE_PATH, guid)
             time.sleep(10) 
        else:
             print(f"Failed to post tweet for {title}. Stopping further posts in this run.")
             break 
else:
     # 只有在 posts_found_since_last 为空时才打印这条（避免上面首次运行不符合条件时也打印）
    if not (last_posted_guid is None and feed.entries):
        print(f"No new posts found with tag '{REQUIRED_TAG}' since the last run.")


# 如果本次运行没有要发布的帖子，但 feed 里有内容，且状态文件是空的
# (并且首次运行的最新文章也没有所需标签)，将状态更新为 feed 里最新的 GUID
# (防止下次运行时把旧文章误判为新文章)
if not posts_found_since_last and newest_guid_in_this_run and last_posted_guid is None:
     print("No posts to tweet this run, but updating state to the newest entry GUID found in feed.")
     update_last_posted_guid(STATE_FILE_PATH, newest_guid_in_this_run)


print("Blog sync process finished.")