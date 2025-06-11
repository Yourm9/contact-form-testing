import time
import random
import csv
from datetime import datetime
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright
import re
import sys

# Check for --headless flag in command-line args
run_headless = '--headless' in sys.argv


def human_type(page, selector, text):
    page.click(selector)
    typo_made = False
    for i, char in enumerate(text):
        if not typo_made and random.random() < 0.015 and len(text) > 8:
            # Introduce one typo, then correct it
            wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
            page.keyboard.insert_text(wrong_char)
            time.sleep(random.uniform(0.05, 0.12))
            page.keyboard.press('Backspace')
            time.sleep(random.uniform(0.03, 0.1))
            typo_made = True

        page.keyboard.insert_text(char)
        time.sleep(random.uniform(0.04, 0.18))

        # Occasional pause to mimic human pause
        if i > 0 and i % random.randint(5, 10) == 0:
            time.sleep(random.uniform(0.1, 0.3))

    time.sleep(random.uniform(0.6, 1.4))


def log_result_to_csv(domain, contact_url, status, fields, log_file="results.csv"):
    with open(log_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            datetime.now().isoformat(),
            domain,
            contact_url or "N/A",
            status,
            ", ".join(fields)
        ])


def smart_contact_form_submitter(start_url):
    domain = urlparse(start_url).netloc
    result = {
        "timestamp": datetime.now().isoformat(),
        "domain": domain,
        "start_url": start_url,
        "contact_page": None,
        "fields_filled": [],
        "status": "",
    }

    with sync_playwright() as p:
        # Launch browser with or without headless mode based on flag
        browser = p.chromium.launch(headless=run_headless, slow_mo=0)

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()

        try:
            print(f"🌐 Visiting: {start_url}")
            page.goto(start_url, timeout=20000)

            contact_links = page.query_selector_all('a[href]')
            contact_url = None
            for link in contact_links:
                href = link.get_attribute('href')
                if href and re.search(r'contact', href, re.IGNORECASE):
                    contact_url = urljoin(start_url, href)
                    break

            if not contact_url:
                result["status"] = "No contact page found"
                log_result_to_csv(domain, None, result["status"], [])
                return result

            result["contact_page"] = contact_url
            print(f"🔗 Contact page found: {contact_url}")
            page.goto(contact_url, timeout=20000)

            field_map = {
                'name': 'John Doe',
                'email': 'john@example.com',
                'subject': 'Quick question about landscaping',
                'message': 'Hi there! Just wondering if you service southern uk area? Thanks!',
                'phone': '07800111222'
            }

            form_inputs = page.query_selector_all('input, textarea')
            filled = []

            for el in form_inputs:
                name_attr = el.get_attribute('name') or ''
                placeholder = el.get_attribute('placeholder') or ''
                selector = f'[name="{name_attr}"]' if name_attr else ''
                for key, value in field_map.items():
                    if key in name_attr.lower() or key in placeholder.lower():
                        if page.query_selector(selector):
                            human_type(page, selector, value)
                            filled.append(key)
                            break

            if not filled:
                result["status"] = "No fields matched"
                log_result_to_csv(domain, contact_url, result["status"], filled)
                return result

            result["fields_filled"] = filled
            print(f"📝 Fields typed: {filled}")

            submit_btn = page.query_selector('form button[type="submit"], form input[type="submit"]')
            if submit_btn:
                time.sleep(random.uniform(1, 2.5))
                submit_btn.hover()
                time.sleep(0.5)
                submit_btn.click()
                page.wait_for_timeout(3000)
                result["status"] = "Form submitted successfully"
                print("✅ Form submitted")
            else:
                result["status"] = "Submit button not found"

        except Exception as e:
            result["status"] = f"Error: {str(e)}"
            print(f"❌ Error: {e}")
        finally:
            log_result_to_csv(domain, result["contact_page"], result["status"], result["fields_filled"])
            browser.close()

    return result


def run_from_csv(file_path):
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            url = row[0].strip()
            if url:
                print(f"\n🚀 Running bot on: {url}")
                smart_contact_form_submitter(url)


# Run from CSV
if __name__ == "__main__":
    filepath = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else "urls.csv"
    run_from_csv(filepath)
