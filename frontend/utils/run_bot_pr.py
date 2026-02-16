import sys
import os
import time
from playwright.sync_api import sync_playwright

def run_bot_pr(cnpj_raw):
    # Clean CNPJ
    cnpj = "".join(filter(str.isdigit, cnpj_raw))
    
    print(f"Starting SEFAZ PR (New Portal) Bot for CNPJ: {cnpj}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            # NEW PORTAL URL after Celepar migration
            url = "https://cdwfazenda.paas.pr.gov.br/cdwportal/certidao/automatica"
            print(f"Navigating to: {url}")
            
            page.goto(url, wait_until="load", timeout=45000)
            
            # Wait for Document input
            # Try to find CNPJ input with multiple strategies
            print("Searching for CNPJ input...")
            selector = None
            
            strategies = [
                "#numDocumento",
                "input[name='numDocumento']",
                "input[formcontrolname='numDocumento']",
                "input[placeholder*='CNPJ']",
                "input[placeholder*='Documento']",
                "input[aria-label*='CNPJ']",
                "input[type='text']",  # Fallback to first text input
                "input[type='tel']"    # Sometimes CNPJ field is tel
            ]
            
            for s in strategies:
                try:
                    print(f"Trying selector: {s}")
                    if page.is_visible(s, timeout=2000):
                        selector = s
                        print(f"Found input: {s}")
                        break
                except:
                    continue
            
            if selector:
                try:
                    page.click(selector, timeout=2000)
                    page.fill(selector, cnpj)
                    print(f"Filled CNPJ using {selector}")
                except Exception as e:
                     print(f"Error filling {selector}: {e}")
            else:
                print("No suitable input found for auto-fill.")

            # Alert user to solve captcha
            page.evaluate("alert('🤖 Automação IAudit:\\n\\nEste é o NOVO sistema da SEFAZ PR.\\n\\nSe o CNPJ não foi preenchido, preencha manualmente.\\nResolva o CAPTCHA e clique em Emitir.')")
            
            print("Waiting for download or user action...")
            try:
                with page.expect_download(timeout=300000) as download_info:
                    # Keep script alive for user interaction
                    pass
                
                download = download_info.value
                save_path = os.path.join(os.getcwd(), "frontend", "downloads", f"CND_Estadual_PR_Original_{cnpj}.pdf")
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                download.save_as(save_path)
                
                print(f"PDF PR Salvo: {save_path}")
                page.evaluate(f"alert('✅ PDF Estadual PR Guardado!')")
                time.sleep(2)
            except Exception as e:
                print(f"Download timeout or closed: {e}")

        except Exception as e:
            print(f"Status Error: {e}")
            # Keep browser open for a bit if error occurs so user sees it
            time.sleep(5)
        finally:
            browser.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_bot_pr(sys.argv[1])
    else:
        print("Please provide a CNPJ argument.")
