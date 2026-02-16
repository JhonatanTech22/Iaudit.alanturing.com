from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        print("Launching headed browser...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        print("Navigating to Caixa...")
        page.goto("https://consulta-crf.caixa.gov.br/consultacrf/pages/consultaEmpregador.jsf")
        
        print("Waiting 10s for user to see...")
        time.sleep(10)
        
        print("Closing...")
        browser.close()

if __name__ == "__main__":
    run()
