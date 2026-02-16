import base64
from datetime import datetime, timedelta
import random

def generate_fgts_certificate(company_data):
    """
    Generate HTML content for FGTS Regularity Certificate based on company data.
    """
    
    # Generate dates
    now = datetime.now()
    validity_start = now - timedelta(days=15)
    validity_end = now + timedelta(days=15)
    
    # Generate unique certificate number
    cert_number = f"{now.strftime('%Y%m%d')}{random.randint(10000000000000, 99999999999999)}"
    
    # Format data
    cnpj = company_data.get('cnpj', '')
    razao_social = company_data.get('razao_social', '').upper()
    endereco = f"{company_data.get('logradouro', '')}, {company_data.get('numero', '')} - {company_data.get('bairro', '')} - {company_data.get('municipio', '')}/{company_data.get('uf', '')} - {company_data.get('cep', '')}".upper()
    
    html_content = f"""
    <!DOCTYPE html>
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <meta charset="utf-8">
        <title>Consulta Regularidade do Empregador</title>
        <style>
            body {{
                font-family: Verdana, sans-serif;
                font-size: 15px; 
                color: #000;
                background: #fff;
                margin: 0;
                padding: 20px;
                line-height: 1.4;
            }}
            .main-container {{
                width: 750px;
                margin: 0 auto;
                padding: 20px;
                border: 1px solid #000;
            }}
            .header {{
                text-align: center;
                margin-bottom: 25px;
            }}
            .caixa-logo {{
                font-family: Arial, sans-serif;
                font-weight: bold;
                font-size: 32px;
                color: #005ca9;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
            }}
            .x-mark {{
                color: #f37021;
                font-size: 32px;
            }}
            .cert-title {{
                font-size: 18px;
                font-weight: bold;
                margin-top: 15px;
            }}
            .info-section {{
               margin-bottom: 15px;
            }}
            .info-label {{
                font-weight: bold;
                font-size: 14px;
                width: 140px;
                display: inline-block;
                vertical-align: top;
            }}
            .info-value {{
                display: inline-block;
                width: 580px;
                font-size: 14px;
                font-weight: normal;
            }}
            .cert-text {{
                text-align: justify;
                margin: 25px 0;
                font-size: 14px;
            }}
            .validity-section {{
                margin-top: 20px;
            }}
            .footer-info {{
                margin-top: 40px;
                font-size: 12px;
            }}
            .verification-note {{
                margin-top: 20px;
                font-size: 12px;
                text-align: justify;
            }}
            @media print {{
                body {{ padding: 0; margin: 0; }}
                .main-container {{ border: none; width: 100%; }}
            }}
        </style>
    </head>
    <body onload="window.print()">
        <div class="main-container">
            <div class="header">
                <div class="caixa-logo">
                    CAIXA <span class="x-mark">X</span>
                </div>
                <div class="cert-title">Certificado de Regularidade do FGTS - CRF</div>
            </div>

            <!-- Inscrição -->
            <div class="info-section">
                <span class="info-label">Inscrição:</span>
                <span class="info-value">{cnpj}</span>
            </div>

            <!-- Razão Social -->
            <div class="info-section">
                <span class="info-label">Razão Social:</span>
                <span class="info-value">{razao_social}</span>
            </div>

            <!-- Endereço -->
            <div class="info-section">
                <span class="info-label">Endereço:</span>
                <span class="info-value">{endereco}</span>
            </div>

            <!-- Texto Legal -->
            <div class="cert-text">
                A Caixa Econômica Federal, no uso da atribuição que lhe confere o Art. 7, da Lei 8.036, de 11 de maio de 1990, certifica que, nesta data, a empresa acima identificada encontra-se em situação regular perante o Fundo de Garantia do Tempo de Servico - FGTS.
            </div>

            <div class="cert-text">
                O presente Certificado não servirá de prova contra cobrança de quaisquer débitos referentes a contribuições e/ou encargos devidos, decorrentes das obrigações com o FGTS.
            </div>

            <!-- Validade e Certificação -->
            <div class="validity-section">
                <div class="info-section">
                    <span class="info-label">Validade:</span>
                    <span class="info-value">{validity_start.strftime('%d/%m/%Y')} a {validity_end.strftime('%d/%m/%Y')}</span>
                </div>
                
                <div class="info-section">
                    <span class="info-label">Certificação Número:</span>
                    <span class="info-value">{cert_number}</span>
                </div>
            </div>

            <!-- Rodapé -->
            <div class="footer-info">
                Informação obtida em {now.strftime('%d/%m/%Y %H:%M:%S')}
            </div>

            <div class="verification-note">
                A utilização deste Certificado para os fins previstos em Lei esta condicionada a verificação de autenticidade no site da Caixa: <strong>www.caixa.gov.br</strong>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content
