import streamlit as st
import os
from utils.ui import setup_page

# ─── SETUP ──────────────────────────────────────────────────────────
setup_page(title="IAudit — Automação Fiscal", icon=None, layout="wide")

# ─── CUSTOM CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Global Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }
    
    @keyframes glow {
        0% { text-shadow: 0 0 20px rgba(96, 165, 250, 0.2); }
        50% { text-shadow: 0 0 40px rgba(96, 165, 250, 0.5), 0 0 10px rgba(255, 255, 255, 0.3); }
        100% { text-shadow: 0 0 20px rgba(96, 165, 250, 0.2); }
    }

    /* Hero Section */
    .hero-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 4rem 1rem 6rem 1rem;
        background: radial-gradient(circle at center, rgba(30, 41, 59, 0.3) 0%, rgba(15, 23, 42, 0) 70%);
        animation: fadeIn 1s ease-out;
    }
    
    .hero-logo-box {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100px;
        height: 100px;
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(30, 41, 59, 0.2));
        border-radius: 24px;
        border: 1px solid rgba(96, 165, 250, 0.3);
        box-shadow: 0 0 40px rgba(59, 130, 246, 0.15);
        margin-bottom: 2rem;
        animation: float 6s ease-in-out infinite;
        backdrop-filter: blur(10px);
    }
    
    .hero-title {
        font-size: 5rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #ffffff 0%, #94a3b8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -2px;
        animation: glow 4s infinite;
    }
    
    .hero-subtitle {
        font-size: 1.5rem;
        color: #94a3b8;
        font-weight: 300;
        margin-bottom: 3rem;
        text-align: center;
        max-width: 600px;
        line-height: 1.6;
    }

    .hero-badge {
        background: rgba(59, 130, 246, 0.1);
        color: #60a5fa;
        padding: 0.5rem 1rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 600;
        border: 1px solid rgba(59, 130, 246, 0.2);
        margin-bottom: 1.5rem;
        display: inline-block;
    }

    /* Glass Cards */
    .glass-card {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 24px;
        padding: 2rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        height: 100%;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(10px);
    }
    
    .glass-card::before {
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0) 100%);
        z-index: 0;
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-5px);
        background: rgba(30, 41, 59, 0.6);
        border-color: rgba(96, 165, 250, 0.3);
        box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.3);
    }
    
    .glass-card:hover::before {
        opacity: 1;
    }
    
    .card-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
    }
    
    .card-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #f8fafc;
        margin-bottom: 0.5rem;
        position: relative;
        z-index: 1;
    }
    
    .card-desc {
        color: #94a3b8;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
        position: relative;
        z-index: 1;
    }
    
    /* Custom Button Style override */
    div.stButton > button {
        width: 100%;
        border-radius: 12px;
        font-weight: 600;
        height: 48px;
        transition: all 0.2s ease;
    }
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding: 1rem 0; text-align: center;">
        <div style="font-weight: 700; font-size: 1.5rem; color: #f8fafc; letter-spacing: -0.5px;">
            <span style="color: #60a5fa;">IAudit</span>
        </div>
        <div style="font-size: 0.8rem; color: #64748b; margin-top: 4px;">System v2.0</div>
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
