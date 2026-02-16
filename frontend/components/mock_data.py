"""Mock data for IAudit when backend is unavailable."""

CLEAR_MOCK_DATA = False # Set to False for persistence

MOCK_DASHBOARD_STATS = {
    "empresas_ativas": 47,
    "consultas_hoje": 128,
    "alertas_ativos": 3,
    "taxa_sucesso": 92
}

MOCK_DASHBOARD_CHART = [
    {"data": "2026-02-08", "total": 45, "sucessos": 42, "erros": 3},
    {"data": "2026-02-09", "total": 52, "sucessos": 48, "erros": 4},
    {"data": "2026-02-10", "total": 61, "sucessos": 58, "erros": 3},
    {"data": "2026-02-11", "total": 58, "sucessos": 54, "erros": 4},
    {"data": "2026-02-12", "total": 67, "sucessos": 62, "erros": 5},
    {"data": "2026-02-13", "total": 74, "sucessos": 69, "erros": 5},
    {"data": "2026-02-14", "total": 82, "sucessos": 77, "erros": 5},
]

MOCK_DASHBOARD_ALERTS = [
    {
        "razao_social": "TECH SOLUTIONS LTDA",
        "tipo": "cnd_federal",
        "situacao": "irregular",
        "data_execucao": "2026-02-14T10:30:00"
    },
    {
        "razao_social": "COMERCIO VAREJISTA SA",
        "tipo": "fgts_regularidade",
        "situacao": "negativa",
        "data_execucao": "2026-02-14T09:15:00"
    },
    {
        "razao_social": "INDUSTRIA METALURGICA ME",
        "tipo": "cnd_pr",
        "situacao": "irregular",
        "data_execucao": "2026-02-14T08:45:00"
    },
]

MOCK_DASHBOARD_UPCOMING = [
    {
        "razao_social": "DISTRIBUIDORA ABC LTDA",
        "cnpj": "12.345.678/0001-90",
        "tipo": "cnd_federal",
        "data_agendada": "2026-02-15"
    },
    {
        "razao_social": "SERVICOS GERAIS EIRELI",
        "cnpj": "98.765.432/0001-10",
        "tipo": "fgts_regularidade",
        "data_agendada": "2026-02-15"
    },
]

# Base template for structure
MOCK_EMPRESA_DATA = {
    "cnpj": "00000000000000",
    "razao_social": "EMPRESA MODELO",
    "nome_fantasia": "MODELO",
    "situacao_cadastral": "ATIVA",
    "data_situacao_cadastral": "2020-01-01",
    "natureza_juridica": "206-2 - Sociedade Empresária Limitada",
    "porte": "Empresa de Pequeno Porte (EPP)",
    "capital_social": 100000.00,
    "identificador_matriz_filial": "MATRIZ",
    "data_inicio_atividade": "2020-01-01",
    "telefone": "4133334444",
    "email": "contato@exemplo.com.br",
    "descricao_tipo_de_logradouro": "Rua",
    "logradouro": "Exemplo",
    "numero": "100",
    "complemento": "",
    "bairro": "Centro",
    "municipio": "Curitiba",
    "uf": "PR",
    "cep": "80000-000",
    "opcao_pelo_simples": True,
    "opcao_pelo_mei": False,
    "cnae_fiscal": "0000000",
    "cnae_fiscal_descricao": "Atividade Indeterminada",
    "cnaes_secundarios": [],
    "qsa": [],
    "certidoes": {}
}

