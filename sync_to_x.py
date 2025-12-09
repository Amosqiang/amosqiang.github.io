import os
import feedparser
import tweepy
import datetime
import time

# --- 配置 ---
# 从环境变量读取 Secrets 和配置
API_KEY = os.environ.get("X_API_KEY")
API_SECRET = os.environ.get("X_API_SECRET")
ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.environ.get("X_ACCESS_TOKEN_SECRET")

RSS_FEED_URL = os.environ.get("RSS_FEED_URL", "https://amosqiang.github.io/index.xml")
STATE_FILE_PATH = os.environ.get("STATE_FILE_PATH", "last_post_guid.txt") 
# 从环境变量读取标签，默认为 "X"
REQUIRED_TAG = os.environ.get("REQUIRED_TAG", "X") 
# 从环境变量读取推文格式，提供默认值
TWEET_FORMAT = os.environ.get("TWEET_FORMAT", "{title} {link}") 

# --- 函数 ---
def get_last_posted_guid(file_path):
    """从状态文件中读取上次发布的文章 GUID"""
    try:
        # 确保文件存在才读取
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                guid = f.read().strip()
                if guid: # 确保读取到的不是空字符串
                    return guid
                else:
                    print("State file is empty.")
                    return None
        else:
            print("State file not found, assuming first run.")
            return None
    except Exception as e:
        print(f"Error reading state file {file_path}: {e}")
        return None # 出错时也当作首次运行

def update_last_posted_guid(file_path, guid):
    """将最新的 GUID 写入状态文件"""
    try:
        with open(file_path, 'w') as f:
            f.write(guid)
        print(f"Updated state file with GUID: {guid}")
        return True
    except Exception as e:
        print(f"Error writing state file {file_path}: {e}")
        return False

def post_tweet(text):
    """使用 Tweepy V2 API 发布推文，处理重复错误并返回状态"""
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
print(f"Tweet format template: '{TWEET_FORMAT}'") 

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
# 假定 feed.entries[0] 是最新的文章
newest_guid_in_this_run = feed.entries[0].get('guid', feed.entries[0].get('link')) if feed.entries else None
posts_to_tweet = [] 
found_last_posted_marker = False 

for entry in feed.entries: # 遍历 Feed (通常从新到旧)
    entry_guid = entry.get('guid', entry.get('link'))
    # 如果 GUID 无效则跳过此条目
    if not entry_guid:
        print(f"Skipping entry with missing GUID/Link: {entry.title if hasattr(entry, 'title') else 'Untitled'}")
        continue
        
    entry_title = entry.title if hasattr(entry, 'title') else 'Untitled Post'
    entry_link = entry.link if hasattr(entry, 'link') else ''

    # 如果当前条目就是上次发布的条目，停止处理更旧的条目
    if entry_guid == last_posted_guid:
        print(f"Found the last posted entry GUID ({last_posted_guid}). Processing stops here.")
        found_last_posted_marker = True
        break 

    # 只处理在找到标记之前的条目（即 Feed 中更新的条目）
    # 检查这些更新的条目是否包含所需标签
    has_required_tag = False
    if hasattr(entry, 'tags') and isinstance(entry.tags, list):
        for tag_info in entry.tags:
            if hasattr(tag_info, 'term') and tag_info.term.lower() == REQUIRED_TAG.lower():
                has_required_tag = True
                break # 找到标签即可

    if has_required_tag:
        print(f"Found potential new post with required tag: '{entry_title}'")
        # 将符合条件的文章信息（以字典形式）加入列表
        posts_to_tweet.append({'guid': entry_guid, 'title': entry_title, 'link': entry_link})
    else:
         print(f"Skipping entry '{entry_title}' (either older or lacks required tag).")

