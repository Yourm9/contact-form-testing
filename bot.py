import time
import random
import csv
import os
from datetime import datetime
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright
import re
import sys
import requests
import socket

# Airtable configuration
AIRTABLE_BASE_ID = 'appT3CUPasvZJBxdf'
AIRTABLE_TABLE_NAME = 'Submission Results'
AIRTABLE_API_KEY = 'patqYGRYwqAmTC8B8.08a5c910f7592dc71077da2230065eae0ab9af1575b02c26c809e0a09bee7c94'

def log_result_to_airtable(data):
    url = f'https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}'
    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {"fields": data}
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to log to Airtable: {e}")

def get_server_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "Unknown"
    finally:
        s.close()
    return ip

is_server = os.environ.get("SERVER_ENV", "false").lower() == "true"
run_headless = is_server or '--headless' in sys.argv

def human_type(page, selector, text):
    page.click(selector)
    typo_made = False
    for i, char in enumerate(text):
        if not typo_made and random.random() < 0.015 and len(text) > 8:
            wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
            page.keyboard.insert_text(wrong_char)
            time.sleep(random.uniform(0.05, 0.12))
            page.keyboard.press('Backspace')
            time.sleep(random.uniform(0.03, 0.1))
            typo_made = True
        page.keyboard.insert_text(char)
        time.sleep(random.uniform(0.04, 0.18))
        if i > 0 and i % random.randint(5, 10) == 0:
            time.sleep(random.uniform(0.1, 0.3))
    time.sleep(random.uniform(0.6, 1.4))

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
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()

        try:
            print(f"\nRunning bot on: {start_url}")
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
                finalise_result(result, domain)
                return result

            result["contact_page"] = contact_url
            print(f"Contact page found: {contact_url}")
            page.goto(contact_url, timeout=20000)

            field_map = {
                'name': 'John Doe',
                'email': 'john@example.com',
                'subject': 'Quick question about landscaping',
                'message': 'Hi there! Just wondering if you service southern UK area? Thanks!',
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
                finalise_result(result, domain)
                return result

            result["fields_filled"] = filled
            print(f"Fields typed: {filled}")

            # Prioritize form-contained submit buttons
            forms = page.query_selector_all("form")
            submit_clicked = False

            for form in forms:
                submit = form.query_selector('input[type="submit"], button[type="submit"]')
                if submit:
                    try:
                        form.scroll_into_view_if_needed()
                        page.wait_for_function(
                            "(btn) => { const r = btn.getBoundingClientRect(); return r.width > 0 && r.height > 0; }",
                            arg=submit,
                            timeout=10000
                        )
                        print("🖱 Attempting form-contained submit button click")
                        submit.click()
                        page.wait_for_timeout(3000)
                        result["status"] = "Form submitted successfully"
                        submit_clicked = True
                        break
                    except Exception as e:
                        print(f"⚠️ Click failed: {e}")

            if not submit_clicked:
                try:
                    print("🖱 Attempting JS click fallback")
                    page.evaluate("document.querySelector('input[type=submit], button[type=submit]').click()")
                    page.wait_for_timeout(3000)
                    result["status"] = "Form submitted via JS"
                except Exception as err:
                    result["status"] = f"Error: {str(err)}"

        except Exception as e:
            result["status"] = f"Error: {str(e)}"
            print(f"Error: {e}")

        finally:
            finalise_result(result, domain)
            browser.close()

    return result

def finalise_result(result, domain):
    status_raw = result["status"].lower()
    if "successfully" in status_raw or "via js" in status_raw:
        status_value = "Success"
    elif "no contact page" in status_raw:
        status_value = "No contact page found"
    elif "no fields matched" in status_raw:
        status_value = "No fields matched"
    else:
        status_value = "Failed"

    result_data = {
        "Submission ID": f"{domain}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "Timestamp": result["timestamp"],
        "Status": status_value,
        "Error Type": "" if status_value == "Success" else result["status"],
        "Message": ", ".join(result["fields_filled"]),
        "Server IP": get_server_ip(),
        "Retry Count": 0,
    }

    log_result_to_airtable(result_data)

def run_from_csv(file_path):
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            url = row[0].strip()
            if url:
                print(f"\nRunning bot on: {url}")
                smart_contact_form_submitter(url)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        smart_contact_form_submitter(sys.argv[1])
    else:
        run_from_csv("urls.csv")
