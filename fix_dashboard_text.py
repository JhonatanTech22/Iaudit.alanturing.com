
import os

file_path = "frontend/pages/1_📊_Dashboard.py"

# The header we know is there (it was added by us and likely survived better than the utf-8 body)
# Or we just search for the import that starts the block
marker = "# --- MODULE: RED FLAG LIST (RISK MONITOR)"

correct_block = """# ─── MODULE: RED FLAG LIST (RISK MONITOR) ─────────────────────────────
import pandas as pd
if 'red_flags' in st.session_state and st.session_state['red_flags']:
    st.markdown('<br>', unsafe_allow_html=True)
    st.markdown('<h3>🚩 Monitoramento de Riscos (Empresas Irregulares)</h3>', unsafe_allow_html=True)
    st.info('Estas empresas foram identificadas como irregulares durante o processo de Importação em Lote.')
    
    red_flags = st.session_state['red_flags']
    df_risk = pd.DataFrame(red_flags)
    
    st.dataframe(
        df_risk[['cnpj', 'razao_social', 'situacao', 'data_consulta']],
        use_container_width=True,
        hide_index=True,
        column_config={
            'cnpj': 'CNPJ',
            'razao_social': 'Razão Social',
            'situacao': st.column_config.TextColumn('Situação', help='Status na Receita Federal'),
            'data_consulta': 'Detectado em'
        }
    )
"""

try:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    # Find where the block starts
    cut_index = -1
    for i, line in enumerate(lines):
        if "MODULE: RED FLAG LIST" in line:
            cut_index = i
            break
    
    if cut_index != -1:
        # Keep everything before the cut
        clean_content = "".join(lines[:cut_index])
        
        # Append the correct block
        new_content = clean_content + "\n" + correct_block
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Successfully rewrote Dashboard.py with clean Red Flag section.")
    else:
        print("Could not find the Red Flag marker to replace.")

except Exception as e:
    print(f"Error: {e}")
