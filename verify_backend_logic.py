
import sys
import os
# Add the project root to sys.path to allow imports
sys.path.append(os.path.abspath("frontend"))

from components.mock_data import get_company_details
from utils.certificate_generator import generate_fgts_certificate
from datetime import datetime

def test_deterministic_cnpj():
    cnpj = "12.345.678/0001-90"
    print(f"Testing deterministic search for CNPJ: {cnpj}")
    
    # Run 1
    data1 = get_company_details(cnpj)
    # Run 2
    data2 = get_company_details(cnpj)
    
    # Check if they are identical
    if data1 == data2:
        print("[OK] SUCCESS: Mock data generation is deterministic.")
        print(f"   Razão Social 1: {data1['razao_social']}")
        print(f"   Razão Social 2: {data2['razao_social']}")
    else:
        print("[FAIL] FAIL: Mock data generation is NOT deterministic.")
        print(f"   Run 1: {data1['razao_social']}")
        print(f"   Run 2: {data2['razao_social']}")
        
    return data1

def test_certificate_generation(company_data):
    print("\nTesting Certificate Generation...")
    try:
        cert_html = generate_fgts_certificate(company_data)
        if cert_html and len(cert_html) > 0:
            print("[OK] SUCCESS: Certificate HTML generated.")
            print(f"   Length: {len(cert_html)} characters")
            # verify it contains some key strings
            if company_data['razao_social'] in cert_html:
                 print("   Contains Company Name: Yes")
            else:
                 print("   Contains Company Name: NO")
        else:
            print("[FAIL] FAIL: Certificate HTML is empty.")
    except Exception as e:
        print(f"[FAIL] FAIL: Certificate generation raised exception: {e}")

if __name__ == "__main__":
    try:
        data = test_deterministic_cnpj()
        test_certificate_generation(data)
    except Exception as e:
        print(f"Simulation failed with error: {e}")
