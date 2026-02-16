from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            print("Navigating to Caixa CRF...")
            page.goto("https://consulta-crf.caixa.gov.br/consultacrf/pages/consultaEmpregador.jsf")
            print("Page loaded.")
            print("Title:", page.title())
            
            # Dump HTML to check for captcha
            content = page.content()
            if "captcha" in content.lower() or "recaptcha" in content.lower():
                print("CAPTCHA detected!")
            else:
                print("No explicit 'captcha' text found, checking form elements...")
                
            # Check inputs
            inputs = page.query_selector_all("input")
            for i, inp in enumerate(inputs):
                print(f"Input {i}: id={inp.get_attribute('id')}, name={inp.get_attribute('name')}, type={inp.get_attribute('type')}")
                
            # Check images (often used for text captchas)
            imgs = page.query_selector_all("img")
            for i, img in enumerate(imgs):
                print(f"Image {i}: src={img.get_attribute('src')}")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
