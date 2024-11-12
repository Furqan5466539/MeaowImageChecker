import os
import time
import re
import sys
import argparse
import json
import pickle
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import requests
from PIL import Image
from io import BytesIO

def load_topics():
    try:
        with open('topics.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print("Error: topics.json file not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: Invalid JSON in topics.json file.")
        sys.exit(1)

def get_topic_data(topic_id, topics):
    for topic in topics:
        if topic['id'] == topic_id:
            return topic
    return None

def save_cookies(driver, path):
    with open(path, 'wb') as filehandler:
        pickle.dump(driver.get_cookies(), filehandler)

def load_cookies(driver, path):
    with open(path, 'rb') as cookiesfile:
        cookies = pickle.load(cookiesfile)
        for cookie in cookies:
            driver.add_cookie(cookie)

def manual_login(driver):
    login_url = "https://x.com/login"
    driver.get(login_url)
    
    input("Please log in manually in the browser window. Press Enter when done...")
    
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[@aria-label='Profile']"))
        )
        print("Login successful")
        return True
    except Exception as e:
        print(f"Error confirming login: {e}")
        return False



def extract_image_urls(html_content):
    if not html_content:
        print("Error: No HTML content to parse.")
        return []

    image_urls = []
    
    # 特定のパターンにマッチする画像URLのみを抽出
    pattern = r'https://x\.com/([^/]+)/status/(\d+)/photo/1'
    matches = re.findall(pattern, html_content)
    
    for match in matches:
        username, status_id = match
        image_url = f"https://x.com/{username}/status/{status_id}/photo/1"
        if image_url not in image_urls:
            image_urls.append(image_url)
    
    print(f"Found {len(image_urls)} image URLs")
    for url in image_urls:
        print(f"  {url}")
    
    return image_urls

def save_image(url, save_dir, keyword):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # 画像データの検証
        image = Image.open(BytesIO(response.content))
        image.verify()
        
        content_type = response.headers.get('Content-Type', '')
        if 'jpeg' in content_type or 'jpg' in content_type:
            ext = 'jpg'
        elif 'png' in content_type:
            ext = 'png'
        elif 'gif' in content_type:
            ext = 'gif'
        else:
            ext = 'jpg'
        
        index = 1
        while True:
            filename = f"{keyword}_{index:03d}.{ext}"
            filepath = os.path.join(save_dir, filename)
            if not os.path.exists(filepath):
                break
            index += 1

        with open(filepath, 'wb') as f:
            f.write(response.content)
        print(f"Saved image: {filepath}")
        
        # 画像のサイズと形式を確認
        with Image.open(filepath) as img:
            print(f"Image size: {img.size}, Format: {img.format}")
        
        return True
    except requests.RequestException as e:
        print(f"Failed to download image {url}: {e}")
    except (IOError, SyntaxError) as e:
        print(f"Invalid image data from {url}: {e}")
    
    return False

def scroll_and_wait(driver, scroll_pause_time=2):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def slow_scroll(driver, scroll_pause_time=1):
    total_height = driver.execute_script("return document.body.scrollHeight")
    viewport_height = driver.execute_script("return window.innerHeight")
    scroll_step = viewport_height // 4  # Scroll quarter of a viewport at a time

    for scroll_position in range(0, total_height, scroll_step):
        driver.execute_script(f"window.scrollTo(0, {scroll_position});")
        time.sleep(scroll_pause_time)

def slow_scroll_and_extract(driver, max_scroll_attempts=1000):
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_attempts = 0
    image_urls = []
    consecutive_no_new_images = 0
    
    while scroll_attempts < max_scroll_attempts and consecutive_no_new_images < 10:
        # Extract images before scrolling
        current_images = extract_visible_images(driver)
        new_images = [img for img in current_images if img not in image_urls]
        if new_images:
            image_urls.extend(new_images)
            print(f"Found {len(new_images)} new images. Total: {len(image_urls)}")
            consecutive_no_new_images = 0
        else:
            consecutive_no_new_images += 1
        
        # Scroll a very small amount
        driver.execute_script("window.scrollBy(0, 100);")
        time.sleep(1)  # Increased wait time
        
        # Check for and click "Show probable spam" link
        if click_if_present(driver, "//span[contains(text(), 'Show probable spam')]"):
            consecutive_no_new_images = 0
        
        # Check for and click "Show additional replies" link
        if click_if_present(driver, "//span[contains(text(), 'Show additional replies')]"):
            consecutive_no_new_images = 0
        
        # Check if we've reached the bottom of the page
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            if consecutive_no_new_images >= 5:
                print("Reached the bottom of the page and no new images found")
                break
        else:
            consecutive_no_new_images = 0
        last_height = new_height
        scroll_attempts += 1
        
        if scroll_attempts % 10 == 0:
            print(f"Scrolled {scroll_attempts} times, found {len(image_urls)} images so far")
    
    print(f"Scrolling completed after {scroll_attempts} attempts")
    return image_urls

def click_show_additional_replies(driver):
    try:
        # テキストと'Show'リンクを正確に特定するための新しいXPath
        xpath = "//span[contains(text(), 'Show additional replies')]/ancestor::div[contains(@role, 'button')]/following-sibling::div[contains(@role, 'button')]//span[text()='Show']"
        link = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        driver.execute_script("arguments[0].click();", link)
        print("Clicked 'Show' link for additional replies")
        time.sleep(2)
        return True
    except (TimeoutException, NoSuchElementException, ElementClickInterceptedException) as e:
        #print(f"'Show' link for additional replies not found or not clickable: {e}")
        print(f"'Show' link for additional replies not found or not clickable")
        return False

