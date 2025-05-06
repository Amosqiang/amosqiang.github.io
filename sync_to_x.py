import os
import feedparser
import tweepy
import datetime
import time

# --- 配置 ---
# 从环境变量读取 Secrets
API_KEY = os.environ.get("X_API_KEY")
API_SECRET = os.environ.get("X_API_SECRET")
ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.environ.get("X_ACCESS_TOKEN_SECRET")

# 你的博客 RSS Feed URL (请确保这个地址是正确的)
RSS_FEED_URL = os.environ.get("RSS_FEED_URL", "https://amosqiang.github.io/feed.xml") 
# 用于存储上次发布文章 GUID 的文件路径
STATE_FILE_PATH = os.environ.get("STATE_FILE_PATH", "last_post_guid.txt") 

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
        # 使用 V2 API 需要 Client
        client = tweepy.Client(
            consumer_key=API_KEY, consumer_secret=API_SECRET,
            access_token=ACCESS_TOKEN, access_token_secret=ACCESS_TOKEN_SECRET
        )
        response = client.create_tweet(text=text)
        print(f"Tweet posted successfully! Tweet ID: {response.data['id']}")
        return True
    except tweepy.errors.TweepyException as e:
        print(f"Error posting tweet: {e}")
        # 检查是否是重复推文错误 (错误码 187 / 403 Forbidden)
        # tweepy.errors.Forbidden: 403 Forbidden / 187 - Status is a duplicate.
        if isinstance(e, tweepy.errors.Forbidden) and 'duplicate' in str(e).lower():
             print("Detected duplicate tweet. Skipping.")
             # 即使是重复错误，也可能意味着我们应该更新状态，
             # 以免下次再次尝试发送这个重复内容。
             # 这里需要谨慎处理，取决于你的逻辑。
             # 暂时按失败处理，不更新状态。
             return False 
        return False
    except Exception as e:
        print(f"An unexpected error occurred during tweeting: {e}")
        return False

# --- 主逻辑 ---
print("Starting blog sync process...")

last_posted_guid = get_last_posted_guid(STATE_FILE_PATH)
print(f"Last posted GUID from state file: {last_posted_guid}")

# 解析 RSS Feed
print(f"Fetching RSS feed from: {RSS_FEED_URL}")
feed = feedparser.parse(RSS_FEED_URL)

if feed.bozo:
    print(f"Error parsing RSS feed: {feed.bozo_exception}")
    exit(1)

if not feed.entries:
    print("No entries found in the RSS feed.")
    exit(0)

# RSS Feed 通常最新的条目在最前面
new_posts_to_tweet = []
for entry in reversed(feed.entries): # 从旧到新处理，确保按时间顺序发帖
    entry_guid = entry.get('guid', entry.get('link')) # 优先用 guid，没有则用 link
    entry_title = entry.title
    entry_link = entry.link

    # 检查是否已经发布过
    if last_posted_guid is None or entry_guid != last_posted_guid:
         # 如果状态文件是空的，只处理最新的一篇防止首次运行发大量推文
         if last_posted_guid is None and entry == feed.entries[-1]: 
             print(f"First run or state file empty. Processing latest entry: {entry_title}")
             new_posts_to_tweet.append((entry_guid, entry_title, entry_link))
         elif last_posted_guid is not None:
             # 检查这个 entry 是否比记录的更新 (注意：简单比较 GUID 可能不完美，如果 GUID 不稳定)
             # 更可靠的方式可能是比较发布时间，但需要处理时区
             # 这里我们假设 GUID 是稳定的，且 feed 是按时间排序的
             # 如果当前 entry 的 guid 不是上次记录的 guid，就认为它是新的
             # （注意：这种简单逻辑假设两次运行间不会产生大量文章，且 feed 顺序稳定）

             # 改进：找到上次发布的文章之后的所有文章
             # 需要更复杂的逻辑来处理 feed 中可能出现的顺序变化或条目丢失
             # 简单起见：如果 last_posted_guid 存在，我们找到它，然后处理它之后的所有条目

             # 重新设计简单逻辑：只处理比 last_posted_guid 更新的（假设 feed 从新到旧）
             # 这个逻辑在上面的 reversed() 循环里有点问题

             # 让我们改为不反转，从新到旧检查，直到找到上次发布的
             pass # 先留空，下面用另一种逻辑

    # else: # 如果 entry_guid == last_posted_guid
         # print(f"Found last posted entry ({entry_title}). Stopping check.")
         # break # 停止检查更旧的条目