# ─── REAL COMPANIES DATABASE ──────────────────────────────────────
REAL_COMPANIES = {
    "20546887000125": {
        "razao_social": "MASTER FITNESS GYM LTDA",
        "nome_fantasia": "ACADEMIA MASTER",
        "municipio": "Ibaiti",
        "uf": "PR",
        "email_notificacao": "academiamstr@gmail.com",
        "telefone": "(43) 3546-2483",
        "logradouro": "RUA ANTONIO DE MOURA BUENO",
        "numero": "515",
        "bairro": "CENTRO",
        "cep": "84.900-000",
        "natureza_juridica": "206-2 - Sociedade Empresária Limitada",
        "porte": "MICRO EMPRESA",
        "capital_social": 10000.00,
        "data_inicio_atividade": "2014-06-25",
        "cnae_principal": {"codigo": "9313-1-00", "descricao": "Atividades de condicionamento físico"}
    },
    "06990590000123": {
        "razao_social": "GOOGLE BRASIL INTERNET LTDA.",
        "nome_fantasia": "GOOGLE",
        "municipio": "São Paulo",
        "uf": "SP",
        "email_notificacao": "googlebrasil@google.com",
        "telefone": "(11) 2395-8400",
        "logradouro": "AVENIDA BRIGADEIRO FARIA LIMA",
        "numero": "3477",
        "bairro": "ITAIM BIBI",
        "cep": "04.538-133",
        "natureza_juridica": "206-2 - Sociedade Empresária Limitada",
        "porte": "DEMAIS",
        "capital_social": 160000000.00,
        "data_inicio_atividade": "2004-08-17",
        "cnae_principal": {"codigo": "6319-4-00", "descricao": "Portais, provedores de conteúdo e outros serviços de informação na internet"}
    },
    "33000167000101": {
        "razao_social": "PETROLEO BRASILEIRO S.A. PETROBRAS",
        "nome_fantasia": "PETROBRAS",
        "municipio": "Rio de Janeiro",
        "uf": "RJ",
        "email_notificacao": "sac@petrobras.com.br",
        "telefone": "(21) 3224-4477",
        "logradouro": "AVENIDA REPUBLICA DO CHILE",
        "numero": "65",
        "bairro": "CENTRO",
        "cep": "20.031-912",
        "natureza_juridica": "203-8 - Sociedade de Economia Mista",
        "porte": "DEMAIS",
        "capital_social": 205432000000.00,
        "data_inicio_atividade": "1966-08-12",
        "cnae_principal": {"codigo": "0600-0-01", "descricao": "Extração de petróleo e gás natural"}
    },
    "09157307000175": {
        "razao_social": "ORGANIZACAO SOLIDARIA DE SERVICO SOCIAL, NUTRICIONAL, EDUCACIONAL E DE SAUDE",
        "nome_fantasia": "ORGANIZACAO SOLIDARIA",
        "municipio": "São Paulo",
        "uf": "SP",
        "email_notificacao": "contato@organizacaosolidaria.org.br",
        "telefone": "(11) 3222-4444",
        "logradouro": "Av. Paulista", 
        "numero": "1366",
        "bairro": "Bela Vista",
        "cep": "01310-100",
        "natureza_juridica": "399-9 - Associação Privada",
        "porte": "DEMAIS",
        "capital_social": 0.00,
        "data_inicio_atividade": "2020-01-10",
        "data_situacao_cadastral": "2020-01-15",
        "cnae_principal": {"codigo": "9430-8-00", "descricao": "Atividades de associações de defesa de direitos sociais"},
        "certidoes": {
            "fgts": {
                "status": "regular", 
                "certificado_url": "https://us-central1-infosimples-data.cloudfunctions.net/infosimples-storage/ucTC-XqB1SVoo12XwdfbjlkhVVAdHel30AZCFJqze4I=/1771860658/a2b1Ez/aHR0cHM6Ly9zdG9yYWdlLmdvb2dsZWFwaXMuY29tL2luZm9zaW1wbGVzLWFwaS10bXAvYXBpL2NhaXhhL3JlZ3VsYXJpZGFkZS8yMDI2MDIxNjEyMzA1OC9uX3VRcHU1VHhjQk5RQlRJcjJjU1FZSjlvVTdZOGg1US9kMGIxZjg2MzZlODFlM2Y5YWQ4NjZjN2M3MTc1Yjk2MF8wX05xdw==.html",
                "validade_inicio": "30/01/2026",
                "validade_fim": "28/02/2026"
            }
        }
    }
}


