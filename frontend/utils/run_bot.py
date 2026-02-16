import sys
import os
import time
from playwright.sync_api import sync_playwright

def run_bot(cnpj_raw, uf="PR"):
    # Clean CNPJ
    cnpj = "".join(filter(str.isdigit, cnpj_raw))
    uf = uf.upper().strip()
    
    print(f"Starting Caixa Bot for CNPJ: {cnpj} | UF: {uf}")
    
    with sync_playwright() as p:
        # Launch headed to allow user interaction
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            print("Navigating to Caixa CRF...")
            page.goto("https://consulta-crf.caixa.gov.br/consultacrf/pages/consultaEmpregador.jsf", wait_until="load", timeout=45000)
            
            # Wait for input to be ready
            page.wait_for_selector("#mainForm\\:txtInscricao1", state="visible", timeout=15000)
            
            # 1. Select UF
            print(f"Selecting UF: {uf}")
            try:
                page.select_option("#mainForm\\:uf", value=uf)
            except Exception as e:
                print(f"Warning: Could not select UF via ID: {e}. Trying name selector...")
                page.select_option('select[name="mainForm:uf"]', value=uf)

            # 2. Fill CNPJ
            # Type slowly to trigger internal JS masks
            page.type("#mainForm\\:txtInscricao1", cnpj, delay=100)
            print("CNPJ Filled.")
            
            # Alert user
            page.evaluate(f"alert('🤖 Automação IAudit:\\n\\nCNPJ ({cnpj}) e UF ({uf}) preenchidos.\\nPor favor, resolva o CAPTCHA e clique em Consultar.')")
            
            print("Waiting for download...")
            
            # Monitor for download triggered by user clicking 'Visualizar' after search
            with page.expect_download(timeout=300000) as download_info:
                # We also attempt to auto-click "Visualizar" if it appears after captcha
                for _ in range(60): # 1 minute max auto-check
                    try:
                        btn = page.get_by_text("Visualizar", exact=False)
                        if btn.is_visible():
                            print("Button 'Visualizar' found! Clicking...")
                            btn.click()
                            break
                    except:
                        pass
                    time.sleep(1)
            
            download = download_info.value
            save_path = os.path.join(os.getcwd(), "frontend", "downloads", f"CRF_Original_{cnpj}.pdf")
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            download.save_as(save_path)
            
            print(f"PDF Original Salvo em: {save_path}")
            page.evaluate(f"alert('✅ PDF Original Salvo!')")
            time.sleep(2)

        except Exception as e:
            print(f"Status Error: {e}")
            time.sleep(10)
        finally:
            browser.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cnpj_arg = sys.argv[1]
        uf_arg = sys.argv[2] if len(sys.argv) > 2 else "PR"
        run_bot(cnpj_arg, uf_arg)
    else:
        print("Usage: python run_bot.py <CNPJ> [UF]")