# 新逻辑：从新到旧遍历，收集所有比 last_posted_guid 更新的条目
newest_guid_in_this_run = None
posts_found_since_last = []
found_last_posted = (last_posted_guid is None) # 如果没有记录，认为所有都是新的

for entry in feed.entries: # feed.entries 通常从新到旧排列
    entry_guid = entry.get('guid', entry.get('link'))
    entry_title = entry.title
    entry_link = entry.link

    if newest_guid_in_this_run is None:
         newest_guid_in_this_run = entry_guid # 记录本次运行看到的最新文章 GUID

    if entry_guid == last_posted_guid:
        print(f"Found the last posted entry GUID ({last_posted_guid}). No more new posts before this.")
        found_last_posted = True
        break # 找到了上次发的，停止处理更旧的

    if not found_last_posted:
        # 如果还没找到上次发的，说明当前这个是新的（或状态文件为空）
        posts_found_since_last.append((entry_guid, entry_title, entry_link))

if not posts_found_since_last and last_posted_guid is None and feed.entries:
    # 处理首次运行，只发最新的一篇
    latest_entry = feed.entries[0]
    entry_guid = latest_entry.get('guid', latest_entry.get('link'))
    entry_title = latest_entry.title
    entry_link = latest_entry.link
    print(f"First run detected. Preparing to post the latest entry: {entry_title}")
    posts_found_since_last.append((entry_guid, entry_title, entry_link))
    newest_guid_in_this_run = entry_guid # 确保状态被更新

if posts_found_since_last:
    print(f"Found {len(posts_found_since_last)} new post(s) to tweet.")
    # 反转列表，使得发帖顺序是从旧到新
    for guid, title, link in reversed(posts_found_since_last):
        tweet_text = f"New Post: {title} {link}"
        # 检查推文长度 (X 限制约为 280 字符)
        if len(tweet_text) > 280:
            # 尝试缩短标题
            available_len = 280 - len(f"New Post: ... {link}")
            if available_len > 0:
                tweet_text = f"New Post: {title[:available_len]}... {link}"
            else: # 如果链接本身就太长，可能无法发布
                print(f"Warning: Cannot shorten tweet sufficiently for '{title}'. Skipping.")
                continue # 跳过这篇

        print(f"Attempting to post: {tweet_text}")
        # 增加一点延迟，避免触发速率限制
        time.sleep(5) 
        if post_tweet(tweet_text):
             # 如果发帖成功，更新状态文件为刚刚成功发布的这篇的 GUID
             # 注意：如果一次运行要发多篇，只在最后一篇成功后更新状态可能更安全
             # 或者，每成功一篇就更新一次。这里选择每成功一篇更新一次。
             update_last_posted_guid(STATE_FILE_PATH, guid)
             # 等待更长时间，避免速率限制
             time.sleep(10) 
        else:
             print(f"Failed to post tweet for {title}. Stopping further posts in this run.")
             # 如果中途失败，不再尝试发送更新的文章，并保留上次成功的状态
             break 
else:
    print("No new posts found since the last run.")

# 如果本次运行有新文章（无论是否发布成功），确保状态文件至少更新到本次看到的最新文章的 GUID
# 这样下次运行时就不会再把它们当作新的了。
# （这个逻辑可能需要调整，如果发帖失败不应跳过）
# 修正逻辑：只有在所有预定推文都成功发布后，才更新到 newest_guid_in_this_run
# 目前的逻辑是每成功一篇就更新状态，如果最后一篇失败，状态会停留在倒数第二篇
# 这里不再额外更新，依赖 post_tweet 成功后的 update_last_posted_guid
if newest_guid_in_this_run and not posts_found_since_last:
     # 如果本次运行没有发现需要发的帖子，但 feed 里有内容，
     # 且状态文件为空，将状态更新为 feed 里最新的 GUID
     if last_posted_guid is None:
          print("Updating state file to the newest entry GUID on first successful check.")
          update_last_posted_guid(STATE_FILE_PATH, newest_guid_in_this_run)

print("Blog sync process finished.")