def get_mock_companies(count=150):
    """Generate a list of mock companies, including real baseline ones."""
    if count == 0:
        return []
    import random
    
    companies = []
    
    # 1. Start with REALBaseline companies to ensure they are always searchable
    for i, (clean_cnpj, data) in enumerate(REAL_COMPANIES.items()):
        # Format CNPJ for display (XX.XXX.XXX/XXXX-XX)
        s = clean_cnpj
        fmt_cnpj = f"{s[0:2]}.{s[2:5]}.{s[5:8]}/{s[8:12]}-{s[12:14]}"
        
        companies.append({
            "id": i + 1,
            "cnpj": fmt_cnpj,
            "razao_social": data["razao_social"],
            "nome_fantasia": data.get("nome_fantasia", data["razao_social"]),
            "email_notificacao": data.get("email_notificacao", f"contato@{s[0:8]}.com.br"),
            "whatsapp": "41999998888",
            "municipio": data.get("municipio", "Curitiba"),
            "uf": data.get("uf", "PR"),
            "periodicidade": "mensal",
            "ativo": True,
            "ultimo_status": "regular",
            "certidoes_summary": {"cnd_federal": "regular", "cnd_estadual": "regular", "fgts": "regular"},
            "data_ultima_consulta": "2026-02-16T10:00:00"
        })

    # 2. Add random companies
    prefixes = ["TECH", "COMERCIAL", "INDUSTRIA", "SERVICOS", "LOGISTICA", "CONSULTORIA", "SOLUCOES", "GLOBAL", "BRASIL", "SUL"]
    suffixes = ["LTDA", "S.A.", "EIRELI", "ME", "EPP", "SOLUCOES", "SISTEMAS", "DIGITAL", "GROUP", "PARTICIPACOES"]
    cities = ["Ibaiti", "Japira", "Jaboti", "Curitiba", "Londrina", "Maringá", "Ponta Grossa", "Cascavel"]
    
    start_idx = len(companies)
    for i in range(start_idx, count):
        razao = f"{random.choice(prefixes)} {random.choice(prefixes)} {random.choice(suffixes)}"
        cnpj_base = f"{random.randint(10, 99)}.{random.randint(100, 999)}.{random.randint(100, 999)}"
        cnpj_filial = "0001" if random.random() > 0.3 else f"000{random.randint(2, 9)}"
        cnpj_dv = f"{random.randint(10, 99)}"
        
        # Generate consistent certificate statuses
        cert_opts = ["regular", "regular", "regular", "irregular", "pendente"]
        certs = {
            "cnd_federal": random.choice(cert_opts),
            "cnd_estadual": random.choice(cert_opts),
            "fgts": random.choice(cert_opts)
        }
        
        # Derive global status
        if "irregular" in certs.values():
            status = "irregular"
        elif "pendente" in certs.values():
            status = "pendente"
        else:
            status = "regular"
        
        company = {
            "id": i + 1,
            "cnpj": f"{cnpj_base}/{cnpj_filial}-{cnpj_dv}",
            "razao_social": razao,
            "nome_fantasia": razao.split()[0] + " " + razao.split()[1],
            "email_notificacao": f"contato@{razao.lower().replace(' ', '').replace('.', '')}.com.br",
            "whatsapp": f"419{random.randint(10000000, 99999999)}",
            "municipio": random.choice(cities),
            "uf": "PR",
            "periodicidade": random.choice(["diario", "semanal", "quinzenal", "mensal"]),
            "ativo": random.choice([True, True, True, False]),
            "ultimo_status": status,
            "certidoes_summary": certs, 
            "data_ultima_consulta": f"2026-02-{random.randint(1, 14)}T{random.randint(8, 18)}:00:00"
        }
        companies.append(company)
        
    return companies