# --- 处理首次运行或状态丢失的情况 ---
latest_guid_to_save = None # 用于记录首次运行时应该保存的 GUID
if last_posted_guid is None:
    print("First run (or state lost). Processing potentially found posts.")
    if posts_to_tweet: # posts_to_tweet 列表是按 Feed 中从新到旧顺序添加的
        # 从找到的带标签的潜在新帖子中，选出真正最新 (列表第一个) 的那个
        newest_tagged_post_data = posts_to_tweet[0] 
        print(f"First run: Selecting only the newest post with tag: '{newest_tagged_post_data['title']}'")
        posts_to_tweet = [newest_tagged_post_data] # 更新列表，只保留这一篇用于发布
        latest_guid_to_save = newest_tagged_post_data['guid'] # 标记这篇的 GUID 为最终要保存的状态
    else:
        # 如果首次运行没找到带标签的文章
        print(f"First run, but no posts found with the required tag '{REQUIRED_TAG}'.")
        if newest_guid_in_this_run:
             latest_guid_to_save = newest_guid_in_this_run # 标记要保存最新文章的 GUID
             print(f"Will attempt to update state to newest overall post GUID found in feed ({latest_guid_to_save}) after run.")

# --- 发布推文 ---
final_state_updated = False # 标记状态文件是否在此次运行中被更新
if posts_to_tweet:
    print(f"Found {len(posts_to_tweet)} new post(s) with tag '{REQUIRED_TAG}' to tweet.")
    # 按时间顺序发布（先发布旧的，所以要反转列表）
    for post_data in reversed(posts_to_tweet): 
        guid = post_data['guid']
        title = post_data['title']
        link = post_data['link']
        
        # 使用 TWEET_FORMAT 构建推文
        try:
            tweet_text = TWEET_FORMAT.format(title=title, link=link) 
        except KeyError as e:
            print(f"Error formatting tweet: Invalid placeholder {e} in TWEET_FORMAT '{TWEET_FORMAT}'. Skipping post '{title}'.")
            continue 

        # 检查长度 (简单截断整个字符串)
        if len(tweet_text) > 280:
            print(f"Warning: Tweet text exceeds 280 characters (length: {len(tweet_text)}). Truncating...")
            chars_to_keep = 280 - 3 # 为 "..." 留空间
            if chars_to_keep > 0:
                tweet_text = tweet_text[:chars_to_keep] + "..."
            else: 
                print(f"Error: Cannot truncate tweet, format string might be too long. Skipping post '{title}'.")
                continue 

        print(f"Attempting to post: {tweet_text}")
        time.sleep(5) 
        
        post_result = post_tweet(tweet_text) 
        
        if post_result == "success" or post_result == "duplicate":
             if post_result == "duplicate":
                 print("Duplicate tweet detected by API. Updating state file as if successful.")
             
             # 尝试更新状态文件
             if update_last_posted_guid(STATE_FILE_PATH, guid):
                 final_state_updated = True # 标记状态已更新
             else:
                 print("Error updating state file! Further tweets might be duplicated.")
                 # 如果状态文件写入失败，停止后续发布可能更安全
                 break 
             
             wait_time = 5 if post_result == "duplicate" else 10
             print(f"Waiting {wait_time} seconds...")
             time.sleep(wait_time) 
        
        elif post_result == "error": 
             print(f"Failed to post tweet for {title} due to API or other error. Stopping further posts in this run.")
             break # 遇到非重复错误，停止发布循环
else:
    # 只有在非首次运行且确实没找到新帖子时才打印这条
    if last_posted_guid is not None:
         print(f"No new posts found with tag '{REQUIRED_TAG}' since the last run.")

# 如果是首次运行且未找到可发布的帖子，但我们标记了要保存最新 GUID
# 并且状态文件还没有被任何成功的推文更新过
if not final_state_updated and last_posted_guid is None and latest_guid_to_save:
     print(f"Performing state update for first run (no tweets sent).")
     update_last_posted_guid(STATE_FILE_PATH, latest_guid_to_save)
     # 注意：这次写入是否会被后续的 Git 步骤捕捉到？是的，因为 git add 会在脚本运行后执行

print("Blog sync process finished.")
exit(0)