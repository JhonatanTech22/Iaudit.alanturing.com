
"""
New Independent Modules Utilities.
Contains logic for Bulk Import, Red Flag Management, and Scheduler.
Zero Breaking Changes: This file is additive and does not modify existing logic.
"""

import streamlit as st
import httpx
import pandas as pd
import re
import os
from datetime import datetime

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ─── MODULE 1: BULK IMPORT LOGIC ─────────────────────────────────────

def clean_cnpj(cnpj: str) -> str:
    """Removes non-digits from CNPJ string."""
    return re.sub(r'\D', '', str(cnpj))

def fetch_company_data_independent(cnpj: str):
    """
    Independent fetcher for Bulk Import to avoid touching core fetch logic.
    Returns: dict or None
    """
    try:
        # Mocking the endpoint call structure used in other pages
        # Assuming there's an endpoint /api/empresas/{cnpj} or similar
        # If not, we fall back to the mock logic or whatever the backend provides.
        # Based on previous context, we might use a direct search endpoint
        
        # NOTE: Using a specific endpoint for data retrieval
        response = httpx.get(f"{BACKEND_URL}/api/query/cnpj/{cnpj}", timeout=30.0)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return {"cnpj": cnpj, "error": "Not Found", "situacao": "DESCONHECIDA"}
        else:
            return {"cnpj": cnpj, "error": f"HTTP {response.status_code}", "situacao": "ERRO"}
            
    except Exception as e:
        return {"cnpj": cnpj, "error": str(e), "situacao": "ERRO"}

def process_bulk_list(cnpjs: list, progress_bar=None):
    """
    Processes a list of CNPJs sequentially.
    Sends data to Backend API to ensure persistence.
    """
    if 'bulk_results' not in st.session_state:
        st.session_state['bulk_results'] = []
    
    total = len(cnpjs)
    
    for i, raw_cnpj in enumerate(cnpjs):
        cnpj = clean_cnpj(raw_cnpj)
        
        # Update Progress
        if progress_bar:
            progress_bar.progress((i + 1) / total, text=f"Processando {i+1}/{total}: {cnpj}")

        if len(cnpj) != 14:
            st.session_state['bulk_results'].append({
                "cnpj": raw_cnpj,
                "razao_social": "CNPJ Inválido",
                "situacao": "ERRO",
                "status_icon": "Erro"
            })
            continue
            
        # Register Company in Backend
        try:
            # 1. Try to fetch existing data to check if already exists
            # For bulk import, we often just want to register them.
            # Let's try to CREATE it. If it exists, the backend handles it or we update it.
            # But the requirement is "add companies".
            
            # Payload for creation
            payload = {
                "cnpj": cnpj,
                "razao_social": f"Empresa {cnpj[:8]}...", # Temporary placeholder if not enriched
                "periodicidade": "mensal",
                "horario": "08:00:00",
                "ativo": True
            }
            
            # Smart enrichment attempt (Simulated for now, or use an enrichment endpoint if available)
            # If we had a real enrichment service, we'd call it here.
            # For now, we post to /api/empresas which validates and stores.
            
            response = httpx.post(f"{BACKEND_URL}/api/empresas", json=payload, timeout=10.0)
            
            if response.status_code == 201 or response.status_code == 200:
                data = response.json()
                situacao = "Regular" # Default for new companies until validated
                status_icon = "Regular"
                razao = data.get("razao_social", payload["razao_social"])
            elif response.status_code == 409:
                # Already exists
                situacao = "Já Cadastrada"
                status_icon = "Regular"
                razao = "Empresa Existente"
            else:
                situacao = "Erro ao Cadastrar"
                status_icon = "Erro"
                razao = "Erro API"

        except Exception as e:
            situacao = f"Erro de Conexão: {str(e)}"
            status_icon = "Erro"
            razao = "Erro"

        result_entry = {
            "cnpj": cnpj,
            "razao_social": razao,
            "situacao": situacao,
            "status_icon": status_icon,
            "data_consulta": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        st.session_state['bulk_results'].insert(0, result_entry)

# ─── MODULE 2: RED FLAG MANAGER ──────────────────────────────────────

def add_to_red_flags(company_data):
    """Adds a company to the Red Flag list if not already present."""
    if 'red_flags' not in st.session_state:
        st.session_state['red_flags'] = []
    
    # Check for duplicates
    exists = any(item['cnpj'] == company_data['cnpj'] for item in st.session_state['red_flags'])
    if not exists:
        st.session_state['red_flags'].append(company_data)

def get_red_flags():
    """Retrieves the list of irregular companies."""
    return st.session_state.get('red_flags', [])

# ─── MODULE 3: SCHEDULER LOGIC ───────────────────────────────────────

def schedule_job(job_data):
    """Adds a job to the schedule list."""
    if 'scheduled_jobs' not in st.session_state:
        st.session_state['scheduled_jobs'] = []
        
    st.session_state['scheduled_jobs'].append(job_data)

def get_scheduled_jobs():
    return st.session_state.get('scheduled_jobs', [])
