"""IAudit - CSV/Excel Upload Page."""

import streamlit as st
import httpx
import pandas as pd
import io
import os
import re

from utils.ui import setup_page
import utils.new_modules as addons

# Configure page & load global CSS (Theme persistence)
setup_page(title="IAudit — Upload", icon="📤")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def validate_cnpj_frontend(cnpj: str) -> bool:
    """Quick CNPJ validation (check digits) for preview."""
    cnpj = re.sub(r"\D", "", cnpj)
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False
    w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    s = sum(int(cnpj[i]) * w1[i] for i in range(12))
    r = s % 11
    d1 = 0 if r < 2 else 11 - r
    if int(cnpj[12]) != d1:
        return False
    w2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    s = sum(int(cnpj[i]) * w2[i] for i in range(13))
    r = s % 11
    d2 = 0 if r < 2 else 11 - r
    return int(cnpj[13]) == d2


# ─── Header ──────────────────────────────────────────────────────────
# ─── Header ──────────────────────────────────────────────────────────
st.markdown("""
<div class="iaudit-header">
<h1>📤 Upload de Empresas</h1>
<p>Cadastro em lote via CSV ou Excel</p>
</div>
""", unsafe_allow_html=True)

# ─── Instructions ────────────────────────────────────────────────────
with st.expander("📋 Formato do Arquivo", expanded=False):
    st.markdown("""
O arquivo deve conter as seguintes colunas:

| Coluna | Obrigatória | Descrição |
|--------|:-----------:|-----------|
| `cnpj` | ✅ | CNPJ da empresa (com ou sem formatação) |
| `razao_social` | ✅ | Razão social da empresa |
| `inscricao_estadual_pr` | ❌ | Inscrição Estadual do Paraná |
| `email_notificacao` | ❌ | Email para receber alertas |
| `whatsapp` | ❌ | WhatsApp para notificações |

**Formatos aceitos:** `.csv`, `.xlsx`, `.xls`
""")

    # Download template
    template_df = pd.DataFrame({
        "cnpj": ["11222333000181", "99888777000166"],
        "razao_social": ["Empresa Exemplo LTDA", "Empresa Teste SA"],
        "inscricao_estadual_pr": ["1234567890", ""],
        "email_notificacao": ["fiscal@exemplo.com", ""],
        "whatsapp": ["41999999999", ""],
    })
    csv_template = template_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Baixar Template CSV",
        csv_template,
        "template_iaudit.csv",
        "text/csv",
    )

# ─── Upload ──────────────────────────────────────────────────────────
tab_upload, tab_bulk = st.tabs(["📁 Upload de Arquivo", "📋 Importação em Lote"])

with tab_upload:
    st.markdown("### 📁 Selecione o Arquivo")

uploaded_file = st.file_uploader(
    "Arraste ou selecione um arquivo CSV/Excel",
    type=["csv", "xlsx", "xls"],
    help="Formatos aceitos: CSV, XLSX, XLS",
)

