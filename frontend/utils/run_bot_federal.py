import sys
import os
import time
from playwright.sync_api import sync_playwright

def run_bot_federal(cnpj_raw):
    # Clean CNPJ
    cnpj = "".join(filter(str.isdigit, cnpj_raw))
    
    print(f"Starting Federal CND Bot for CNPJ: {cnpj}")
    
    with sync_playwright() as p:
        # Launch with a common user agent
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            # TRY ALL LOWERCASE FIRST (Standard PJ URL)
            url = "https://solucoes.receita.fazenda.gov.br/Servicos/certidaointernet/pj/emitir"
            print(f"Navigating to: {url}")
            
            # Go to the main PJ emission page
            page.goto(url, wait_until="load", timeout=45000)
            
            # If we still see 404, the portal might be temporarily down or moved to GOV.BR
            if "404" in page.title() or "not found" in page.content().lower():
                print("404 Detected. Redirecting to GOV.BR bridge...")
                page.goto("https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/certidoes-e-situacao-fiscal/certidao-de-regularidade-fiscal-pessoa-juridica")
                page.click("text=Emitir certidão") # Standard GOV.BR pattern
                time.sleep(2)

            # Wait for CNPJ input - The selector is usually 'NI' (case sensitive)
            try:
                page.wait_for_selector('input[name="NI"]', state="visible", timeout=15000)
                selector = 'input[name="NI"]'
            except:
                page.wait_for_selector('input#Ni', state="visible", timeout=10000)
                selector = 'input#Ni'
            
            # Fill CNPJ
            page.fill(selector, cnpj)
            print("CNPJ Filled.")
            
            # Alert user
            page.evaluate("alert('🤖 Automação IAudit:\\n\\nCNPJ preenchido.\\nResolva o CAPTCHA e clique em Consultar.')")
            
            print("Waiting for download...")
            with page.expect_download(timeout=300000) as download_info:
                pass
            
            download = download_info.value
            save_path = os.path.join(os.getcwd(), "frontend", "downloads", f"CND_Federal_Original_{cnpj}.pdf")
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            download.save_as(save_path)
            
            print(f"PDF Federal Salvo: {save_path}")
            page.evaluate(f"alert('✅ PDF Federal Guardado!')")
            time.sleep(2)

        except Exception as e:
            print(f"Status Error: {e}")
            time.sleep(10)
        finally:
            browser.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_bot_federal(sys.argv[1])
    else:
        print("Please provide a CNPJ argument.")
