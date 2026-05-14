from playwright.async_api import async_playwright
import pandas as pd
import os
import re
import random
import asyncio
import nest_asyncio
import json

# Cookies if necessary
cookies_string = """[COOKIES]"""

# Configuration of file paths and main scraping function
progress_file = r"C:\Code\clean_df_progress_save.csv"
initial_file = r"C:\Code\kickstarter_combined_clean_no_faulty_no_duplicates.csv"

# Start index of dataframe subset to process and width of the subset to process
# Each of these can be adjusted to control which portion of the data is processed in each run, allowing for progress saving and resuming
start_idx = 0
end_idx = start_idx + 10

# Function to extract slug from Kickstarter URL
def extract_slug(url):
    match = re.search(r"kickstarter\.com/projects/([^/]+/[^/?#]+)", url)
    return match.group(1) if match else None

# Fetches the project story, risks, and rewards HTML from a Kickstarter URL using Playwright
async def fetch_story_with_playwright(url, cookies_string = cookies_string):
    story_html = None
    risks_html = None
    rewards_html = None

    try:
        async with async_playwright() as p:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=user_agent)

            try:
                cookies_list = json.loads(cookies_string)
                cleaned_cookies = []
                for cookie in cookies_list:
                    if 'sameSite' in cookie and cookie['sameSite'] == 'no_restriction':
                        cookie['sameSite'] = 'None'
                    elif 'sameSite' in cookie and cookie['sameSite'] == 'unspecified':
                        del cookie['sameSite']

                    if 'name' in cookie and 'value' in cookie and 'domain' in cookie and 'path' in cookie:
                        cleaned_cookies.append(cookie)
                    else:
                        print(f"Skipping malformed cookie: {cookie}")


                await context.add_cookies(cleaned_cookies)
                print("Cookies loaded into browser context.")
            except Exception as e:
                print(f"Failed to load cookies: {e}")

            page = await context.new_page()

            # Small random delay before navigation
            await asyncio.sleep(random.uniform(2, 5))

            try:
                await page.goto(url, timeout=90000)
                print(f"Page loaded successfully for {url}")
            except Exception as e:
                print(f"Navigation failed for {url}: {e}")
                await browser.close()
                return {"story_html": "Navigation failed", "risks_html": "Navigation failed", "rewards_html": "Navigation failed"}

            # Delay after navigation to allow dynamic content/checks to load
            await asyncio.sleep(random.uniform(5, 10))

            # Print the page title and URL after navigation
            print(f"Page Title: {await page.title()}")
            print(f"Page URL: {page.url}")

            # Wait for a common element that indicates the page is loaded
            try:
                await page.wait_for_selector("h1", timeout=15000)
                print("Project title element found.")
            except Exception as e:
                print(f"Project title element not found: {e}")

            # Multiple selectors for the story content
            story_selectors = [
                "#story-container",
                "div#story-container",
                "section#story-container",
                "div.rte__content",
                "div[data-test-id='campaign-description']",
                ".full-description",
                "#project-description",
                "div.full-description",
                "#description",
                ".desc",
                "div.grid-col-10",
                "div.mx-auto",
                "section.mb5"
            ]

            for sel in story_selectors:
                try:
                    await page.wait_for_selector(sel, timeout=20000)
                    story_html = await page.inner_html(sel)
                    if story_html and len(story_html.strip()) > len("<div></div>"):
                        print(f"Story content found using selector '{sel}'. Length: {len(story_html)}")
                        break
                    else:
                        print(f"Selector '{sel}' found, but returned empty or minimal content.")
                except Exception as e:
                    print(f"Selector '{sel}' not found or failed to load: {e}")
                    continue

            # Multiple selectors for the risks content
            risks_selectors = [
                #"div#risks-and-challenges.mb3.mb10-sm.js-risks"
                #"#risks",
                #"section#risks",
                #"div#risks",
                #"div#risks-and-challenges",
                #"section#risks-and-challenges",
                #"[data-test-id='risks']",
                #"div[data-test-id='risks']",
                #"section[data-test-id='project-risks']",
                #"article#risks-and-challenges",
                #"section[data-anchor='risks-and-challenges']",
                #"div[data-anchor='risks-and-challenges']",
                "div.js-risks",
                "div[data-test-id='risks-and-challenges']",
                "section[data-test-id='risks-and-challenges']",
                "div[data-section='risks']",
                "#risks-and-challenges",
                "div.px3-sm.px5-lg.col-sm-12.col-lg-10.mx-auto.mb5"
            ]
            for sel in risks_selectors:
                try:
                    await page.wait_for_selector(sel, timeout=10000)
                    risks_html = await page.inner_html(sel)
                    if risks_html and len(risks_html.strip()) > len("<div></div>"):
                        print(f"Risks content found using selector '{sel}'. Length: {len(risks_html)}")
                        break
                    else:
                        print(f"Selector '{sel}' for risks found, but returned empty or minimal content.")
                except Exception as e:
                    print(f"Selector '{sel}' for risks not found or failed: {e}")
                    continue

            # Multiple selectors for the rewards content
            rewards_selectors = [
                ".sticky-rewards",
                "div.js-project-rewards",
                "div.js-rewards",
                "[data-test-id='rewards']",
                "div[data-test-id='rewards']",
                "#rewards",
                ".NS_projects__rewards_list",
                "div.RewardsSection",
                "section.rewards-module",
                "div.ReactModal__Content",
                "div.bg-white.py3.py0-lg.col-full.col-lg-12",
                "div.RewardsSection-container",
                "div.backed-project-modal",
                "section.rewards-section",
                "div.pledge--wrapper",
                "div.RewardsTable-component",
                "ul.NS-rewards",
                "div.reward",
                "div[class*='reward']",
                "div[id*='reward']",
                "div.NS-rewards-container",
                "div[data-rewards-list]"
            ]
            for sel in rewards_selectors:
                try:
                    await page.wait_for_selector(sel, timeout=15000)
                    rewards_html = await page.inner_html(sel)
                    if rewards_html and len(rewards_html.strip()) > len("<div></div>"):
                        print(f"Rewards content found using selector '{sel}'. Length: {len(rewards_html)}")
                        break
                    else:
                        print(f"Selector '{sel}' for rewards found, but returned empty or minimal content.")
                except Exception as e:
                    print(f"Selector '{sel}' for rewards not found or failed: {e}")
                    continue

            await browser.close()

    except Exception as e:
        print(f"Playwright failed to fetch data for {url}: {e}")
        return {"story_html": "General Playwright error", "risks_html": "General Playwright error", "rewards_html": "General Playwright error"}

    return {
        "story_html": story_html or "Story content not found",
        "risks_html": risks_html or "Risks content not found",
        "rewards_html": rewards_html or "Rewards content not found"
    }

