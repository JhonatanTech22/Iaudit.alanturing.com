from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from io import BytesIO
import datetime

def generate_company_pdf(company_data):
    """
    Generates a PDF report for the given company data.
    Returns a BytesIO object containing the PDF.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=10,
        textColor=colors.HexColor('#1e40af'),
        alignment=1 # Center
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=20,
        alignment=1
    )
    
    header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#1e40af'),
        spaceBefore=15,
        spaceAfter=5,
        borderPadding=5,
        borderColor=colors.HexColor('#e2e8f0'),
        borderWidth=1
    )
    
    normal_style = styles['Normal']
    
    elements = []
    
    # ─── HEADER ────────────────────────────────────────────────────────
    elements.append(Paragraph("Relatório de Situação Fiscal", title_style))
    elements.append(Paragraph(f"Gerado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}", subtitle_style))
    elements.append(Spacer(1, 10))
    
    # ─── COMPANY INFO ──────────────────────────────────────────────────
    data = [
        ["Razão Social:", company_data.get('razao_social', 'N/A')],
        ["CNPJ:", company_data.get('cnpj', 'N/A')],
        ["Situação Cadastral:", company_data.get('situacao_cadastral', 'N/A')],
        ["Abertura:", company_data.get('data_inicio_atividade', 'N/A')],
        ["Natureza Jurídica:", company_data.get('natureza_juridica', 'N/A')],
        ["Porte:", company_data.get('porte', 'N/A')],
        ["Endereço:", f"{company_data.get('logradouro','')} {company_data.get('numero','')}, {company_data.get('bairro','')}"],
        ["Cidade/UF:", f"{company_data.get('municipio','')}/{company_data.get('uf','')}"]
    ]
    
    t = Table(data, colWidths=[5*cm, 11*cm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor('#334155')),
        ('BACKGROUND', (0,0), (1,0), colors.HexColor('#f1f5f9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # ─── CERTIFICATES ──────────────────────────────────────────────────
    elements.append(Paragraph("Situação das Certidões", header_style))
    
    cert_data = company_data.get('certidoes', {})
    cnd_fed = cert_data.get('cnd_federal', {}).get('status', 'N/D')
    cnd_est = cert_data.get('cnd_estadual', {}).get('status', 'N/D')
    fgts = cert_data.get('fgts', {}).get('status', 'N/D')
    
    cert_table_data = [
        ["Certidão", "Status"],
        ["CND Federal", cnd_fed.upper()],
        ["CND Estadual (PR)", cnd_est.upper()],
        ["FGTS", fgts.upper()]
    ]
    
    ct = Table(cert_table_data, colWidths=[8*cm, 8*cm])
    ct.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('ALIGN', (1,0), (1,-1), 'CENTER'),
    ]))
    elements.append(ct)
    
    # Disclaimer
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("Este documento é gerado automaticamente pelo sistema IAudit e não substitui as certidões oficiais emitidas pelos órgãos governamentais.", ParagraphStyle('Disclaimer', parent=normal_style, fontSize=8, textColor=colors.gray)))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
