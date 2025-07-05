# filename: main.py

import asyncio
import sys
import os
import re
import httpx
from playwright.async_api import async_playwright, TimeoutError
from urllib.parse import urljoin, unquote
import mimetypes
from bs4 import BeautifulSoup

# --- Configuration ---
START_URL = "https://sites.google.com/your-domain.com/your-site-name/home"
BASE_DOMAIN = "sites.google.com/your-domain.com"
OUTPUT_DIR = "output"

async def get_auth_cookies():
    """Launches a browser for login to get authentication cookies."""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    print("--- 👤 YOUR TURN: AUTHENTICATION ---")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(START_URL)
        print("Please complete the login process in the browser window...")
        try:
            await page.wait_for_url(f"**/{BASE_DOMAIN}/**", timeout=300000)
            print("✅ Login successful! Extracting session cookies...")
            cookies = await context.cookies()
            await browser.close()
            print("🔒 Headed browser closed. Authentication complete.")
            return cookies
        except TimeoutError:
            print("❌ Login timed out.")
            await browser.close()
            return None

async def download_file(session_cookies, file_url, save_dir, file_prefix):
    """
    Downloads a single file using a direct HTTP request and returns the saved filename.
    """
    # Skip embedded base64 data URLs
    if not file_url or file_url.startswith('data:image'):
        return None
        
    cookie_jar = httpx.Cookies()
    for cookie in session_cookies:
        cookie_jar.set(cookie['name'], cookie['value'], domain=cookie['domain'])

    try:
        async with httpx.AsyncClient(cookies=cookie_jar, follow_redirects=True, timeout=120.0) as client:
            response = await client.get(file_url)
            response.raise_for_status()

            filename = file_prefix # Default filename
            if 'content-disposition' in response.headers:
                disp_header = response.headers['content-disposition']
                fn_match = re.search(r'filename="([^"]+)"', disp_header, re.IGNORECASE)
                if fn_match:
                    filename = unquote(fn_match.group(1))
            else:
                content_type = response.headers.get("content-type", "")
                extension = mimetypes.guess_extension(content_type) or ""
                # Ensure filename has an extension
                if extension and not filename.endswith(extension):
                    filename = f"{filename}{extension}"

            filepath = os.path.join(save_dir, filename)
            with open(filepath, "wb") as f:
                f.write(response.content)
            return filename # Return the actual saved filename
            
    except Exception as e:
        print(f"      - Could not download {file_url}. Error: {e}")
    return None


async def scrape_site_headless(cookies, initial_links):
    """Launches a headless browser to scrape all pages."""
    print("\n--- 🤖 MY TURN: HEADLESS SCRAPING ---")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state={"cookies": cookies})

        for i, link_info in enumerate(initial_links):
            url_to_scrape = link_info['url']
            print(f"({i+1}/{len(initial_links)}) Scraping: {url_to_scrape}")
            page = await context.new_page()
            try:
                await page.goto(url_to_scrape, wait_until="load", timeout=90000)
                await page.wait_for_timeout(3000)

                page_output_dir = create_page_folder(page)
                images_dir = os.path.join(page_output_dir, "images")
                os.makedirs(images_dir, exist_ok=True)
                
                # Get HTML from the main page and all frames to parse together
                full_html = await page.content()
                for frame in page.frames:
                    try:
                        full_html += await frame.content()
                    except Exception: pass

                soup = BeautifulSoup(full_html, "lxml")
                
                doc_links_to_save_as_list = []
                
                # Process images and replace with placeholders
                print(f"    🖼️  Finding and downloading images...")
                image_counter = 0
                for img_tag in soup.find_all('img'):
                    src = img_tag.get('src')
                    if src and src.startswith('http'):
                        image_counter += 1
                        filename = f"image_{image_counter}"
                        saved_filename = await download_file(cookies, src, images_dir, filename)
                        if saved_filename:
                            placeholder = f"\n[IMAGE: {os.path.join('images', saved_filename)}]\n"
                            img_tag.replace_with(placeholder)

                # Process documents and replace with placeholders
                print(f"    📎 Finding and downloading documents...")
                doc_counter = 0
                for embed_div in soup.find_all('div', attrs={'data-embed-doc-id': True}):
                    doc_counter += 1
                    download_url = embed_div.get('data-embed-download-url')
                    open_url = embed_div.get('data-embed-open-url')
                    
                    if download_url:
                        saved_filename = await download_file(cookies, download_url, page_output_dir, f"document_{doc_counter}")
                        if saved_filename:
                            placeholder = f"\n[DOWNLOADED_DOCUMENT: {saved_filename}]\n"
                            embed_div.replace_with(placeholder)
                    elif open_url:
                        doc_links_to_save_as_list.append(open_url)
                        placeholder = f"\n[DOCUMENT_LINK: {open_url}]\n"
                        embed_div.replace_with(placeholder)
                
                # Get clean text from the modified HTML
                page_text = soup.get_text(separator='\n', strip=True)
                
                # Save the final processed content
                save_final_content(page_output_dir, page_text, doc_links_to_save_as_list)

            except Exception as e:
                print(f"    ❌ Failed to scrape {url_to_scrape}. Error: {e}")
            finally:
                if not page.is_closed():
                    await page.close()
        await browser.close()

def create_page_folder(page):
    title = page.url.split('/')[-1] or "home"
    folder_name = "".join(c for c in title if c.isalnum() or c in (' ', '_')).rstrip()
    page_output_dir = os.path.join(OUTPUT_DIR, folder_name)
    os.makedirs(page_output_dir, exist_ok=True)
    return page_output_dir

def save_final_content(page_dir, text, docs):
    content_path = os.path.join(page_dir, "content.md")
    with open(content_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"    📄 Saved content with placeholders to: {content_path}")

    if docs:
        docs_path = os.path.join(page_dir, "document_links.txt")
        with open(docs_path, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(list(set(docs)))))
        print(f"    🔗 Saved non-downloadable document links to: {docs_path}")

async def main():
    cookies = await get_auth_cookies()
    if not cookies:
        return
    print("\n--- 🤖 Getting initial links to scrape ---")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state={"cookies": cookies})
        page = await context.new_page()
        await page.goto(START_URL, wait_until="load")
        
        link_elements = await page.locator(f'a[href*="{BASE_DOMAIN}"], a[href^="/"]').all()
        internal_links = []
        for handle in link_elements:
            href = await handle.get_attribute('href')
            text = await handle.inner_text()
            if href:
                full_url = urljoin(START_URL, href)
                if not any(d['url'] == full_url for d in internal_links):
                    internal_links.append({"text": text.strip(), "url": full_url})
        await browser.close()
        if not any(d['url'] == START_URL for d in internal_links):
            internal_links.insert(0, {"text": "Home", "url": START_URL})
        print(f"✅ Found {len(internal_links)} internal pages to scrape.")

    if internal_links:
        await scrape_site_headless(cookies, internal_links)
    print("\n🎉 All tasks complete.")

if __name__ == "__main__":
    asyncio.run(main())