# Main function to fetch stories for a DataFrame of Kickstarter projects, with progress saving and error handling
async def fetch_stories_for_dataframe(df, slug_column="slug", story_column_name="story_html", risks_column_name="risks_html", rewards_column_name="rewards_html", parent_df=None, parent_save_path=None):
    # List of errors that trigger a refetch attempt
    specific_error_messages = [
        "Error or not found",
        "Navigation failed",
        "General Playwright error",
        "Story content not found",
        "Risks content not found",
        "Rewards content not found",
        "<div></div>",
        """<a href="/?ref=nav" class="max-w40 global-nav-ksr-logo"><svg width="100%" viewBox="0 0 181 20" fill="none" xmlns="http://www.w3.org/2000/svg" class="valign-middle" aria-label="Kickstarter"><title>Kickstarter</title><path class="fill-ksr10-green" fill-rule="evenodd" clip-rule="evenodd" d="M16.9257 15.2442C16.9257 14.3321 16.6731 13.4527 16.1362 12.6709L14.1153 9.77192L16.1362 6.87291C16.6731 6.12373 16.9257 5.21169 16.9257 4.29964C16.9257 1.88924 14.9994 0.0325731 12.7258 0.0325731C11.3996 0.0325731 10.0733 0.716607 9.25228 1.88924L8.24179 3.32245C7.86286 1.40064 6.2524 0 4.19984 0C1.83151 0 0 1.95438 0 4.36479V15.2768C0 17.6872 1.86309 19.6416 4.19984 19.6416C6.22082 19.6416 7.79971 18.3386 8.21022 16.4494L9.09439 17.7523C9.91541 18.9901 11.2733 19.6416 12.5995 19.6416C14.9994 19.6741 16.9257 17.6546 16.9257 15.2442ZM18.1794 4.6984C18.1794 2.15344 20.2063 0 22.7399 0C25.2735 0 27.3004 2.15344 27.2688 4.6984V14.9435C27.2688 17.4885 25.2735 19.6419 22.7082 19.6419C20.2063 19.6419 18.1794 17.5211 18.1794 14.9435V4.6984ZM44.8219 14.2437C44.8219 12.1624 43.8247 10.699 41.8304 9.82097C43.8247 8.94294 44.8219 7.51207 44.8219 5.39828C44.8219 2.24386 42.2979 0 38.247 0C32.825 0 28.8365 4.19505 28.8365 9.82097C28.8365 15.4469 32.825 19.6419 38.247 19.6419C42.2979 19.6419 44.8219 17.3981 44.8219 14.2437ZM62.5236 12.6709C63.0614 13.4527 63.3145 14.3321 63.3145 15.2442C63.3145 17.6546 61.3846 19.6741 59.0119 19.6416C57.6831 19.6416 56.3228 18.9901 55.5002 17.7523L54.6144 16.4494C54.2031 18.3386 52.6213 19.6416 50.5965 19.6416C48.2554 19.6416 46.3888 17.6872 46.3888 15.2768V4.36479C46.3888 1.95438 48.2237 0 50.5965 0C52.6529 0 54.2664 1.40064 54.646 3.32245L55.6268 1.88924C56.4493 0.716607 57.7781 0.0325731 59.1068 0.0325731C61.3846 0.0325731 63.3145 1.88924 63.3145 4.29964C63.3145 5.21169 63.0614 6.12373 62.5236 6.87291L60.4988 9.77192L62.5236 12.6709ZM79.3001 13.5975C79.3001 11.6269 78.3578 10.2474 76.9444 8.93364L75.7822 7.84978C77.4783 7.58702 78.6091 6.40463 78.6091 4.66389C78.6091 1.74075 76.379 0 71.6676 0C67.0504 0 64.3493 2.43048 64.3493 6.27325C64.3493 8.24391 65.3229 9.59052 66.7364 10.9371L67.8671 12.021H67.8357C65.7313 12.021 64.255 13.3019 64.255 15.3054C64.255 18.1957 66.5793 19.9693 71.542 19.9693C76.4104 19.9693 79.3001 17.506 79.3001 13.5975ZM103.096 16.2274C104.166 18.5363 105.675 19.6419 107.531 19.6419C110.865 19.6419 113.224 16.4875 111.777 12.9429L107.908 3.57717C106.965 1.26827 105.55 0 103.128 0C100.738 0 99.3222 1.26827 98.3472 3.57717L94.4787 12.9429C93.0005 16.4875 95.3908 19.6419 98.6932 19.6419C100.517 19.6419 102.027 18.5363 103.096 16.2274ZM113.465 5.2049C113.465 1.99671 115.107 0.327148 118.045 0.327148H123.509C126.826 0.327148 129.416 2.94607 129.416 6.31794C129.416 8.15119 128.69 9.65707 127.489 10.6064L129.132 13.3236C129.574 14.0438 129.764 14.8295 129.764 15.6479C129.764 18.0704 127.931 19.9691 125.626 19.9691C124.204 19.9691 122.814 19.2162 122.025 17.8412L121.583 17.0228C121.046 18.7578 119.561 19.9691 117.666 19.9691C115.36 19.9691 113.465 17.9394 113.465 15.4842V5.2049ZM138.32 19.9691C140.922 19.9691 142.865 17.9722 142.865 15.5497V8.77318C144.965 8.67498 146.689 6.84173 146.689 4.55017C146.689 2.19313 144.871 0.327148 142.646 0.327148H134.12C131.895 0.327148 130.077 2.1604 130.077 4.55017C130.077 6.84173 131.801 8.64224 133.901 8.77318V15.5497C133.901 17.9722 135.875 19.9691 138.32 19.9691ZM159.934 12.5742C161.522 12.9043 162.675 14.3238 162.675 16.2054C162.675 18.3181 161.055 20.0016 159.093 19.9686H152.552C149.562 19.9686 147.943 18.3181 147.943 15.083V5.21276C147.943 2.0107 149.562 0.327148 152.552 0.327148H159.093C161.055 0.327148 162.675 2.0107 162.675 4.1234C162.675 6.03803 161.553 7.42449 159.934 7.75459C160.681 8.24976 161.086 9.07503 161.086 10.1644C161.086 11.2537 160.65 12.079 159.934 12.5742ZM168.13 19.9691C165.824 19.9691 163.929 17.9394 163.929 15.4842V5.2049C163.929 1.99671 165.54 0.327148 168.509 0.327148H173.973C177.29 0.327148 179.88 2.94607 179.88 6.31794C179.88 8.15119 179.153 9.65707 177.953 10.6064L179.596 13.3236C180.038 14.0438 180.227 14.8295 180.227 15.6479C180.227 18.0704 178.395 19.9691 176.09 19.9691C174.668 19.9691 173.278 19.2162 172.489 17.8412L172.046 17.0228C171.509 18.7578 170.025 19.9691 168.13 19.9691ZM92.0807 15.5497C92.0807 17.9722 90.1023 19.9691 87.5587 19.9691C85.1092 19.9691 83.1308 17.9722 83.1308 15.5497V8.77318C81.0268 8.64224 79.2997 6.84173 79.2997 4.55017C79.2997 2.1604 81.121 0.327148 83.3507 0.327148H91.8609C94.0905 0.327148 95.9119 2.19313 95.9119 4.55017C95.9119 6.84173 94.1847 8.67498 92.0807 8.77318V15.5497Z"></path></svg></a><div class="flex items-center text-center pl2 global-nav-search w100p max-w110"><svg class="kds-icon shrink0 kds-fill-icon" style="width: 24px; aspect-ratio: 1 / 1;"><use xlink:href="#icon--search.kds"></use></svg><div class="w100p inline-block"><div class="relative smart-input-group"><input class="atomic-text-input border-none" id="global-nav-search-input" placeholder="Search projects, creators, and categories" type="text" value="" style="border-radius: 8px;"></div><div class="relative w100p"><div class="h5 clip absolute l0 t0 w100p"><div class="absolute l0 t1 w100p"></div></div></div></div><div class="global-nav-search-results flex display-grid max-h50vh justify-center absolute z-dropdown-2 l0 w100p scroll-y webkit-scrolling"><div class="max-w110"></div></div></div><section class="flex justify-start items-center global-nav-user-menu"><a class="kds-button kds-button" data-rac="" data-variant="outlined" href="/creators?ref=nav">For creators</a><a href="/login?ref=nav" class="soft-black hover-ksr-green-700 ml3 mr3 mr0-lg type-16">Log in</a></section>""",
        """<div class="mobile-show py3"></div><h2 class="normal mb4">Risks and challenges</h2><p class="js-risks-text text-preline"></p><a target="_blank" class="ksr-green-700 bold type-16" href="/help/hc/sections/115001107133">Learn about accountability on Kickstarter</a>"""
    ]

    if slug_column not in df.columns:
        print(f"Error: Slug column '{slug_column}' not found in DataFrame.")
        return df

    # Initialize the new story, risks, and rewards columns if they don't exist
    for col_name in [story_column_name, risks_column_name, rewards_column_name]:
        if col_name not in df.columns:
            df[col_name] = None

    # Identify rows with missing or error-related scraped content
    condition = df[story_column_name].isna()
    for msg in specific_error_messages:
        condition = condition | (df[story_column_name] == msg)
    condition = condition | (df[story_column_name].astype(str).str.startswith("Error or not found:", na=False))

    condition = condition | df[risks_column_name].isna()
    for msg in specific_error_messages:
        condition = condition | (df[risks_column_name] == msg)
    condition = condition | (df[risks_column_name].astype(str).str.startswith("Error or not found:", na=False))

    condition = condition | df[rewards_column_name].isna()
    for msg in specific_error_messages:
        condition = condition | (df[rewards_column_name] == msg)
    condition = condition | (df[rewards_column_name].astype(str).str.startswith("Error or not found:", na=False))

    slugs_to_process = df[condition][slug_column].dropna().unique().tolist()

    print(f"Attempting to fetch content for {len(slugs_to_process)} unique slugs that are missing data or have error messages.")

    if not slugs_to_process:
        print("No slugs to process or all content already fetched successfully.")
        return df

    batch_size = 5
    total_batches = (len(slugs_to_process) + batch_size - 1) // batch_size

    for i in range(0, len(slugs_to_process), batch_size):
        batch_slugs = slugs_to_process[i : i + batch_size]
        print(f"Processing batch {i // batch_size + 1}/{total_batches}...")
        tasks = []
        for slug in batch_slugs:
            url = f"https://www.kickstarter.com/projects/{slug}"
            tasks.append(fetch_story_with_playwright(url, cookies_string))

        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Update the DataFrame incrementally after each batch
        for slug, result in zip(batch_slugs, batch_results):
            # Find the indices in the original DataFrame for this slug
            indices_to_update = df.index[df[slug_column] == slug]

            if isinstance(result, dict):
                # Update the specified columns with the fetched data
                df.loc[indices_to_update, story_column_name] = result.get("story_html", "Error or not found")
                df.loc[indices_to_update, risks_column_name] = result.get("risks_html", "Error or not found")
                df.loc[indices_to_update, rewards_column_name] = result.get("rewards_html", "Error or not found")
            else:
                error_str = str(result) if isinstance(result, Exception) else "Error or not found"
                df.loc[indices_to_update, story_column_name] = f"Error or not found: {error_str}"
                df.loc[indices_to_update, risks_column_name] = f"Error or not found: {error_str}"
                df.loc[indices_to_update, rewards_column_name] = f"Error or not found: {error_str}"
                print(f"Failed to fetch or error for slug {slug}: {result}")

        if parent_df is not None:
            try:
                for col in [story_column_name, risks_column_name, rewards_column_name]:
                    parent_df.loc[df.index, col] = df[col]
                print(f"Parent DataFrame updated in-memory for batch {i // batch_size + 1}.")
            except Exception as e:
                print(f"Failed to update parent_df in-memory after batch: {e}")

        # Save progress after each batch to avoid data loss in case of interruptions
        try:
            if parent_df is not None and parent_save_path:
                parent_df.to_csv(parent_save_path, index=False)
                print(f"Parent DataFrame (full dataset) saved to {parent_save_path} after batch {i // batch_size + 1}")
            else:
                # No parent to update: write subset progress to a distinct file to avoid overwriting the full CSV
                if isinstance(save_path, str):
                    subset_save = save_path.replace('.csv', '_subset_progress.csv')
                    df.to_csv(subset_save, index=False)
                    print(f"Subset progress saved to {subset_save} after batch {i // batch_size + 1}")
                else:
                    print("No valid save path available to persist progress.")
        except Exception as save_e:
            print(f"Error saving progress: {save_e}")
            
    try:
        subset_save = save_path.replace('.csv', '_subset_progress.csv') if isinstance(save_path, str) else None
        if subset_save and os.path.exists(subset_save):
            os.remove(subset_save)
            print(f"Removed temporary subset file: {subset_save}")
    except Exception as rm_e:
        print(f"Failed to remove subset file {subset_save}: {rm_e}")

    print("Finished fetching content.")
    return df

