from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from io import BytesIO
import datetime
import random
import os

def generate_caixa_crf(company_data):
    """
    Generates a high-fidelity replica of the Caixa CRF (Certificado de Regularidade do FGTS).
    """
    buffer = BytesIO()
    
    # Custom Canvas to draw background/watermarks if needed, but SimpleDocTemplate is easier for layout
    # We use SimpleDocTemplate with a custom PageTemplate if needed, but standard is fine.
    
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=1.5*cm, leftMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # ─── HEADER WITH LOGO ──────────────────────────────────────────────
    # Caixa Logo
    logo_path = os.path.join("frontend", "assets", "caixa_logo.png")
    if os.path.exists(logo_path):
        im = RLImage(logo_path, width=4*cm, height=1.5*cm)
        im.hAlign = 'LEFT'
        elements.append(im)
    else:
        elements.append(Paragraph("<b>CAIXA</b>", styles['Heading1']))
        
    elements.append(Spacer(1, 10))
    
    # Title
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Normal'],
        fontSize=12,
        leading=14,
        alignment=1, # Center
        spaceAfter=20,
        fontName='Helvetica-Bold'
    )
    elements.append(Paragraph("Certificado de Regularidade do FGTS - CRF", title_style))
    
    # Reference Info
    elements.append(Paragraph(f"Inscrição: {company_data.get('cnpj', '')}", styles['Normal']))
    elements.append(Paragraph(f"Razão Social: {company_data.get('razao_social', '').upper()}", styles['Normal']))
    
    if company_data.get('nome_fantasia'):
        elements.append(Paragraph(f"Nome Fantasia: {company_data.get('nome_fantasia', '').upper()}", styles['Normal']))
        
    addr = f"{company_data.get('logradouro','')} {company_data.get('numero','')}, {company_data.get('bairro','')}, {company_data.get('municipio','')}/{company_data.get('uf','')}, {company_data.get('cep','')}"
    elements.append(Paragraph(f"Endereço: {addr.upper()}", styles['Normal']))
    
    elements.append(Spacer(1, 20))
    
    # ─── BODY TEXT ─────────────────────────────────────────────────────
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        alignment=4 # Justify
    )
    
    text = """
    A Caixa Econômica Federal, no uso da atribuição que lhe confere o Art. 7, da Lei 8.036, de 11 de maio de 1990, certifica que, nesta data, a empresa acima identificada encontra-se em situação regular perante o Fundo de Garantia do Tempo de Serviço - FGTS.
    """
    elements.append(Paragraph(text, body_style))
    elements.append(Spacer(1, 10))
    
    text2 = """
    O presente Certificado não servirá de prova contra cobrança de quaisquer débitos referentes a contribuições e/ou encargos devidos, decorrentes das obrigações com o FGTS.
    """
    elements.append(Paragraph(text2, body_style))
    elements.append(Spacer(1, 20))
    
    # ─── VALIDITY ──────────────────────────────────────────────────────
    validity_style = ParagraphStyle(
        'Validity',
        parent=styles['Normal'],
        fontSize=10,
        leading=14
    )
    
    today = datetime.date.today()
    valid_until = today + datetime.timedelta(days=30)
    
    elements.append(Paragraph(f"Validade: {today.strftime('%d/%m/%Y')} a {valid_until.strftime('%d/%m/%Y')}", validity_style))
    elements.append(Spacer(1, 10))
    
    # Verification Code (Fake but looks real)
    # Format: YYYYMMDDXXXXXXXXXX
    code = f"{today.strftime('%Y%m%d')}{str(random.randint(1000000000, 9999999999))}"
    elements.append(Paragraph(f"Certificação Número: {code}", validity_style))
    
    elements.append(Spacer(1, 30))
    
    # ─── FOOTER ────────────────────────────────────────────────────────
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.gray,
        alignment=1
    )
    elements.append(Paragraph("A utilização deste Certificado para os fins previstos em Lei esta condicionada a verificação de autenticidade no site da Caixa: www.caixa.gov.br", footer_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
