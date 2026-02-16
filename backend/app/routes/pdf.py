"""PDF Certificate generation for CNPJ compliance reports."""

import io
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Circle, String, Rect, Line
from reportlab.graphics import renderPDF

from app.routes.query import query_cnpj

router = APIRouter()

# ─── Color palette ────────────────────────────────────────────────
BLUE_DARK = colors.HexColor('#0f172a')
BLUE_PRIMARY = colors.HexColor('#1e40af')
BLUE_LIGHT = colors.HexColor('#dbeafe')
BLUE_ACCENT = colors.HexColor('#3b82f6')
GREEN = colors.HexColor('#059669')
GREEN_LIGHT = colors.HexColor('#d1fae5')
RED = colors.HexColor('#dc2626')
RED_LIGHT = colors.HexColor('#fee2e2')
YELLOW = colors.HexColor('#d97706')
YELLOW_LIGHT = colors.HexColor('#fef3c7')
GRAY = colors.HexColor('#64748b')
GRAY_LIGHT = colors.HexColor('#f1f5f9')
GRAY_BORDER = colors.HexColor('#cbd5e1')
WHITE = colors.white


def _fmt_cnpj(c):
    c = str(c).zfill(14)
    return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:14]}"


def _fmt_capital(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "N/A"


def _fmt_date(d):
    if d and len(str(d)) == 10:
        parts = str(d).split("-")
        if len(parts) == 3:
            return f"{parts[2]}/{parts[1]}/{parts[0]}"
    return str(d or "N/A")


def _fmt_cnae_code(code):
    c = str(code).zfill(7)
    return f"{c[:2]}.{c[2:4]}-{c[4]}/{c[5:7]}"


def _fmt_telefone(t):
    t = str(t or "")
    if len(t) >= 10:
        return f"({t[:2]}) {t[2:6]}-{t[6:]}"
    return t or "N/A"


def _get_status_info(status):
    if status == 'regular':
        return 'REGULAR', GREEN, GREEN_LIGHT, '✓'
    elif status == 'irregular':
        return 'IRREGULAR', RED, RED_LIGHT, '✗'
    elif status == 'consultando':
        return 'CONSULTANDO', YELLOW, YELLOW_LIGHT, '…'
    else:
        return 'INDISPONÍVEL', GRAY, GRAY_LIGHT, '—'


def _create_seal(score):
    """Create a compliance seal drawing."""
    d = Drawing(120, 120)
    
    # Outer circle
    if score >= 70:
        fill_color = GREEN
    elif score >= 40:
        fill_color = YELLOW
    else:
        fill_color = RED
    
    d.add(Circle(60, 60, 55, fillColor=fill_color, strokeColor=colors.white, strokeWidth=3))
    d.add(Circle(60, 60, 48, fillColor=colors.white, strokeColor=fill_color, strokeWidth=2))
    d.add(Circle(60, 60, 44, fillColor=fill_color, strokeColor=fill_color, strokeWidth=0))
    
    # Score text
    d.add(String(60, 55, f"{score}%", fontSize=22, fillColor=colors.white,
                 textAnchor='middle', fontName='Helvetica-Bold'))
    d.add(String(60, 40, "SCORE", fontSize=8, fillColor=colors.white,
                 textAnchor='middle', fontName='Helvetica'))
    
    return d


def create_certificate_pdf(cnpj: str, data: dict) -> bytes:
    """Generate professional compliance certificate PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=1.8*cm, leftMargin=1.8*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    page_width = A4[0] - 3.6*cm  # Available width
    
    # ─── Custom Styles ─────────────────────────────────────────
    title_style = ParagraphStyle(
        'CertTitle', parent=styles['Heading1'],
        fontSize=22, textColor=BLUE_PRIMARY,
        spaceAfter=5, alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CertSubtitle', parent=styles['Normal'],
        fontSize=11, textColor=GRAY,
        spaceAfter=15, alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    heading_style = ParagraphStyle(
        'SectionHead', parent=styles['Heading2'],
        fontSize=13, textColor=BLUE_PRIMARY,
        spaceAfter=8, spaceBefore=15,
        fontName='Helvetica-Bold',
        borderColor=BLUE_PRIMARY,
        borderWidth=0, borderPadding=0,
    )
    
    normal_style = ParagraphStyle(
        'CertNormal', parent=styles['Normal'],
        fontSize=10, spaceAfter=4,
        fontName='Helvetica',
    )
    
    small_style = ParagraphStyle(
        'CertSmall', parent=styles['Normal'],
        fontSize=8, textColor=GRAY,
        fontName='Helvetica',
    )
    
    footer_style = ParagraphStyle(
        'CertFooter', parent=styles['Normal'],
        fontSize=8, textColor=GRAY,
        alignment=TA_CENTER, spaceAfter=3,
    )
    
    # ─── Header ────────────────────────────────────────────────
    # Top border
    elements.append(HRFlowable(
        width="100%", thickness=3, color=BLUE_PRIMARY,
        spaceAfter=15
    ))
    
    elements.append(Paragraph("CERTIFICADO DE CONFORMIDADE", title_style))
    elements.append(Paragraph("Relatório de Situação Cadastral e Regularidade", subtitle_style))
    
    # Meta info
    tz_br = timezone(timedelta(hours=-3))
    now = datetime.now(tz_br).strftime("%d/%m/%Y às %H:%M")
    
    meta_data = [
        [
            Paragraph(f"<b>Data de Emissão:</b> {now}", small_style),
            Paragraph(f"<b>CNPJ:</b> {_fmt_cnpj(data.get('cnpj', cnpj))}", small_style),
        ]
    ]
    meta_table = Table(meta_data, colWidths=[page_width/2, page_width/2])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BLUE_LIGHT),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('BOX', (0, 0), (-1, -1), 0.5, GRAY_BORDER),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 1: DADOS CADASTRAIS
    # ═══════════════════════════════════════════════════════════
    elements.append(Paragraph("1. DADOS CADASTRAIS", heading_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=BLUE_ACCENT, spaceAfter=8))
    
    situacao = data.get('situacao_cadastral', 'N/A')
    
    company_rows = [
        ['Campo', 'Informação'],
        ['CNPJ', _fmt_cnpj(data.get('cnpj', ''))],
        ['Razão Social', data.get('razao_social', 'N/A')],
        ['Nome Fantasia', data.get('nome_fantasia', '') or '—'],
        ['Situação Cadastral', situacao],
        ['Data Situação', _fmt_date(data.get('data_situacao_cadastral', ''))],
        ['Natureza Jurídica', data.get('natureza_juridica', 'N/A')],
        ['Porte', data.get('porte', 'N/A')],
        ['Capital Social', _fmt_capital(data.get('capital_social', 0))],
        ['Tipo', data.get('identificador_matriz_filial', 'N/A')],
        ['Data de Abertura', _fmt_date(data.get('data_inicio_atividade', ''))],
        ['Telefone', _fmt_telefone(data.get('telefone', ''))],
        ['Email', data.get('email', '') or '—'],
    ]
    
    company_table = Table(company_rows, colWidths=[5*cm, page_width - 5*cm])
    company_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), BLUE_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        # Data rows
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (0, -1), BLUE_LIGHT),
        ('ROWBACKGROUNDS', (1, 1), (1, -1), [WHITE, GRAY_LIGHT]),
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, GRAY_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(company_table)
    elements.append(Spacer(1, 0.4*cm))
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 2: ENDEREÇO
    # ═══════════════════════════════════════════════════════════
    elements.append(Paragraph("2. ENDEREÇO", heading_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=BLUE_ACCENT, spaceAfter=8))
    
    tipo_log = data.get('descricao_tipo_de_logradouro', '')
    logr = data.get('logradouro', '')
    num = data.get('numero', '')
    comp = data.get('complemento', '')
    endereco = f"{tipo_log} {logr}, {num}"
    if comp:
        endereco += f" - {comp}"
    
    addr_rows = [
        ['Campo', 'Informação'],
        ['Logradouro', endereco],
        ['Bairro', data.get('bairro', 'N/A')],
        ['Município/UF', f"{data.get('municipio', 'N/A')}/{data.get('uf', 'N/A')}"],
        ['CEP', data.get('cep', 'N/A')],
    ]
    
    addr_table = Table(addr_rows, colWidths=[5*cm, page_width - 5*cm])
    addr_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BLUE_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (0, -1), BLUE_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.5, GRAY_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(addr_table)
    elements.append(Spacer(1, 0.4*cm))
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 3: ATIVIDADE ECONÔMICA
    # ═══════════════════════════════════════════════════════════
    elements.append(Paragraph("3. ATIVIDADES ECONÔMICAS (CNAE)", heading_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=BLUE_ACCENT, spaceAfter=8))
    
    cnae_rows = [['Tipo', 'Código', 'Descrição']]
    
    cnae_principal = data.get('cnae_fiscal', '')
    if cnae_principal:
        cnae_rows.append(['PRINCIPAL', _fmt_cnae_code(cnae_principal), data.get('cnae_fiscal_descricao', '')])
    
    for cnae_sec in data.get('cnaes_secundarios', []):
        cnae_rows.append([
            'Secundária',
            _fmt_cnae_code(cnae_sec.get('codigo', '')),
            Paragraph(cnae_sec.get('descricao', ''), small_style)
        ])
    
    cnae_table = Table(cnae_rows, colWidths=[3*cm, 3.5*cm, page_width - 6.5*cm])
    cnae_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BLUE_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (0, 1), GREEN_LIGHT),
        ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 2), (-1, -1), [WHITE, GRAY_LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.5, GRAY_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(cnae_table)
    elements.append(Spacer(1, 0.4*cm))
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 4: QUADRO DE SÓCIOS (QSA)
    # ═══════════════════════════════════════════════════════════
    qsa = data.get('qsa', [])
    if qsa:
        elements.append(Paragraph("4. QUADRO DE SÓCIOS E ADMINISTRADORES", heading_style))
        elements.append(HRFlowable(width="100%", thickness=1, color=BLUE_ACCENT, spaceAfter=8))
        
        qsa_rows = [['Nome', 'Qualificação', 'Entrada', 'Faixa Etária']]
        for socio in qsa:
            qsa_rows.append([
                socio.get('nome_socio', 'N/A'),
                socio.get('qualificacao_socio', 'N/A'),
                _fmt_date(socio.get('data_entrada_sociedade', '')),
                socio.get('faixa_etaria', 'N/A'),
            ])
        
        qsa_table = Table(qsa_rows, colWidths=[
            page_width * 0.35, page_width * 0.3, page_width * 0.17, page_width * 0.18
        ])
        qsa_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BLUE_PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, GRAY_LIGHT]),
            ('GRID', (0, 0), (-1, -1), 0.5, GRAY_BORDER),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(qsa_table)
        elements.append(Spacer(1, 0.4*cm))
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 5: INFORMAÇÕES FISCAIS
    # ═══════════════════════════════════════════════════════════
    section_num = 5 if qsa else 4
    elements.append(Paragraph(f"{section_num}. INFORMAÇÕES FISCAIS E TRIBUTÁRIAS", heading_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=BLUE_ACCENT, spaceAfter=8))
    
    simples = data.get('opcao_pelo_simples')
    mei = data.get('opcao_pelo_mei')
    simples_text = "Sim" if simples else ("Não" if simples == False else "Não informado")
    mei_text = "Sim" if mei else ("Não" if mei == False else "Não informado")
    
    fiscal_rows = [
        ['Campo', 'Informação'],
        ['Simples Nacional', simples_text],
        ['MEI', mei_text],
        ['Capital Social', _fmt_capital(data.get('capital_social', 0))],
    ]
    
    # Add regime tributário if available
    regime = data.get('regime_tributario', '')
    if isinstance(regime, list) and regime:
        ultimo = regime[-1]
        fiscal_rows.append(['Regime Tributário', f"{ultimo.get('forma_de_tributacao', 'N/A')} ({ultimo.get('ano', '')})"])
    
    fiscal_table = Table(fiscal_rows, colWidths=[5*cm, page_width - 5*cm])
    fiscal_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BLUE_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (0, -1), BLUE_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.5, GRAY_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(fiscal_table)
    elements.append(Spacer(1, 0.4*cm))
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 6: STATUS DAS CERTIDÕES
    # ═══════════════════════════════════════════════════════════
    section_num += 1
    elements.append(Paragraph(f"{section_num}. STATUS DAS CERTIDÕES DE REGULARIDADE", heading_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=BLUE_ACCENT, spaceAfter=8))
    
    certidoes = data.get('certidoes', {})
    
    cert_items = [
        ('CND Federal (Receita Federal / PGFN)', certidoes.get('cnd_federal', {})),
        ('CND Estadual PR (SEFAZ/PR)', certidoes.get('cnd_estadual', {})),
        ('Certificado FGTS (Caixa Econômica)', certidoes.get('fgts', {})),
    ]
    
    cert_rows = [['Certidão', 'Status', 'Observação']]
    score_count = 0
    total_certs = 3
    
    for cert_name, cert_data_item in cert_items:
        status = cert_data_item.get('status', 'indisponivel')
        status_text, status_color, bg_color, symbol = _get_status_info(status)
        
        if status == 'regular':
            score_count += 1
            obs = "Situação regular verificada"
        elif status == 'irregular':
            obs = "ATENÇÃO: Pendências identificadas"
        else:
            obs = "Consulta indisponível no momento"
        
        cert_rows.append([cert_name, f"{symbol} {status_text}", obs])
    
    cert_table = Table(cert_rows, colWidths=[page_width * 0.42, page_width * 0.22, page_width * 0.36])
    
    # Build style
    cert_style_commands = [
        ('BACKGROUND', (0, 0), (-1, 0), BLUE_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, GRAY_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]
    
    # Color-code status cells
    for i, (_, cert_data_item) in enumerate(cert_items, start=1):
        status = cert_data_item.get('status', 'indisponivel')
        _, status_color, bg_color, _ = _get_status_info(status)
        cert_style_commands.append(('BACKGROUND', (1, i), (1, i), bg_color))
        cert_style_commands.append(('TEXTCOLOR', (1, i), (1, i), status_color))
    
    cert_table.setStyle(TableStyle(cert_style_commands))
    elements.append(cert_table)
    elements.append(Spacer(1, 0.6*cm))
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 7: ANÁLISE DE CONFORMIDADE
    # ═══════════════════════════════════════════════════════════
    section_num += 1
    elements.append(Paragraph(f"{section_num}. ANÁLISE DE CONFORMIDADE", heading_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=BLUE_ACCENT, spaceAfter=8))
    
    # Calculate score
    score = 0
    score_details = []
    
    # Certidões (60 points)
    cert_score = int((score_count / total_certs) * 60)
    score += cert_score
    score_details.append(f"Certidões: {score_count}/{total_certs} regulares ({cert_score}/60 pts)")
    
    # Situação cadastral (20 points)
    if 'ATIVA' in situacao.upper():
        score += 20
        score_details.append("Situação Cadastral: ATIVA (20/20 pts)")
    else:
        score_details.append(f"Situação Cadastral: {situacao} (0/20 pts)")
    
    # Capital social > 0 (10 points)
    cap = data.get('capital_social', 0)
    try:
        cap_val = float(cap)
    except:
        cap_val = 0
    if cap_val > 0:
        score += 10
        score_details.append(f"Capital Social: {_fmt_capital(cap_val)} (10/10 pts)")
    else:
        score_details.append("Capital Social: Não informado (0/10 pts)")
    
    # QSA exists (10 points)
    if qsa:
        score += 10
        score_details.append(f"Quadro Societário: {len(qsa)} sócio(s) registrado(s) (10/10 pts)")
    else:
        score_details.append("Quadro Societário: Não disponível (0/10 pts)")
    
    # Score classification
    if score >= 80:
        classification = "EXCELENTE"
        class_color = GREEN
        recommendation = "A empresa apresenta excelente nível de conformidade regulatória. Recomenda-se manter o acompanhamento periódico das certidões para garantir a continuidade da regularidade."
    elif score >= 60:
        classification = "BOM"
        class_color = BLUE_ACCENT
        recommendation = "A empresa apresenta bom nível de conformidade, porém existem pontos que merecem atenção. Recomenda-se verificar as pendências identificadas e regularizá-las."
    elif score >= 40:
        classification = "ATENÇÃO"
        class_color = YELLOW
        recommendation = "A empresa apresenta pontos de atenção significativos em sua conformidade regulatória. É necessário tomar medidas corretivas nas áreas identificadas como pendentes."
    else:
        classification = "CRÍTICO"
        class_color = RED
        recommendation = "A empresa apresenta situação crítica de conformidade. Ações imediatas são necessárias para regularização junto aos órgãos competentes."
    
    # Score display with seal
    seal = _create_seal(score)
    
    analysis_text = f"""
    <b>Classificação: {classification}</b><br/><br/>
    <b>Pontuação Detalhada:</b><br/>
    {'<br/>'.join(f'• {d}' for d in score_details)}<br/><br/>
    <b>Recomendação:</b><br/>
    {recommendation}
    """
    
    analysis_style = ParagraphStyle(
        'Analysis', parent=styles['Normal'],
        fontSize=9, spaceAfter=4,
        fontName='Helvetica', leading=14,
    )
    
    analysis_data = [
        [seal, Paragraph(analysis_text, analysis_style)]
    ]
    
    analysis_table = Table(analysis_data, colWidths=[3.5*cm, page_width - 3.5*cm])
    analysis_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), GRAY_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, class_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(analysis_table)
    elements.append(Spacer(1, 0.8*cm))
    
    # ═══════════════════════════════════════════════════════════
    # FOOTER
    # ═══════════════════════════════════════════════════════════
    elements.append(HRFlowable(width="100%", thickness=2, color=BLUE_PRIMARY, spaceAfter=10))
    
    elements.append(Paragraph(
        f"<b>CERTIFICADO DE CONFORMIDADE — IAudit</b>",
        footer_style
    ))
    elements.append(Paragraph(
        f"Emitido em {now} (Horário de Brasília)",
        footer_style
    ))
    elements.append(Paragraph(
        "Informações obtidas de fontes oficiais: Receita Federal (BrasilAPI) e InfoSimples.",
        footer_style
    ))
    elements.append(Paragraph(
        "<i>Este documento tem caráter informativo e não substitui as certidões oficiais emitidas pelos órgãos competentes.</i>",
        footer_style
    ))
    elements.append(Paragraph(
        f"<i>Score de conformidade: {score}/100 — Classificação: {classification}</i>",
        footer_style
    ))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.read()


@router.get("/cnpj/{cnpj}")
async def generate_pdf_report(cnpj: str):
    """Generate compliance certificate PDF for CNPJ."""
    cnpj_clean = cnpj.replace(".", "").replace("/", "").replace("-", "").strip()
    
    if len(cnpj_clean) != 14 or not cnpj_clean.isdigit():
        raise HTTPException(status_code=400, detail="CNPJ inválido")
    
    try:
        data = await query_cnpj(cnpj_clean)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar CNPJ: {str(e)}")
    
    try:
        pdf_bytes = create_certificate_pdf(cnpj_clean, data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar certificado: {str(e)}")
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=certificado_conformidade_{cnpj_clean}.pdf"
        }
    )