# main scraping function that loads the DataFrame, identifies which slugs need processing, and runs the scraper on a subset of the data with progress saving
def scrape(clean_df, save_path, start_idx, end_idx):
    # Display the first few rows to verify it loaded correctly
    print("DataFrame loaded from CSV:")
    print(clean_df.head())
    print(len(clean_df))

    # Display a sample of slugs
    print("Sample of slugs:")
    print(clean_df['slug'].dropna().sample(20) if len(clean_df['slug'].dropna()) >= 20 else clean_df['slug'].dropna().head())

    # Check for slugs that might be profile URLs or other invalid formats
    invalid_slug_patterns = clean_df[clean_df['slug'].dropna().str.startswith('profile/')]
    print(f"\nNumber of slugs starting with 'profile/': {len(invalid_slug_patterns)}")

    # Check for slugs that don't contain a '/' which might indicate they are not in the expected "creator/project" format
    single_part_slugs = clean_df[~clean_df['slug'].dropna().str.contains('/')]
    print(f"Number of slugs without a '/': {len(single_part_slugs)}")

    # Display some of the potentially invalid slugs
    if not invalid_slug_patterns.empty:
        print("\nSample of slugs starting with 'profile/':")
        print(invalid_slug_patterns['slug'].head())

    if not single_part_slugs.empty:
        print("\nSample of slugs without a '/':")
        print(single_part_slugs['slug'].head())

    clean_df["slug"] = clean_df["urls_web_project"].apply(extract_slug)

    print("Sample of updated slugs:")
    print(clean_df['slug'].dropna().sample(20) if len(clean_df['slug'].dropna()) >= 20 else clean_df['slug'].dropna().head())

    # Ensure the necessary columns exist
    required_scrape_cols = ['story_html', 'risks_html', 'rewards_html']
    for col in required_scrape_cols:
        if col not in clean_df.columns:
            clean_df[col] = None
            print(f"Column '{col}' not found, created with None values.")

    # List of specific error messages
    specific_error_messages = ["Navigation failed", "General Playwright error", "Story content not found", "Risks content not found", "Rewards content not found"]

    # Define the condition to select slugs for processing
    condition = clean_df['story_html'].isna()
    for msg in specific_error_messages:
        condition = condition | (clean_df['story_html'] == msg)
    
    # Add condition for messages starting with "Error or not found: "
    condition = condition | (clean_df['story_html'].astype(str).str.startswith("Error or not found:", na=False))

    for col_name in ['risks_html', 'rewards_html']:
        condition = condition | clean_df[col_name].isna()
        for msg in specific_error_messages:
            condition = condition | (clean_df[col_name] == msg)
        # Add condition for messages starting with "Error or not found: " to other columns as well
        condition = condition | (clean_df[col_name].astype(str).str.startswith("Error or not found:", na=False))

    # Select the slugs based on the condition
    slugs_to_process_check = clean_df[condition]['slug'].dropna().unique().tolist()

    print(f"Number of unique slugs identified for processing by the current filter: {len(slugs_to_process_check)}")

    # Display a sample of these slugs and their corresponding story_html to verify the filter
    if len(slugs_to_process_check) > 0:
        print("\nSample of slugs and story_html identified for processing:")
        # Get the rows for the identified slugs and display relevant columns
        sample_df = clean_df[clean_df['slug'].isin(slugs_to_process_check)].head(20) # Displaying first 20 for check
        print(sample_df[['slug', 'story_html', 'risks_html', 'rewards_html']])
    else:
        print("No slugs were identified for processing based on the current filter conditions.")

    print(clean_df.head(10))

    try:
        subset_to_process = clean_df.iloc[start_idx:end_idx]
        # Run scraper on subset
        asyncio.run(
            fetch_stories_for_dataframe(
                subset_to_process,
                parent_df=clean_df,
                parent_save_path=save_path
            )
        )
    except Exception as e:
        print(f"Error while processing subset: {e}")
    finally:
        try:
            clean_df.to_csv(save_path, index=False)
            print(f"Full DataFrame with subset updates saved to {save_path}")
        except Exception as save_e:
            print(f"Error saving full DataFrame to {save_path}: {save_e}")

    print("Finished fetching content for the subset.")

    # lenth of dataframe
    print(f"Length of clean_df after update: {len(clean_df)} rows")

    scraped_subset_df = clean_df[start_idx:end_idx].copy()

    print(f"Analysis of Scraped Subset (Rows {start_idx}-{end_idx})")

    # Define the list of specific error messages to consider for refetching
    specific_error_messages = [
        "Error or not found",
        "Navigation failed",
        "General Playwright error",
        "Story content not found",
        "Risks content not found",
        "Rewards content not found",
        """<h2 id="story" class="normal mb3 mb7-sm mobile-hide page-anchor">Story</h2>"""
        """<a href="/?ref=nav" class="max-w40 global-nav-ksr-logo"><svg width="100%" viewBox="0 0 181 20" fill="none" xmlns="http://www.w3.org/2000/svg" class="valign-middle" aria-label="Kickstarter"><title>Kickstarter</title><path class="fill-ksr10-green" fill-rule="evenodd" clip-rule="evenodd" d="M16.9257 15.2442C16.9257 14.3321 16.6731 13.4527 16.1362 12.6709L14.1153 9.77192L16.1362 6.87291C16.6731 6.12373 16.9257 5.21169 16.9257 4.29964C16.9257 1.88924 14.9994 0.0325731 12.7258 0.0325731C11.3996 0.0325731 10.0733 0.716607 9.25228 1.88924L8.24179 3.32245C7.86286 1.40064 6.2524 0 4.19984 0C1.83151 0 0 1.95438 0 4.36479V15.2768C0 17.6872 1.86309 19.6416 4.19984 19.6416C6.22082 19.6416 7.79971 18.3386 8.21022 16.4494L9.09439 17.7523C9.91541 18.9901 11.2733 19.6416 12.5995 19.6416C14.9994 19.6741 16.9257 17.6546 16.9257 15.2442ZM18.1794 4.6984C18.1794 2.15344 20.2063 0 22.7399 0C25.2735 0 27.3004 2.15344 27.2688 4.6984V14.9435C27.2688 17.4885 25.2735 19.6419 22.7082 19.6419C20.2063 19.6419 18.1794 17.5211 18.1794 14.9435V4.6984ZM44.8219 14.2437C44.8219 12.1624 43.8247 10.699 41.8304 9.82097C43.8247 8.94294 44.8219 7.51207 44.8219 5.39828C44.8219 2.24386 42.2979 0 38.247 0C32.825 0 28.8365 4.19505 28.8365 9.82097C28.8365 15.4469 32.825 19.6419 38.247 19.6419C42.2979 19.6419 44.8219 17.3981 44.8219 14.2437ZM62.5236 12.6709C63.0614 13.4527 63.3145 14.3321 63.3145 15.2442C63.3145 17.6546 61.3846 19.6741 59.0119 19.6416C57.6831 19.6416 56.3228 18.9901 55.5002 17.7523L54.6144 16.4494C54.2031 18.3386 52.6213 19.6416 50.5965 19.6416C48.2554 19.6416 46.3888 17.6872 46.3888 15.2768V4.36479C46.3888 1.95438 48.2237 0 50.5965 0C52.6529 0 54.2664 1.40064 54.646 3.32245L55.6268 1.88924C56.4493 0.716607 57.7781 0.0325731 59.1068 0.0325731C61.3846 0.0325731 63.3145 1.88924 63.3145 4.29964C63.3145 5.21169 63.0614 6.12373 62.5236 6.87291L60.4988 9.77192L62.5236 12.6709ZM79.3001 13.5975C79.3001 11.6269 78.3578 10.2474 76.9444 8.93364L75.7822 7.84978C77.4783 7.58702 78.6091 6.40463 78.6091 4.66389C78.6091 1.74075 76.379 0 71.6676 0C67.0504 0 64.3493 2.43048 64.3493 6.27325C64.3493 8.24391 65.3229 9.59052 66.7364 10.9371L67.8671 12.021H67.8357C65.7313 12.021 64.255 13.3019 64.255 15.3054C64.255 18.1957 66.5793 19.9693 71.542 19.9693C76.4104 19.9693 79.3001 17.506 79.3001 13.5975ZM103.096 16.2274C104.166 18.5363 105.675 19.6419 107.531 19.6419C110.865 19.6419 113.224 16.4875 111.777 12.9429L107.908 3.57717C106.965 1.26827 105.55 0 103.128 0C100.738 0 99.3222 1.26827 98.3472 3.57717L94.4787 12.9429C93.0005 16.4875 95.3908 19.6419 98.6932 19.6419C100.517 19.6419 102.027 18.5363 103.096 16.2274ZM113.465 5.2049C113.465 1.99671 115.107 0.327148 118.045 0.327148H123.509C126.826 0.327148 129.416 2.94607 129.416 6.31794C129.416 8.15119 128.69 9.65707 127.489 10.6064L129.132 13.3236C129.574 14.0438 129.764 14.8295 129.764 15.6479C129.764 18.0704 127.931 19.9691 125.626 19.9691C124.204 19.9691 122.814 19.2162 122.025 17.8412L121.583 17.0228C121.046 18.7578 119.561 19.9691 117.666 19.9691C115.36 19.9691 113.465 17.9394 113.465 15.4842V5.2049ZM138.32 19.9691C140.922 19.9691 142.865 17.9722 142.865 15.5497V8.77318C144.965 8.67498 146.689 6.84173 146.689 4.55017C146.689 2.19313 144.871 0.327148 142.646 0.327148H134.12C131.895 0.327148 130.077 2.1604 130.077 4.55017C130.077 6.84173 131.801 8.64224 133.901 8.77318V15.5497C133.901 17.9722 135.875 19.9691 138.32 19.9691ZM159.934 12.5742C161.522 12.9043 162.675 14.3238 162.675 16.2054C162.675 18.3181 161.055 20.0016 159.093 19.9686H152.552C149.562 19.9686 147.943 18.3181 147.943 15.083V5.21276C147.943 2.0107 149.562 0.327148 152.552 0.327148H159.093C161.055 0.327148 162.675 2.0107 162.675 4.1234C162.675 6.03803 161.553 7.42449 159.934 7.75459C160.681 8.24976 161.086 9.07503 161.086 10.1644C161.086 11.2537 160.65 12.079 159.934 12.5742ZM168.13 19.9691C165.824 19.9691 163.929 17.9394 163.929 15.4842V5.2049C163.929 1.99671 165.54 0.327148 168.509 0.327148H173.973C177.29 0.327148 179.88 2.94607 179.88 6.31794C179.88 8.15119 179.153 9.65707 177.953 10.6064L179.596 13.3236C180.038 14.0438 180.227 14.8295 180.227 15.6479C180.227 18.0704 178.395 19.9691 176.09 19.9691C174.668 19.9691 173.278 19.2162 172.489 17.8412L172.046 17.0228C171.509 18.7578 170.025 19.9691 168.13 19.9691ZM92.0807 15.5497C92.0807 17.9722 90.1023 19.9691 87.5587 19.9691C85.1092 19.9691 83.1308 17.9722 83.1308 15.5497V8.77318C81.0268 8.64224 79.2997 6.84173 79.2997 4.55017C79.2997 2.1604 81.121 0.327148 83.3507 0.327148H91.8609C94.0905 0.327148 95.9119 2.19313 95.9119 4.55017C95.9119 6.84173 94.1847 8.67498 92.0807 8.77318V15.5497Z"></path></svg></a><div class="flex items-center text-center pl2 global-nav-search w100p max-w110"><svg class="kds-icon shrink0 kds-fill-icon" style="width: 24px; aspect-ratio: 1 / 1;"><use xlink:href="#icon--search.kds"></use></svg><div class="w100p inline-block"><div class="relative smart-input-group"><input class="atomic-text-input border-none" id="global-nav-search-input" placeholder="Search projects, creators, and categories" type="text" value="" style="border-radius: 8px;"></div><div class="relative w100p"><div class="h5 clip absolute l0 t0 w100p"><div class="absolute l0 t1 w100p"></div></div></div></div><div class="global-nav-search-results flex display-grid max-h50vh justify-center absolute z-dropdown-2 l0 w100p scroll-y webkit-scrolling"><div class="max-w110"></div></div></div><section class="flex justify-start items-center global-nav-user-menu"><a class="kds-button kds-button" data-rac="" data-variant="outlined" href="/creators?ref=nav">For creators</a><a href="/login?ref=nav" class="soft-black hover-ksr-green-700 ml3 mr3 mr0-lg type-16">Log in</a></section>""",
        """<div class="mobile-show py3"></div><h2 class="normal mb4">Risks and challenges</h2><p class="js-risks-text text-preline"></p><a target="_blank" class="ksr-green-700 bold type-16" href="/help/hc/sections/115001107133">Learn about accountability on Kickstarter</a>"""
    ]

    # Count successful fetches
    # Updated the regex pattern to precisely match the specific error messages or start with "Error or not found: "
    error_pattern = "|".join([re.escape(msg) for msg in specific_error_messages]) + "|^Error or not found: "

    print(f"Number of projects in the scraped subset: {scraped_subset_df.shape[0]}")

    # Count projects with successfully scraped Story, Risks, and Rewards
    successful_count = scraped_subset_df[
        (~scraped_subset_df['story_html'].isna()) &
        (~scraped_subset_df['story_html'].astype(str).str.contains(error_pattern, na=False)) &
        (~scraped_subset_df['risks_html'].isna()) &
        (~scraped_subset_df['risks_html'].astype(str).str.contains(error_pattern, na=False)) &
        (~scraped_subset_df['rewards_html'].isna()) &
        (~scraped_subset_df['rewards_html'].astype(str).str.contains(error_pattern, na=False))
    ].shape[0]
    print(f"Number of projects with successfully scraped Story, Risks, and Rewards: {successful_count}")

    # Count projects with content in each column
    story_content_count = scraped_subset_df[
        (~scraped_subset_df['story_html'].isna()) &
        (~scraped_subset_df['story_html'].astype(str).str.contains(error_pattern, na=False))
    ].shape[0]
    print(f"Number of projects with Story content: {story_content_count}")

    risks_content_count = scraped_subset_df[
        (~scraped_subset_df['risks_html'].isna()) &
        (~scraped_subset_df['risks_html'].astype(str).str.contains(error_pattern, na=False))
    ].shape[0]
    print(f"Number of projects with Risks content: {risks_content_count}")

    rewards_content_count = scraped_subset_df[
        (~scraped_subset_df['rewards_html'].isna()) &
        (~scraped_subset_df['rewards_html'].astype(str).str.contains(error_pattern, na=False))
    ].shape[0]
    print(f"Number of projects with Rewards content: {rewards_content_count}")

    # Identify rows with any error message
    error_condition = (scraped_subset_df['story_html'].isna()) | (scraped_subset_df['story_html'].astype(str).str.contains(error_pattern, na=False)) | \
                    (scraped_subset_df['risks_html'].isna()) | (scraped_subset_df['risks_html'].astype(str).str.contains(error_pattern, na=False)) | \
                    (scraped_subset_df['rewards_html'].isna()) | (scraped_subset_df['rewards_html'].astype(str).str.contains(error_pattern, na=False))

    error_rows_df = scraped_subset_df[error_condition]

    print(f"\nNumber of projects with errors or missing content: {error_rows_df.shape[0]}")

    # Display number of unique values in the story_html, risks_html, and rewards_html columns
    print(f"\nNumber of unique values in 'story_html': {scraped_subset_df['story_html'].nunique()}")
    print(f"Number of unique values in 'risks_html': {scraped_subset_df['risks_html'].nunique()}")
    print(f"Number of unique values in 'rewards_html': {scraped_subset_df['rewards_html'].nunique()}")

if __name__ == "__main__":
    # If the progress file exists, use it
    if os.path.exists(progress_file):
        clean_df = pd.read_csv(progress_file)
    else:
        clean_df = pd.read_csv(initial_file)

    save_path = progress_file

    scrape(clean_df, save_path, start_idx=start_idx, end_idx=end_idx)