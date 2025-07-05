# Private Google Site Scraper

This project contains a robust Python script designed to perform a comprehensive scrape of a private Google Site protected by a full Google login, including 2-Factor Authentication (2FA).

It uses a hybrid "human-in-the-loop" workflow to handle the complex authentication and then proceeds with a fully automated, headless process to download all site content, including text, images, and embedded documents.

## Features

  * **Handles Complex Logins:** Opens a real browser for a user to handle manual login and 2FA, then captures the session cookies to automate the rest of the process.
  * **Full Site Crawl:** Automatically discovers and scrapes all internal pages linked from the homepage.
  * **Context-Aware Content Scraping:** Downloads all text, images, and documents while preserving the context of where they appeared on the page using placeholders.
  * **Downloads All Assets:**
      * Saves the text of each page to a separate `.md` file.
      * Downloads all images and saves them to a local `images` subfolder for each page.
      * Downloads embedded files like PDFs directly.
  * **Organized Output:** Creates a clean, structured folder hierarchy for the scraped content.

## The Workflow

The script operates in two main phases:

1.  **Headed Authentication:** A visible browser window is launched, allowing you to log in with your credentials and 2FA. The script extracts the necessary session cookies and then closes the browser.
2.  **Headless Scraping:** A new, invisible (headless) browser is launched in the background. It uses the captured cookies to run as an authenticated user, automatically navigating to every page to scrape and download content without further interaction.

## Project Structure

```
/Your_Project_Folder/
├── main.py                 # The main Python script
├── requirements.txt        # Project dependencies
└── output/                   # All scraped content is saved here
    ├── home/
    │   ├── content.md
    │   ├── some_document.pdf
    │   └── images/
    │       ├── image_1.jpg
    │       └── image_2.png
    └── another_page/
        ├── content.md
```

-----

## Setup and Installation

Follow these steps to set up the project on your local machine.

#### 1\. Clone or Download

Get the files (`main.py`, `requirements.txt`) and place them in your project folder.

#### 2\. Create a Python Environment

It is highly recommended to use a dedicated environment. If you are using Conda:

```bash
# Create a new environment with Python 3.11
conda create --name handbook_scraper python=3.11 -y

# Activate the environment
conda activate handbook_scraper
```

#### 3\. Install Dependencies

Install all required libraries from the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

#### 4\. Install Playwright Browsers

This is a crucial one-time step to download the browsers that the script will control.

```bash
playwright install
```

#### 5\. Configure the Script

Open the `main.py` file and update the configuration variables at the top to match your Google Site's URL.

```python
# --- Configuration ---
START_URL = "https://sites.google.com/your-domain.com/your-site-name/home"
BASE_DOMAIN = "sites.google.com/your-domain.com"
# ...
```

-----

## How to Run

1.  Open your terminal (Anaconda Prompt on Windows, or Terminal on macOS/Linux).
2.  Navigate to your project directory.
3.  Activate your Conda environment: `conda activate handbook_scraper`
4.  Run the script:
    ```bash
    python main.py
    ```
5.  A browser window will open. Complete the login process.
6.  Once you are logged in, the browser will close, and the script will automatically proceed with the headless scraping in your terminal. All content will be saved in the `output` folder.

## Troubleshooting

  * **Windows `NotImplementedError`:** The script contains a fix for a common `asyncio` issue on Windows. If you encounter this, ensure you are running the script from a standard terminal.
  * **Timeouts:** If the script fails due to timeouts, especially on the `page.goto` command, the default 90-second timeout may need to be increased for very slow-loading pages.
