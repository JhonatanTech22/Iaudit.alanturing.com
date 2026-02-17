import streamlit as st
import os
from utils.ui import setup_page

# ─── SETUP ──────────────────────────────────────────────────────────
setup_page(title="IAudit — Automação Fiscal", icon=None, layout="wide")

# ─── CUSTOM CSS ─────────────────────────────────────────────────────
# Visual branding and common styles are now handled globally.


# ─── SIDEBAR ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding: 1rem 0; text-align: center;">
        <div style="font-weight: 700; font-size: 1.5rem; color: #f8fafc; letter-spacing: -0.5px;">
            <span style="color: #60a5fa;">IAudit</span>
        </div>
        <div style="font-size: 0.8rem; color: #64748b; margin-top: 4px;">System v2.1 (Refreshed)</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    domain_name = os.getenv("DOMAIN_NAME", "iaudit.alanturing.com")
    st.caption(f"Connected to: {domain_name}")

# ─── HERO SECTION ────────────────────────────────────────────────────
st.markdown("""
<div class="hero-container">
    <div class="hero-logo-box">
        <svg xmlns="http://www.w3.org/2000/svg" width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            <path d="m9 12 2 2 4-4"/>
        </svg>
    </div>
    <div class="hero-badge">Sistema IAudit</div>
    <h1 class="hero-title">IAudit</h1>
    <div style="font-size: 1.2rem; margin-top: -1rem; color: var(--text-accent); font-weight: 500; opacity: 0.9;">Plataforma de Automação Fiscal</div>
    <p class="hero-subtitle">
        Monitoramento fiscal e conformidade em tempo real. <br>
        Simples, Rápido e Eficiente.
    </p>
</div>
""", unsafe_allow_html=True)

# ─── NAVIGATION CARDS ────────────────────────────────────────────────
c1, c2, c3 = st.columns(3, gap="large")

with c1:
    st.markdown("""
    <div class="glass-card" style="animation: fadeIn 0.6s ease-out 0.2s backwards;">
        <div class="card-icon">📊</div>
        <div class="card-title">Dashboard</div>
        <div class="card-desc">Visualize seus indicadores e o status das empresas.</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Acessar Dashboard", type="primary", use_container_width=True):
        st.switch_page("pages/1_Dashboard.py")

with c2:
    st.markdown("""
    <div class="glass-card" style="animation: fadeIn 0.6s ease-out 0.4s backwards;">
        <div class="card-icon">🏢</div>
        <div class="card-title">Empresas</div>
        <div class="card-desc">Gerencie o cadastro de empresas e filiais.</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Gerenciar Empresas", type="secondary", use_container_width=True):
        st.switch_page("pages/2_Empresas.py")

with c3:
    st.markdown("""
    <div class="glass-card" style="animation: fadeIn 0.6s ease-out 0.6s backwards;">
        <div class="card-icon">⚡</div>
        <div class="card-title">Upload</div>
        <div class="card-desc">Importe dados em massa via planilha.</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Upload de Arquivos", type="secondary", use_container_width=True):
        st.switch_page("pages/3_Carregar.py")

# ─── FOOTER ──────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align: center; margin-top: 6rem; padding-bottom: 2rem; color: #475569;">
    <p style="font-size: 0.875rem;">&copy; 2024 IAudit. Todos os direitos reservados.</p>
</div>
""", unsafe_allow_html=True)
