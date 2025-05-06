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
REQUIRED_TAG = os.environ.get("REQUIRED_TAG", "X") # 从环境变量读取标签，默认为 "X"

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
        return None # Treat as first run on error

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
        return "error" # 返回错误标识
    
    try:
        client = tweepy.Client(
            consumer_key=API_KEY, consumer_secret=API_SECRET,
            access_token=ACCESS_TOKEN, access_token_secret=ACCESS_TOKEN_SECRET
        )
        response = client.create_tweet(text=text)
        print(f"Tweet posted successfully! Tweet ID: {response.data['id']}")
        return "success" # 返回成功标识
    except tweepy.errors.TweepyException as e:
        print(f"Error posting tweet: {e}")
        # 特别检查 403 Forbidden 且是内容重复错误
        if isinstance(e, tweepy.errors.Forbidden) and 'duplicate content' in str(e).lower():
             print("Detected duplicate tweet via 403 Forbidden.")
             return "duplicate" # 返回重复标识
        # 可以添加对其他特定错误的处理，例如速率限制 (429)
        # elif isinstance(e, tweepy.errors.TooManyRequests): return "ratelimit"
        return "error" # 返回通用错误标识
    except Exception as e:
        print(f"An unexpected error occurred during tweeting: {e}")
        return "error" # 返回通用错误标识

# --- 主逻辑 ---
print("Starting blog sync process...")
print(f"Required tag for tweeting: '{REQUIRED_TAG}' (case-insensitive)")

last_posted_guid = get_last_posted_guid(STATE_FILE_PATH)
print(f"Last posted GUID from state file: {last_posted_guid}")

print(f"Fetching RSS feed from: {RSS_FEED_URL}")
feed = feedparser.parse(RSS_FEED_URL)

if feed.bozo:
    print(f"Error parsing RSS feed: {feed.bozo_exception}")
    exit(1) # 应该退出，避免上传错误的状态
if not feed.entries:
    print("No entries found in the RSS feed.")
    exit(0) # 正常退出

# --- 修订后的逻辑 ---
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

# --- 处理首次运行或状态丢失的情况 ---
latest_guid_to_save = None 
if last_posted_guid is None:
    print("First run (or state lost). Processing potentially found posts.")
    if posts_to_tweet: # posts_to_tweet 列表是按 Feed 中从新到旧顺序添加的
        # 从找到的带标签的潜在新帖子中，选出真正最新(列表第一个)的那个
        newest_tagged_post_data = posts_to_tweet[0] 
        print(f"First run: Selecting only the newest post with tag: '{newest_tagged_post_data['title']}'")
        posts_to_tweet = [newest_tagged_post_data] # 更新列表，只保留这一篇用于发布
        latest_guid_to_save = newest_tagged_post_data['guid'] # 标记这篇的 GUID 为最终要保存的状态
    else:
        # 如果首次运行没找到带标签的文章
        print(f"First run, but no posts found with the required tag '{REQUIRED_TAG}'.")
        if newest_guid_in_this_run:
             latest_guid_to_save = newest_guid_in_this_run 
             print(f"Will update state to newest overall post GUID found in feed ({latest_guid_to_save}) after run.")

# --- 发布推文 ---
final_state_updated = False # 标记状态文件是否在此次运行中被更新
if posts_to_tweet:
    print(f"Found {len(posts_to_tweet)} new post(s) with tag '{REQUIRED_TAG}' to tweet.")
    for post_data in reversed(posts_to_tweet): 
        guid = post_data['guid']
        title = post_data['title']
        link = post_data['link']
        
        tweet_text = f"{title} {link}" 
        if len(tweet_text) > 280:
            available_len = 280 - len(f"... {link}") 
            if available_len > 0:
                tweet_text = f"{title[:available_len]}... {link}" 
            else: 
                print(f"Warning: Cannot shorten tweet sufficiently for '{title}'. Skipping.")
                continue 

        print(f"Attempting to post: {tweet_text}")
        time.sleep(5) 
        
        post_result = post_tweet(tweet_text) 
        
        if post_result == "success" or post_result == "duplicate":
             # 如果成功 或 检测到是重复帖子，都更新状态文件
             if post_result == "duplicate":
                 print("Duplicate tweet detected by API. Updating state file as if successful.")
             
             if update_last_posted_guid(STATE_FILE_PATH, guid):
                 final_state_updated = True # 标记状态已更新
             else:
                 print("Error updating state file! Further tweets might be duplicated.")
                 # 即使状态文件写入失败，也可能需要停止，取决于策略
                 # break 
             
             # 如果只是检查到重复，可能不需要等那么久
             wait_time = 5 if post_result == "duplicate" else 10
             print(f"Waiting {wait_time} seconds...")
             time.sleep(wait_time) 
        
        elif post_result == "error": 
             print(f"Failed to post tweet for {title} due to API or other error. Stopping further posts in this run.")
             break # 遇到非重复错误，停止发布循环

else:
    if last_posted_guid is not None:
         print(f"No new posts found with tag '{REQUIRED_TAG}' since the last run.")

# 如果是首次运行且未找到可发布的帖子，但我们标记了要保存最新GUID
if not final_state_updated and last_posted_guid is None and latest_guid_to_save:
     print(f"Performing state update for first run (no tweets sent).")
     update_last_posted_guid(STATE_FILE_PATH, latest_guid_to_save)

print("Blog sync process finished.")

# 确保脚本最后有一个明确的退出码 (0表示成功)
# 如果在任何地方调用了 exit(1)，则工作流步骤会失败
# 这里我们假设如果脚本能运行到最后就是成功 (即使中间有推文失败但被处理了)
exit(0)