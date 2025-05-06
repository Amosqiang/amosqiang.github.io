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
REQUIRED_TAG = "X" # <--- 确保这里是你想要的标签名

# --- 函数 ---
def get_last_posted_guid(file_path):
    try:
        with open(file_path, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def update_last_posted_guid(file_path, guid):
    with open(file_path, 'w') as f:
        f.write(guid)
    print(f"Updated state file with GUID: {guid}")

def post_tweet(text):
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
    
# --- 修订后的逻辑 ---
newest_guid_in_this_run = feed.entries[0].get('guid', feed.entries[0].get('link')) # 记录 Feed 中最新的 GUID
posts_to_tweet = [] # 存储待发布的文章信息
found_last_posted_marker = False # 标记是否已找到上次发布的文章

for entry in feed.entries: # 遍历 Feed (通常从新到旧)
    entry_guid = entry.get('guid', entry.get('link'))
    entry_title = entry.title
    entry_link = entry.link

    # 如果当前条目就是上次发布的条目，停止处理更旧的条目
    if entry_guid == last_posted_guid:
        print(f"Found the last posted entry GUID ({last_posted_guid}). Processing stops here.")
        found_last_posted_marker = True
        break # 找到了标记，停止循环

    # 只处理在找到标记之前的条目（即 Feed 中更新的条目）
    # 检查这些更新的条目是否包含所需标签
    has_required_tag = False
    if hasattr(entry, 'tags') and isinstance(entry.tags, list):
        for tag_info in entry.tags:
            if hasattr(tag_info, 'term') and tag_info.term.lower() == REQUIRED_TAG.lower():
                has_required_tag = True
                break # 找到标签即可

    if has_required_tag:
        # 如果条目是新的（在标记之前找到）并且有标签，则加入待发布列表
        print(f"Found potential new post with required tag: '{entry_title}'")
        posts_to_tweet.append({'guid': entry_guid, 'title': entry_title, 'link': entry_link})
    else:
        # 即使是新的，如果没有标签也跳过
         print(f"Skipping entry '{entry_title}' (either older or lacks required tag).")

# --- 处理首次运行或状态丢失的情况 ---
if last_posted_guid is None:
    print("First run (or state lost). Processing potentially found posts.")
    if posts_to_tweet:
        # 如果首次运行找到了带标签的文章，只发布最新的一篇
        print(f"First run: Selecting only the newest post with tag from the initial list.")
        newest_tagged_post = posts_to_tweet[0] # 列表目前是新的在前
        posts_to_tweet = [newest_tagged_post] # 只保留最新的一篇
    else:
        # 如果首次运行没找到带标签的文章
        print(f"First run, but no posts found with the required tag '{REQUIRED_TAG}'.")
        # 更新状态到 Feed 中最新的文章 GUID，避免下次重复检查所有文章
        if newest_guid_in_this_run:
             print("Updating state to newest overall post GUID found in feed to prevent re-checking.")
             update_last_posted_guid(STATE_FILE_PATH, newest_guid_in_this_run)

# --- 发布推文 ---
if posts_to_tweet:
    print(f"Found {len(posts_to_tweet)} new post(s) with tag '{REQUIRED_TAG}' to tweet.")
    # 按时间顺序发布（先发布旧的）
    for post_data in reversed(posts_to_tweet): 
        guid = post_data['guid']
        title = post_data['title']
        link = post_data['link']
        
        tweet_text = f"{title} {link}" 
        # 检查长度
        if len(tweet_text) > 280:
            available_len = 280 - len(f"... {link}") 
            if available_len > 0:
                tweet_text = f"{title[:available_len]}... {link}" 
            else: 
                print(f"Warning: Cannot shorten tweet sufficiently for '{title}'. Skipping.")
                continue 

        print(f"Attempting to post: {tweet_text}")
        time.sleep(5) 
        if post_tweet(tweet_text):
             # 每次成功发布后更新状态文件
             update_last_posted_guid(STATE_FILE_PATH, guid) 
             time.sleep(10) 
        else:
             print(f"Failed to post tweet for {title}. Stopping further posts in this run.")
             break # 如果中途失败，状态停留在上一个成功的 GUID
else:
    # 只有在非首次运行且确实没找到新帖子时才打印这条
    if last_posted_guid is not None:
         print(f"No new posts found with tag '{REQUIRED_TAG}' since the last run.")

print("Blog sync process finished.")