def efficient_scroll_and_extract(driver, max_scroll_attempts=500):
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_attempts = 0
    image_urls = []
    consecutive_no_new_images = 0
    show_spam_clicked = False
    
    while scroll_attempts < max_scroll_attempts and consecutive_no_new_images < 20:
        # Extract images before scrolling
        current_images = extract_visible_images(driver)
        new_images = [img for img in current_images if img not in image_urls]
        if new_images:
            image_urls.extend(new_images)
            print(f"Found {len(new_images)} new images. Total: {len(image_urls)}")
            consecutive_no_new_images = 0
        else:
            consecutive_no_new_images += 1
        
        # Scroll by a full viewport height
        driver.execute_script("window.scrollBy(0, window.innerHeight);")
        time.sleep(1)
        
        # Check for and click "Show probable spam" link only once
        if not show_spam_clicked:
            if click_if_present(driver, "//span[contains(text(), 'Show probable spam')]"):
                show_spam_clicked = True
                consecutive_no_new_images = 0
        
        # Check for and click "Show" link for additional replies
        if click_show_additional_replies(driver):
            consecutive_no_new_images = 0
        else:
            # If "Show" link is not found after clicking "Show probable spam",
            # and no new images are found, consider ending the process
            if show_spam_clicked and consecutive_no_new_images > 5:
                print("No 'Show' link found for additional replies after 'Show probable spam'. Ending process.")
                break
        
        # Check if we've reached the bottom of the page
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            if consecutive_no_new_images >= 10:
                print("Reached the bottom of the page and no new images found")
                break
        else:
            consecutive_no_new_images = 0
        last_height = new_height
        scroll_attempts += 1
        
        if scroll_attempts % 10 == 0:
            print(f"Scrolled {scroll_attempts} times, found {len(image_urls)} images so far")
    
    print(f"Scrolling completed after {scroll_attempts} attempts")
    return image_urls

def click_if_present(driver, xpath):
    try:
        element = WebDriverWait(driver, 1).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        driver.execute_script("arguments[0].click();", element)
        print(f"Clicked '{xpath}'")
        time.sleep(2)
        return True
    except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
        return False

def extract_visible_images(driver):
    js_script = """
    function getVisibleImageUrls() {
        var urls = [];
        var elements = document.querySelectorAll('[data-testid="tweetPhoto"], [data-testid="tweetImageContainer"]');
        elements.forEach(function(el) {
            var rect = el.getBoundingClientRect();
            if (rect.top < window.innerHeight * 2 && rect.bottom >= -window.innerHeight) {
                var img = el.querySelector('img');
                if (img && img.src && img.src.includes('https://pbs.twimg.com/media/')) {
                    urls.push(img.src.replace('&name=small', '&name=large').replace('&name=medium', '&name=large'));
                }
            }
        });
        return urls;
    }
    return getVisibleImageUrls();
    """
    return driver.execute_script(js_script)

def get_tweet_data(post_id, username, cookies_path):
    url = f"https://x.com/{username}/status/{post_id}"
    
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--disable-extensions")
    
    driver = uc.Chrome(options=options)
    
    try:
        driver.get("https://x.com")
        
        if os.path.exists(cookies_path):
            load_cookies(driver, cookies_path)
            driver.refresh()
        else:
            if not manual_login(driver):
                return None, None, []
            save_cookies(driver, cookies_path)
        
        driver.get(url)
        print(f"Successfully loaded page: {url}")
        
        # Initial wait for the page to load
        time.sleep(10)
        
        # Perform scrolling and image extraction
        image_urls = efficient_scroll_and_extract(driver)
        
        print(f"Found {len(image_urls)} unique image URLs")
        for i, url in enumerate(image_urls):
            print(f"Image {i+1}: {url}")
        
        page_source = driver.page_source
        print(f"Page source length: {len(page_source)} characters")
        
        return page_source, driver.current_url, image_urls
    except Exception as e:
        print(f"Error fetching tweet data: {e}")
        return None, None, []
    finally:
        driver.quit()

def get_reply_images(topic_id, username, topics, cookies_path):
    topic_data = get_topic_data(topic_id, topics)
    if not topic_data:
        print(f"Error: Topic ID {topic_id} not found in topics.json")
        return

    keyword = topic_data['keyword']
    post_id = topic_data['post_id']

    print(f"Processing topic: {keyword} (ID: {topic_id})")
    print(f"Post ID: {post_id}")

    html_content, current_url, image_urls = get_tweet_data(post_id, username, cookies_path)
    if not html_content or not current_url:
        print("Error: Failed to retrieve tweet data.")
        return

    if not image_urls:
        print("No images found in the tweet.")
        print("Debugging information:")
        print(f"HTML content length: {len(html_content)}")
        return

    save_dir = os.path.join("images", keyword)
    os.makedirs(save_dir, exist_ok=True)
    
    successful_downloads = 0
    for url in image_urls:
        if save_image(url, save_dir, keyword):
            successful_downloads += 1
        time.sleep(1)
    
    print(f"Successfully downloaded {successful_downloads} out of {len(image_urls)} images.")

def main():
    load_dotenv()
    username = os.getenv('TWITTER_USERNAME')
    
    if not username:
        print("Error: TWITTER_USERNAME not found in .env file")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Scrape images from X.com replies.")
    parser.add_argument("topic_id", type=int, help="The Topic ID")
    args = parser.parse_args()

    cookies_path = 'twitter_cookies.pkl'
    topics = load_topics()
    get_reply_images(args.topic_id, username, topics, cookies_path)

if __name__ == "__main__":
    main()