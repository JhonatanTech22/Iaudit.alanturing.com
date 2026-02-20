"""IAudit - Gestão de Cobranças & Notificações."""

import streamlit as st
import httpx
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ui import setup_page

# ─── SETUP ──────────────────────────────────────────────────────────
setup_page(title="IAudit — Cobranças", icon=None, layout="wide")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def fetch(endpoint: str, params: dict | None = None):
    try:
        r = httpx.get(f"{BACKEND_URL}{endpoint}", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def post(endpoint: str, payload: dict):
    try:
        r = httpx.post(f"{BACKEND_URL}{endpoint}", json=payload, timeout=15)
        if r.status_code >= 400:
            try:
                body = r.json()
            except Exception:
                body = {"detail": r.text}
            return {"error": body.get("detail", body)}
        return r.json()
    except Exception as e:
        return {"error": str(e)}


# ─── HEADER ──────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom: 2rem; padding: 1.5rem; background: linear-gradient(90deg, rgba(16,185,129,0.25) 0%, rgba(6,78,59,0.08) 100%); border-radius: 14px; border: 1px solid rgba(255,255,255,0.05);">
    <h1 style="margin: 0; font-size: 1.8rem; color: #f8fafc;">Gestão de Cobranças</h1>
    <p style="margin: 0.3rem 0 0; color: #94a3b8; font-size: 0.9rem;">Boletos Bradesco, notificações omnichannel e régua de cobrança automatizada</p>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════
# 1. SYSTEM STATUS (Health + Queue)
# ═══════════════════════════════════════════════════════════════════════

health = fetch("/api/health")

col1, col2, col3, col4 = st.columns(4)

if health:
    queue = health.get("notification_queue", {})
    jobs = health.get("jobs", [])
    scheduler_on = health.get("scheduler_running", False)

    venc_job = next((j for j in jobs if j["id"] == "boleto_vencimentos"), None)
    monitor_job = next((j for j in jobs if j["id"] == "monitor_boletos"), None)

    with col1:
        st.markdown(f"""
        <div class="glass-card" style="text-align: center; padding: 1.2rem;">
            <div style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem;">Fila de Envio</div>
            <div style="font-size: 2rem; font-weight: 800; color: #10b981;">{queue.get('pending', 0)}</div>
            <div style="font-size: 0.7rem; color: #64748b; margin-top: 0.25rem;">pendentes</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="glass-card" style="text-align: center; padding: 1.2rem;">
            <div style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem;">Enviadas</div>
            <div style="font-size: 2rem; font-weight: 800; color: #3b82f6;">{queue.get('sent', 0)}</div>
            <div style="font-size: 0.7rem; color: #64748b; margin-top: 0.25rem;">com sucesso</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        failed = queue.get('failed', 0)
        fail_color = "#ef4444" if failed > 0 else "#22c55e"
        st.markdown(f"""
        <div class="glass-card" style="text-align: center; padding: 1.2rem;">
            <div style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem;">Falhas</div>
            <div style="font-size: 2rem; font-weight: 800; color: {fail_color};">{failed}</div>
            <div style="font-size: 0.7rem; color: #64748b; margin-top: 0.25rem;">após 3 retries</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        status_color = "#22c55e" if scheduler_on else "#ef4444"
        status_text = "Ativo" if scheduler_on else "Inativo"
        next_run = venc_job["next_run"][:16] if venc_job and venc_job.get("next_run") else "—"
        st.markdown(f"""
        <div class="glass-card" style="text-align: center; padding: 1.2rem;">
            <div style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem;">Scheduler</div>
            <div style="font-size: 1.2rem; font-weight: 700; color: {status_color};">{status_text}</div>
            <div style="font-size: 0.65rem; color: #64748b; margin-top: 0.25rem;">Próx. D-1/D+1: {next_run}</div>
        </div>
        """, unsafe_allow_html=True)
else:
    for c in [col1, col2, col3, col4]:
        with c:
            st.markdown("""
            <div class="glass-card" style="text-align: center; padding: 1.2rem;">
                <div style="font-size: 0.8rem; color: #64748b;">Aguardando backend...</div>
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════
# 2. TABS
# ═══════════════════════════════════════════════════════════════════════

tab_emitir, tab_consultar, tab_notificar, tab_sistema = st.tabs([
    "Emitir Boleto", "Consultar Status", "Notificação Manual", "Arquitetura"
])


# ─── TAB 1: EMITIR BOLETO ───────────────────────────────────────────
with tab_emitir:
    st.markdown("### Emissão de Boleto via API Bradesco")

    with st.form("form_emitir", clear_on_submit=False):
        c1, c2 = st.columns(2)

        with c1:
            pagador_nome = st.text_input("Nome do Pagador", placeholder="Fulano Silva Ltda")
            pagador_doc = st.text_input("CPF/CNPJ do Pagador", placeholder="12.345.678/0001-90")
            valor = st.number_input("Valor (R$)", min_value=0.01, step=0.01, value=150.00)

        with c2:
            vencimento = st.date_input("Vencimento")
            pagador_email = st.text_input("Email para Notificação", placeholder="contato@empresa.com")
            pagador_whatsapp = st.text_input("WhatsApp (opcional)", placeholder="+5541999990000")

        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

        c_end1, c_end2 = st.columns(2)
        with c_end1:
            endereco = st.text_input("Endereço", placeholder="Rua XV de Novembro, 100")
        with c_end2:
            e1, e2, e3 = st.columns(3)
            with e1:
                cidade = st.text_input("Cidade", value="Curitiba")
            with e2:
                uf = st.text_input("UF", value="PR", max_chars=2)
            with e3:
                cep = st.text_input("CEP", placeholder="80000-000")

        submitted = st.form_submit_button("Registrar Boleto", type="primary", use_container_width=True)

        if submitted:
            if not pagador_nome or not pagador_doc or valor <= 0:
                st.error("Preencha nome, CPF/CNPJ e valor.")
            else:
                with st.spinner("Registrando boleto na API Bradesco..."):
                    payload = {
                        "pagador_nome": pagador_nome,
                        "pagador_documento": pagador_doc,
                        "vlNominal": int(valor * 100),
                        "dataVencimento": vencimento.strftime("%Y-%m-%d"),
                        "pagador_email": pagador_email or None,
                        "pagador_whatsapp": pagador_whatsapp or None,
                        "pagador_endereco": endereco,
                        "pagador_cidade": cidade,
                        "pagador_uf": uf,
                        "pagador_cep": cep.replace("-", ""),
                        "pagador_bairro": "Centro",
                        "nuFatura": f"FAT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    }

                    result = post("/api/cobranca/registrar", payload)

                    if result and result.get("status") == "sucesso":
                        st.success(f"Boleto registrado! Nosso Número: **{result.get('nosso_numero')}**")
                        st.code(result.get("linha_digitavel", ""), language=None)
                        if pagador_email:
                            st.info(f"Notificação enviada para {pagador_email}")
                    elif result and result.get("error"):
                        st.error(f"Erro: {result['error']}")
                    else:
                        st.error(f"Falha: {result}")


# ─── TAB 2: CONSULTAR STATUS ────────────────────────────────────────
with tab_consultar:
    st.markdown("### Consultar Status de Boleto")

    col_search, col_btn = st.columns([3, 1])
    with col_search:
        nosso_numero = st.text_input("Nosso Número", placeholder="Ex: 1234567890", label_visibility="collapsed")
    with col_btn:
        btn_search = st.button("Consultar", type="primary", use_container_width=True, key="btn_consultar")

    if btn_search and nosso_numero:
        with st.spinner("Consultando status na API Bradesco..."):
            result = fetch(f"/api/cobranca/{nosso_numero}/status")

            if result:
                status = result.get("status", "desconhecido")
                status_colors = {
                    "emitido": ("#3b82f6", "Emitido / A Vencer"),
                    "pago": ("#22c55e", "Pago"),
                    "atraso": ("#ef4444", "Em Atraso"),
                    "baixado": ("#94a3b8", "Baixado / Cancelado"),
                    "erro": ("#ef4444", "Erro"),
                }
                color, label = status_colors.get(status, ("#94a3b8", status.title()))

                st.markdown(f"""
                <div class="glass-card" style="padding: 1.5rem; margin-top: 1rem;">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1rem;">
                        <div style="width: 12px; height: 12px; border-radius: 50%; background: {color};"></div>
                        <span style="font-size: 1.2rem; font-weight: 700; color: {color};">{label}</span>
                    </div>
                    <div style="font-size: 0.85rem; color: #94a3b8;">
                        Nosso Número: <b style="color: #f8fafc;">{result.get('nosso_numero')}</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                with st.expander("Detalhes da API Bradesco"):
                    st.json(result.get("details", {}))
            else:
                st.warning("Boleto não encontrado ou backend indisponível.")

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    st.markdown("---")

    # ── Search by CNPJ ───────────────────────────────────────────────
    st.markdown("### Buscar por CNPJ")

    col_cnpj, col_cnpj_btn = st.columns([3, 1])
    with col_cnpj:
        cnpj_input = st.text_input("CNPJ", placeholder="12.345.678/0001-90", label_visibility="collapsed", key="cnpj_search")
    with col_cnpj_btn:
        btn_cnpj = st.button("Buscar", type="secondary", use_container_width=True, key="btn_cnpj")

    if btn_cnpj and cnpj_input:
        with st.spinner("Buscando empresa..."):
            result = fetch("/api/cobranca/search", params={"cnpj": cnpj_input})

            if result and result.get("found"):
                empresa = result["empresa"]
                st.success(f"Empresa: **{empresa['razao_social']}**")

                boletos = result.get("boletos", [])
                if boletos:
                    st.markdown(f"**{len(boletos)}** boleto(s) encontrado(s):")
                    for b in boletos[:10]:
                        status = b.get("status", "—")
                        color = "#22c55e" if status == "pago" else "#3b82f6" if status == "emitido" else "#ef4444"
                        st.markdown(f"""
                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.6rem 1rem; background: rgba(255,255,255,0.03); border-radius: 8px; margin-bottom: 0.4rem; border: 1px solid rgba(255,255,255,0.04);">
                            <span style="color: #f8fafc; font-size: 0.85rem;">{b.get('nosso_numero', '—')}</span>
                            <span style="color: #94a3b8; font-size: 0.8rem;">R$ {b.get('valor', 0):.2f}</span>
                            <span style="color: {color}; font-weight: 600; font-size: 0.8rem;">{status.upper()}</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Nenhum boleto encontrado para esta empresa.")
            else:
                st.warning("Empresa não encontrada.")


# ─── TAB 3: NOTIFICAÇÃO MANUAL ──────────────────────────────────────
with tab_notificar:
    st.markdown("### Disparo Manual de Notificação")
    st.markdown(
        "<p style='color: #94a3b8; font-size: 0.85rem;'>Envie uma notificação avulsa via WhatsApp e/ou Email para um boleto específico.</p>",
        unsafe_allow_html=True,
    )

    with st.form("form_notify", clear_on_submit=False):
        cn1, cn2 = st.columns(2)

        with cn1:
            n_nosso = st.text_input("Nosso Número", key="n_nosso")
            n_nome = st.text_input("Nome da Empresa/Pagador", key="n_nome")
            n_valor = st.number_input("Valor (R$)", min_value=0.01, value=100.00, key="n_valor")

        with cn2:
            n_venc = st.text_input("Vencimento (DD/MM/AAAA)", key="n_venc")
            n_email = st.text_input("Email", key="n_email")
            n_whatsapp = st.text_input("WhatsApp", placeholder="+5541999990000", key="n_whatsapp")

        n_linha = st.text_input("Linha Digitável", key="n_linha")

        n_event = st.selectbox(
            "Tipo de Evento",
            ["emitido", "pago", "atraso", "vencimento_d1", "reativado"],
            index=0,
            key="n_event",
        )

        event_descriptions = {
            "emitido": "Nova fatura — envia boleto com linha digitável e link PDF",
            "pago": "Confirmação de pagamento — agradece e confirma quitação",
            "atraso": "Aviso de atraso — alerta sobre juros e multa",
            "vencimento_d1": "Lembrete — boleto vence amanhã",
            "reativado": "Reativação — boleto foi estornado e está ativo novamente",
        }
        st.markdown(
            f"<p style='font-size: 0.75rem; color: #64748b; margin-top: -0.5rem;'>{event_descriptions.get(n_event, '')}</p>",
            unsafe_allow_html=True,
        )

        btn_notify = st.form_submit_button("Enviar Notificação", type="primary", use_container_width=True)

        if btn_notify:
            if not n_nosso or (not n_email and not n_whatsapp):
                st.error("Informe o Nosso Número e pelo menos um canal (Email ou WhatsApp).")
            else:
                with st.spinner("Enviando notificação..."):
                    payload = {
                        "nosso_numero": n_nosso,
                        "empresa_nome": n_nome,
                        "valor": n_valor,
                        "vencimento": n_venc,
                        "linha_digitavel": n_linha,
                        "link_boleto": f"{BACKEND_URL}/api/boleto/pdf/{n_nosso}",
                        "email": n_email or None,
                        "whatsapp": n_whatsapp or None,
                        "event_type": n_event,
                    }

                    result = post("/api/cobranca/notify-manual", payload)

                    if result and result.get("status") == "sent":
                        st.success(result.get("message", "Notificação enviada!"))
                    else:
                        st.error(f"Falha: {result}")


# ─── TAB 4: ARQUITETURA DO SISTEMA ──────────────────────────────────
with tab_sistema:
    st.markdown("### Arquitetura do Sistema de Notificações")

    st.markdown("""
    <div class="glass-card" style="padding: 1.5rem; margin-bottom: 1.5rem;">
        <h4 style="color: #f8fafc; margin: 0 0 1rem;">Fluxo de Notificações</h4>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">

            <div style="background: rgba(59,130,246,0.1); border: 1px solid rgba(59,130,246,0.2); border-radius: 10px; padding: 1rem;">
                <div style="font-size: 0.7rem; color: #60a5fa; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;">Trigger A</div>
                <div style="font-weight: 600; color: #f8fafc; font-size: 0.9rem;">Boleto Emitido</div>
                <div style="color: #94a3b8; font-size: 0.75rem; margin-top: 0.3rem;">Registro via API Bradesco → Notifica "Nova Fatura" com linha digitável + QR Pix</div>
            </div>

            <div style="background: rgba(34,197,94,0.1); border: 1px solid rgba(34,197,94,0.2); border-radius: 10px; padding: 1rem;">
                <div style="font-size: 0.7rem; color: #22c55e; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;">Trigger B</div>
                <div style="font-weight: 600; color: #f8fafc; font-size: 0.9rem;">Pagamento Confirmado</div>
                <div style="color: #94a3b8; font-size: 0.75rem; margin-top: 0.3rem;">Webhook/Monitoring detecta status 61/13 → Notifica "Pagamento Recebido"</div>
            </div>

            <div style="background: rgba(245,158,11,0.1); border: 1px solid rgba(245,158,11,0.2); border-radius: 10px; padding: 1rem;">
                <div style="font-size: 0.7rem; color: #f59e0b; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;">Trigger C</div>
                <div style="font-weight: 600; color: #f8fafc; font-size: 0.9rem;">Vencimento D-1 / D+1</div>
                <div style="color: #94a3b8; font-size: 0.75rem; margin-top: 0.3rem;">Cron diário 07:00 → "Lembrete" (D-1) ou "Aviso de Atraso" (D+1)</div>
            </div>

            <div style="background: rgba(139,92,246,0.1); border: 1px solid rgba(139,92,246,0.2); border-radius: 10px; padding: 1rem;">
                <div style="font-size: 0.7rem; color: #a78bfa; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;">Trigger D</div>
                <div style="font-weight: 600; color: #f8fafc; font-size: 0.9rem;">Estorno / Reativação</div>
                <div style="color: #94a3b8; font-size: 0.75rem; margin-top: 0.3rem;">Endpoint /estorno → Notifica "Boleto Reativado"</div>
            </div>

        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Technical Stack ──────────────────────────────────────────────
    st.markdown("""
    <div class="glass-card" style="padding: 1.5rem; margin-bottom: 1.5rem;">
        <h4 style="color: #f8fafc; margin: 0 0 1rem;">Stack Técnico</h4>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div>
                <div style="font-size: 0.7rem; color: #60a5fa; text-transform: uppercase; margin-bottom: 0.5rem; letter-spacing: 0.08em;">Canais</div>
                <div style="color: #94a3b8; font-size: 0.85rem; line-height: 1.8;">
                    <div>WhatsApp via <b style="color: #f8fafc;">Twilio</b></div>
                    <div>Email via <b style="color: #f8fafc;">Resend / SMTP Gmail</b></div>
                </div>
            </div>
            <div>
                <div style="font-size: 0.7rem; color: #10b981; text-transform: uppercase; margin-bottom: 0.5rem; letter-spacing: 0.08em;">Resiliência</div>
                <div style="color: #94a3b8; font-size: 0.85rem; line-height: 1.8;">
                    <div>Retry Queue com <b style="color: #f8fafc;">Exponential Backoff</b></div>
                    <div>Max 3 tentativas (1s → 2s → 4s)</div>
                </div>
            </div>
            <div>
                <div style="font-size: 0.7rem; color: #f59e0b; text-transform: uppercase; margin-bottom: 0.5rem; letter-spacing: 0.08em;">Segurança</div>
                <div style="color: #94a3b8; font-size: 0.85rem; line-height: 1.8;">
                    <div>TLS 1.2 + <b style="color: #f8fafc;">AES-128-GCM-SHA256</b></div>
                    <div>OAuth2 JWT Profile (RS256)</div>
                </div>
            </div>
            <div>
                <div style="font-size: 0.7rem; color: #a78bfa; text-transform: uppercase; margin-bottom: 0.5rem; letter-spacing: 0.08em;">Arquitetura</div>
                <div style="color: #94a3b8; font-size: 0.85rem; line-height: 1.8;">
                    <div>SOLID Provider Pattern (ABC)</div>
                    <div>Clean Architecture + APScheduler</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Scheduled Jobs ───────────────────────────────────────────────
    st.markdown("#### Jobs Agendados")

    if health and health.get("jobs"):
        for job in health["jobs"]:
            next_run = job.get("next_run", "—")
            if next_run and next_run != "None":
                next_run = next_run[:19].replace("T", " ")
            else:
                next_run = "—"

            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.7rem 1rem; background: rgba(255,255,255,0.03); border-radius: 8px; margin-bottom: 0.4rem; border: 1px solid rgba(255,255,255,0.04);">
                <div>
                    <span style="color: #f8fafc; font-size: 0.85rem; font-weight: 600;">{job.get('name', job['id'])}</span>
                    <span style="color: #64748b; font-size: 0.7rem; margin-left: 0.5rem;">({job['id']})</span>
                </div>
                <span style="color: #94a3b8; font-size: 0.8rem;">{next_run}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Backend indisponível — não foi possível listar os jobs agendados.")