if uploaded_file:
    # Read file
    try:
        content = uploaded_file.read()
        if uploaded_file.name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(content))
        else:
            for enc in ["utf-8", "latin-1", "cp1252"]:
                try:
                    df = pd.read_csv(io.BytesIO(content), encoding=enc)
                    break
                except UnicodeDecodeError:
                    continue

        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        if "cnpj" not in df.columns or "razao_social" not in df.columns:
            st.error("❌ O arquivo deve conter as colunas `cnpj` e `razao_social`.")
        else:
            # Validate CNPJs
            df["cnpj_limpo"] = df["cnpj"].astype(str).apply(lambda x: re.sub(r"\D", "", x))
            df["cnpj_valido"] = df["cnpj_limpo"].apply(validate_cnpj_frontend)
            df["status_validacao"] = df["cnpj_valido"].map({
                True: "✅ Válido",
                False: "❌ Inválido"
            })

            # Preview
            st.markdown(f"### 👁️ Preview — {len(df)} empresa(s) encontrada(s)")

            valid_count = df["cnpj_valido"].sum()
            invalid_count = len(df) - valid_count

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Total", len(df))
            with c2:
                st.metric("✅ Válidos", int(valid_count))
            with c3:
                st.metric("❌ Inválidos", int(invalid_count))

            # Show preview table
            preview_cols = ["cnpj", "razao_social", "status_validacao"]
            for col in ["inscricao_estadual_pr", "email_notificacao", "whatsapp"]:
                if col in df.columns:
                    preview_cols.insert(-1, col)

            st.dataframe(
                df[preview_cols].rename(columns={
                    "cnpj": "CNPJ",
                    "razao_social": "Razão Social",
                    "inscricao_estadual_pr": "IE PR",
                    "email_notificacao": "Email",
                    "whatsapp": "WhatsApp",
                    "status_validacao": "Validação",
                }),
                use_container_width=True,
                hide_index=True,
            )

            # Scheduling config
            st.markdown("### ⚙️ Configuração de Agendamento")
            c1, c2 = st.columns(2)
            with c1:
                periodicidade = st.selectbox(
                    "Periodicidade",
                    ["diario", "semanal", "quinzenal", "mensal"],
                    index=3,
                )
            with c2:
                horario = st.time_input("Horário das Consultas", value=None)
                horario_str = horario.strftime("%H:%M:%S") if horario else "08:00:00"

            # Submit
            st.markdown("---")
            if st.button("🚀 Enviar e Cadastrar Empresas", type="primary"):
                with st.spinner("Processando upload..."):
                    try:
                        uploaded_file.seek(0)
                        files = {"file": (uploaded_file.name, uploaded_file.read(), uploaded_file.type)}
                        params = {
                            "periodicidade": periodicidade,
                            "horario": horario_str,
                        }
                        r = httpx.post(
                            f"{BACKEND_URL}/api/empresas/upload",
                            files=files,
                            params=params,
                            timeout=60,
                        )
                        r.raise_for_status()
                        result = r.json()

                        st.markdown("### 📊 Resultado do Upload")
                        r1, r2, r3, r4 = st.columns(4)
                        with r1:
                            st.metric("Total", result.get("total", 0))
                        with r2:
                            st.metric("✅ Criadas", result.get("criadas", 0))
                        with r3:
                            st.metric("🔄 Duplicadas", result.get("duplicadas", 0))
                        with r4:
                            st.metric("❌ Inválidas", result.get("invalidas", 0))

                        erros = result.get("erros", [])
                        if erros:
                            with st.expander(f"⚠️ {len(erros)} erro(s) encontrado(s)"):
                                for erro in erros:
                                    st.text(erro)

                        if result.get("criadas", 0) > 0:
                            st.success(
                                f"✅ {result['criadas']} empresa(s) cadastrada(s) com sucesso!"
                            )
                            st.balloons()

                    except httpx.HTTPError as e:
                        error_msg = str(e)
                        if hasattr(e, 'response') and e.response is not None:
                            try:
                                error_msg = e.response.json().get('detail', error_msg)
                            except:
                                pass
                        st.error(f"❌ Erro no upload: {error_msg}")
                    except Exception as e:
                        st.error(f"❌ Erro inesperado: {e}")

                        st.error(f"❌ Erro inesperado: {e}")

    except Exception as e:
        st.error(f"❌ Erro ao ler arquivo: {e}")

with tab_bulk:
    st.markdown("### 📋 Importação em Lote (Copy & Paste)")
    st.markdown("Cole sua lista de CNPJs abaixo to processar sequencialmente.")
    
    bulk_input = st.text_area("Lista de CNPJs (um por linha ou separados por vírgula)", height=150)
    
    if st.button("🚀 Iniciar Processamento em Lote"):
        if not bulk_input:
            st.warning("⚠️ Cole uma lista de CNPJs para começar.")
        else:
            # Parse Input
            import re
            raw_cnpjs = re.split(r'[,\n\s]+', bulk_input)
            cnpjs = [c for c in raw_cnpjs if c.strip()]
            
            if not cnpjs:
                 st.warning("⚠️ Nenhum CNPJ válido identificado.")
            else:
                st.info(f"Iniciando processamento de {len(cnpjs)} empresas...")
                progress_bar = st.progress(0, text="Aguardando início...")
                
                # Run the loop
                addons.process_bulk_list(cnpjs, progress_bar)
                
                st.success("✅ Processamento concluído!")
                
    # Display Results
    if 'bulk_results' in st.session_state and st.session_state['bulk_results']:
        st.markdown("### 📊 Relatório de Processamento")
        results = st.session_state['bulk_results']
        
        # Simple Dataframe view
        df_bulk = pd.DataFrame(results)
        st.dataframe(
            df_bulk[['status_icon', 'cnpj', 'razao_social', 'situacao', 'data_consulta']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "status_icon": st.column_config.TextColumn("Status", width="small"),
                "cnpj": "CNPJ",
                "razao_social": "Razão Social",
                "situacao": "Situação Cadastral",
                "data_consulta": "Data/Hora"
            }
        )

# ─── Danger Zone ─────────────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
with st.expander("⚠️ Zona de Perigo"):
    st.markdown("""<div style="background-color: rgba(239, 68, 68, 0.1); padding: 1.5rem; border-radius: 10px; border: 1px solid #ef4444;">
<h4 style="color: #ef4444; margin-top: 0;">Remover Todas as Empresas</h4>
<p style="color: #94a3b8; font-size: 0.9rem;">
Esta ação irá excluir permanentemente <b>todas</b> as empresas cadastradas, 
incluindo histórico de consultas e logs. Esta ação não pode ser desfeita.
</p>
</div>""", unsafe_allow_html=True)
    
    confirm = st.checkbox("Eu entendo que esta ação é permanente e irreversível.")
    
    if st.button("🗑️ Remover Tudo", type="secondary", disabled=not confirm):
        with st.spinner("Limpando banco de dados..."):
            try:
                r = httpx.delete(f"{BACKEND_URL}/api/empresas/purge", timeout=30)
                r.raise_for_status()
                st.success("✅ Todas as empresas foram removidas com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao remover empresas: {e}")
