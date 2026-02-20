import streamlit as st
import os
from utils.ui import setup_page

# ─── SETUP ──────────────────────────────────────────────────────────
setup_page(title="IAudit — Automação Fiscal", icon=None, layout="wide")

# ─── NAVIGATION ───────────────────────────────────────────────────
pages = {
    "": [
        st.Page("app.py", title="Início", icon=None, default=True),
    ],
    "Fiscal": [
        st.Page("views/1_Fiscal/1_Dashboard.py", title="Painel", icon=None),
        st.Page("views/1_Fiscal/2_Empresas.py", title="Empresas", icon=None),
        st.Page("views/1_Fiscal/3_Carregar.py", title="Upload", icon=None),
        st.Page("views/1_Fiscal/6_Agendamentos.py", title="Agendas", icon=None),
        st.Page("views/1_Fiscal/4_Detalhes.py", title="Monitor", icon=None),
    ],
    "Financeiro": [
        st.Page("views/2_Financeiro/8_Cobrancas.py", title="Cobranças", icon=None),
    ],
}

pg = st.navigation(pages)

# ─── SIDEBAR ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding: 1.25rem 0; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.06); margin-bottom: 0.5rem;">
        <div style="display: flex; align-items: center; justify-content: center; gap: 10px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                <path d="m9 12 2 2 4-4"/>
            </svg>
            <span style="font-weight: 800; font-size: 1.4rem; color: #f8fafc; letter-spacing: -0.5px;">IAudit</span>
        </div>
        <div style="font-size: 0.7rem; color: #475569; margin-top: 6px; letter-spacing: 0.08em; text-transform: uppercase;">Automação Fiscal & Cobranças</div>
    </div>
    """, unsafe_allow_html=True)

    domain_name = os.getenv("DOMAIN_NAME", "iaudit.alanturing.com")
    st.caption(f"Conectado a: {domain_name}")

# ─── HOME PAGE ────────────────────────────────────────────────────────
if pg.title == "Início":

    # Hero
    st.markdown("""
    <div style="text-align: center; padding: 3rem 1rem 2rem; position: relative;">
        <div style="
            position: absolute; top: -30%; left: 50%; transform: translateX(-50%);
            width: 600px; height: 400px;
            background: radial-gradient(circle, rgba(59,130,246,0.12) 0%, transparent 60%);
            filter: blur(60px); pointer-events: none; z-index: 0;
        "></div>
        <div style="position: relative; z-index: 1;">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(0 0 20px rgba(59,130,246,0.5)); margin-bottom: 1rem;">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                <path d="m9 12 2 2 4-4"/>
            </svg>
            <div style="font-size: 0.75rem; color: #60a5fa; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.75rem;">IAudit v2.2</div>
            <h1 style="font-size: clamp(2rem, 5vw, 3.5rem); font-weight: 800; color: #f1f5f9; margin: 0; letter-spacing: -0.03em;">
                Automação <span style="color: #60a5fa;">Fiscal</span> & <span style="color: #10b981;">Cobranças</span>
            </h1>
            <p style="color: #94a3b8; font-size: 1.05rem; margin-top: 0.75rem; max-width: 500px; margin-left: auto; margin-right: auto; line-height: 1.6;">
                Gerencie auditorias, certidões, cobranças e notificações em uma plataforma unificada.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # ─── MODULE CARDS ────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="glass-card" style="animation: fadeIn 0.6s ease-out 0.2s backwards; min-height: 200px;">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1rem;">
                <div style="width: 40px; height: 40px; border-radius: 10px; background: rgba(59,130,246,0.15); display: flex; align-items: center; justify-content: center;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                        <path d="m9 12 2 2 4-4"/>
                    </svg>
                </div>
                <div class="card-title" style="margin: 0;">Módulo Fiscal</div>
            </div>
            <div class="card-desc" style="margin-bottom: 0.75rem;">Dashboard de conformidade, monitoramento de certidões e indicadores fiscais das empresas.</div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                <span style="font-size: 0.7rem; color: #94a3b8; background: rgba(255,255,255,0.05); padding: 4px 10px; border-radius: 20px;">Dashboard</span>
                <span style="font-size: 0.7rem; color: #94a3b8; background: rgba(255,255,255,0.05); padding: 4px 10px; border-radius: 20px;">Empresas</span>
                <span style="font-size: 0.7rem; color: #94a3b8; background: rgba(255,255,255,0.05); padding: 4px 10px; border-radius: 20px;">Agendamentos</span>
                <span style="font-size: 0.7rem; color: #94a3b8; background: rgba(255,255,255,0.05); padding: 4px 10px; border-radius: 20px;">Monitor</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Acessar Painel Fiscal", type="primary", use_container_width=True, key="btn_fiscal"):
            st.switch_page("views/1_Fiscal/1_Dashboard.py")

    with col2:
        st.markdown("""
        <div class="glass-card" style="animation: fadeIn 0.6s ease-out 0.4s backwards; min-height: 200px;">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1rem;">
                <div style="width: 40px; height: 40px; border-radius: 10px; background: rgba(16,185,129,0.12); display: flex; align-items: center; justify-content: center;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="12" y1="1" x2="12" y2="23"/>
                        <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
                    </svg>
                </div>
                <div class="card-title" style="margin: 0;">Financeiro</div>
            </div>
            <div class="card-desc" style="margin-bottom: 0.75rem;">Gestão de cobranças via API Bradesco, boletos, notificações WhatsApp/Email e régua de cobrança automatizada.</div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                <span style="font-size: 0.7rem; color: #94a3b8; background: rgba(255,255,255,0.05); padding: 4px 10px; border-radius: 20px;">Boletos</span>
                <span style="font-size: 0.7rem; color: #94a3b8; background: rgba(255,255,255,0.05); padding: 4px 10px; border-radius: 20px;">Notificações</span>
                <span style="font-size: 0.7rem; color: #94a3b8; background: rgba(255,255,255,0.05); padding: 4px 10px; border-radius: 20px;">Bradesco API</span>
                <span style="font-size: 0.7rem; color: #94a3b8; background: rgba(255,255,255,0.05); padding: 4px 10px; border-radius: 20px;">Retry Queue</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Gestão Financeira", type="secondary", use_container_width=True, key="btn_financeiro"):
            st.switch_page("views/2_Financeiro/8_Cobrancas.py")

    # ─── QUICK ACCESS ────────────────────────────────────────────────
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; margin-bottom: 1rem;">
        <span style="font-size: 0.7rem; color: #475569; letter-spacing: 0.1em; text-transform: uppercase; font-weight: 600;">Acesso Rápido</span>
    </div>
    """, unsafe_allow_html=True)

    qa1, qa2, qa3, qa4 = st.columns(4, gap="small")

    with qa1:
        if st.button("Empresas", use_container_width=True, key="qa_empresas"):
            st.switch_page("views/1_Fiscal/2_Empresas.py")
    with qa2:
        if st.button("Upload CSV", use_container_width=True, key="qa_upload"):
            st.switch_page("views/1_Fiscal/3_Carregar.py")
    with qa3:
        if st.button("Agendas", use_container_width=True, key="qa_agendas"):
            st.switch_page("views/1_Fiscal/6_Agendamentos.py")
    with qa4:
        if st.button("Cobranças", use_container_width=True, key="qa_cobrancas"):
            st.switch_page("views/2_Financeiro/8_Cobrancas.py")

else:
    pg.run()

# ─── FOOTER ──────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align: center; margin-top: 4rem; padding-bottom: 1.5rem; color: #475569;">
    <div style="width: 60px; height: 1px; background: rgba(255,255,255,0.06); margin: 0 auto 1rem;"></div>
    <p style="font-size: 0.8rem; margin: 0;">IAudit &mdash; Plataforma de Automação Fiscal & Cobranças</p>
    <p style="font-size: 0.7rem; margin-top: 4px; color: #334155;">&copy; 2026 IAudit. Todos os direitos reservados.</p>
</div>
""", unsafe_allow_html=True)