def get_company_details(cnpj, summary_data=None):
    """
    Get detailed mock data for a specific CNPJ.
    
    Args:
        cnpj: The CNPJ string
        summary_data: Optional dict containing base data (like cert statuses) to ensure consistency
    """
    import random
    import copy
    
    # Standardize CNPJ
    clean_cnpj = ''.join(filter(str.isdigit, str(cnpj)))
    
    # 1. REAL_COMPANIES override deactivated for search (keeping it for the initial list only)
    # The frontend now uses official BrasilAPI data for searches.
    
    # 2. Consistent Fallback Generation (Used only when the API is down)
    
    # Base structure using deepcopy to prevent reference leaking
    details = copy.deepcopy(MOCK_EMPRESA_DATA)
    details["cnpj"] = cnpj
    
    # Use isolated random instance for deterministic generation based on CNPJ
    # This ensures that querying the same CNPJ repeatedly yields the same data
    seed = int(clean_cnpj or '0')
    rng = random.Random(seed)
    
    # Define helpers first
    prefixes = ["TECH", "COMERCIAL", "INDUSTRIA", "SERVICOS", "LOGISTICA", "CONSULTORIA", "SOLUCOES", "GLOBAL", "BRASIL", "SUL"]
    suffixes = ["LTDA", "S.A.", "EIRELI", "ME", "EPP", "SOLUCOES", "SISTEMAS", "DIGITAL", "GROUP", "PARTICIPACOES"]
    cities = ["Ibaiti", "Japira", "Jaboti", "Curitiba", "Londrina", "Maringá", "Ponta Grossa", "Cascavel"]

    # Priority 1: Use summary_data if provided (preserve known state)
    if summary_data:
        details["razao_social"] = summary_data.get("razao_social", details["razao_social"])
        rs = str(details.get("razao_social", "NOVA EMPRESA"))
        details["nome_fantasia"] = summary_data.get("nome_fantasia", rs.split()[0] if " " in rs else rs)
        details["municipio"] = summary_data.get("municipio", rng.choice(cities))
        details["email"] = summary_data.get("email_notificacao", details.get("email", ""))
        details["ativo"] = summary_data.get("ativo", True)
    else:
        # Priority 2: Generate Semantically Consistent Data
        
        # Industry/Sector logic
        sectors = [
            {"type": "TECH", "cnae": "6201-5-01", "desc": "Desenvolvimento de programas de computador", "nature": "LTDA"},
            {"type": "COMERCIO", "cnae": "4713-0-04", "desc": "Comércio varejista de mercadorias", "nature": "LTDA"},
            {"type": "INDUSTRIA", "cnae": "1091-1-01", "desc": "Fabricação de produtos de panificação", "nature": "S.A."},
            {"type": "SERVICOS", "cnae": "8121-4-00", "desc": "Limpeza em prédios e em domicílios", "nature": "ME"},
            {"type": "LOGISTICA", "cnae": "4930-2-02", "desc": "Transporte rodoviário de carga", "nature": "LTDA"},
        ]
        
        sector = rng.choice(sectors)
        
        prefix = rng.choice(["SOLUCOES", "GRUPO", "COMERCIAL", "SISTEMAS", "GLOBAL", "NOVA"])
        mid = rng.choice(["BRASIL", "PARANA", "SUL", "NORTE", "UNIAO", "ALIANCA"])
        
        # Construct Name
        if sector["type"] == "TECH":
            razao = f"{prefix} TECNOLOGIA E SISTEMAS {sector['nature']}"
            fantasia = f"{prefix} TECH"
        elif sector["type"] == "INDUSTRIA":
             razao = f"{prefix} INDUSTRIA E COMERCIO {sector['nature']}"
             fantasia = f"{prefix} IND"
        else:
             razao = f"{prefix} {mid} {sector['type']} {sector['nature']}"
             fantasia = f"{prefix} {sector['type']}"

        details["razao_social"] = razao
        details["nome_fantasia"] = fantasia
        details["email"] = f"contato@{prefix.lower().replace(' ', '')}{sector['type'].lower()}.com.br"
        # Only set numicipio if not already set by summary
        if "municipio" not in details or details["municipio"] == "Curitiba": # Default check
             details["municipio"] = rng.choice(cities)
        
        details["cnae_fiscal"] = sector["cnae"].replace("-", "").replace(".", "")
        details["cnae_fiscal_descricao"] = sector["desc"]
        
    # ─── COMMON ADDRESS GENERATION (Deterministically based on CNPJ) ───
    # This runs for BOTH summary_data fallback and pure generation
    # ensuring we never get "Rua Exemplo"
    
    logradouros_pool = [
        "Rua das Flores", "Av. Brasil", "Rua XV de Novembro", "Av. Paulista", "Rua 7 de Setembro", "Av. Paraná",
        "Rua Marechal Deodoro", "Av. Batel", "Rua Comendador Araújo", "Av. Visconde de Guarapuava",
        "Rua Itupava", "Av. Presidente Kennedy", "Rua Mateus Leme", "Av. Cândido de Abreu"
    ]
    bairros_pool = [
        "Centro", "Jardim Botânico", "Batel", "Zona Industrial", "Água Verde", "Boqueirão",
        "Bigorrilho", "Cabral", "Portão", "Santa Felicidade", "Cic", "Rebouças"
    ]
    
    details["logradouro"] = rng.choice(logradouros_pool)
    details["descricao_tipo_de_logradouro"] = "" # Address pool already includes type
    details["numero"] = str(rng.randint(10, 2000))
    details["bairro"] = rng.choice(bairros_pool)
    details["cep"] = f"{rng.randint(80000, 89999)}-{rng.randint(0, 999):03d}"
    
    # If city is Curitiba, use specific real street names for extra realism
    if details.get("municipio") == "Curitiba":
        ctba_streets = ["Rua XV de Novembro", "Av. Batel", "Rua Comendador Araújo", "Av. Cândido de Abreu", "Rua Mateus Leme"]
        details["logradouro"] = rng.choice(ctba_streets)

    # Capital social based on nature/size roughly
    if "S.A." in details["razao_social"]:
        details["capital_social"] = float(rng.randint(1000, 50000) * 1000)
        details["natureza_juridica"] = "205-4 - Sociedade Anônima Fechada"
    elif "ME" in details["razao_social"]:
        details["capital_social"] = float(rng.randint(10, 100) * 1000)
        details["natureza_juridica"] = "213-5 - Empresário (Individual)"
    else:
        details["capital_social"] = float(rng.randint(50, 500) * 1000)
        details["natureza_juridica"] = "206-2 - Sociedade Empresária Limitada"
        
    # Certificates
    cert_status = {
        "cnd_federal": "regular",
        "cnd_estadual": "regular",
        "fgts": "regular"
    }
    
    if summary_data and "certidoes_summary" in summary_data:
        cert_status.update(summary_data["certidoes_summary"])
    
    details["certidoes"] = {
        "cnd_federal": {
            "status": cert_status["cnd_federal"],
            "certificado_url": "https://solucoes.receita.fazenda.gov.br/"
        },
        "cnd_estadual": {
            "status": cert_status["cnd_estadual"],
            "certificado_url": "https://cdwfazenda.paas.pr.gov.br/cdwportal/certidao/automatica"
        },
        "fgts": {
            "status": cert_status["fgts"],
            "certificado_url": "https://consulta-crf.caixa.gov.br/"
        }
    }
    
    return details
