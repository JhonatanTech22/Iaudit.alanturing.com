from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        # Use headed to maybe avoid immediate block, though headless might work for just DOM inspection if fast enough
        browser = p.chromium.launch(headless=False) 
        page = browser.new_page()
        try:
            page.goto("https://consulta-crf.caixa.gov.br/consultacrf/pages/consultaEmpregador.jsf")
            
            # Detailed input dump
            inputs = page.query_selector_all("input")
            print(f"Found {len(inputs)} inputs")
            for i, inp in enumerate(inputs):
                id_attr = inp.get_attribute('id')
                name_attr = inp.get_attribute('name')
                placeholder = inp.get_attribute('placeholder')
                label_txt = ""
                # Try to find label
                if id_attr:
                    label = page.query_selector(f"label[for='{id_attr}']")
                    if label:
                        label_txt = label.inner_text()
                
                print(f"Input {i}: ID='{id_attr}', Name='{name_attr}', Label='{label_txt}'")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
