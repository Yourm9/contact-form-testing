import asyncio
import os
from playwright.async_api import async_playwright

async def smart_contact_form_submitter(url):
    headless = os.getenv("HEADLESS", "true").lower() == "true"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context()
        page = await context.new_page()

        result = {"status": "", "message": ""}
        try:
            await page.goto(url, timeout=60000)
            fields_filled = []

            selectors = {
                "name": ['input[name="name"]', 'input[name="your-name"]'],
                "email": ['input[name="email"]', 'input[name="your-email"]'],
                "subject": ['input[name="subject"]', 'input[name="your-subject"]'],
                "message": ['textarea[name="message"]', 'textarea[name="your-message"]']
            }

            field_values = {
                "name": "Test User",
                "email": "test@example.com",
                "subject": "Test Subject",
                "message": "This is a test message"
            }

            for field, selectors_list in selectors.items():
                for selector in selectors_list:
                    el = await page.query_selector(selector)
                    if el:
                        await el.fill(field_values[field])
                        fields_filled.append(field)
                        break

            submit_button = await page.query_selector('form button[type="submit"], form input[type="submit"]')
            if submit_button:
                await submit_button.click()
                result["status"] = "Success"
                result["message"] = f"Fields typed: {fields_filled}"
            else:
                result["status"] = "Failed"
                result["message"] = "No submit button found"
        except Exception as e:
            result["status"] = "Error"
            result["message"] = str(e)

        await browser.close()
        return result

# Local test
if __name__ == "__main__":
    test_url = "https://example.com/contact"
    print(asyncio.run(smart_contact_form_submitter(test_url)))
