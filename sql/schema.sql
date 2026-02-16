-- =============================================
-- IAudit - Schema Completo Supabase
-- =============================================

-- Tabela de Empresas
create table if not exists empresas (
    id uuid default gen_random_uuid() primary key,
    cnpj text not null unique,
    razao_social text not null,
    inscricao_estadual_pr text,
    email_notificacao text,
    whatsapp text,
    periodicidade text not null check (periodicidade in ('diario', 'semanal', 'quinzenal', 'mensal')),
    dia_semana integer check (dia_semana between 0 and 6),
    dia_mes integer check (dia_mes between 1 and 31),
    horario time not null default '08:00:00',
    ativo boolean default true,
    created_at timestamp with time zone default now(),
    updated_at timestamp with time zone default now()
);

-- Tabela de Consultas
create table if not exists consultas (
    id uuid default gen_random_uuid() primary key,
    empresa_id uuid references empresas(id) on delete cascade not null,
    tipo text not null check (tipo in ('cnd_federal', 'cnd_pr', 'fgts_regularidade')),
    status text not null check (status in ('agendada', 'processando', 'concluida', 'erro')) default 'agendada',
    situacao text check (situacao in ('positiva', 'negativa', 'regular', 'irregular', 'erro')),
    resultado_json jsonb default '{}',
    pdf_url text,
    mensagem_erro text,
    data_agendada timestamp with time zone not null,
    data_execucao timestamp with time zone,
    data_validade date,
    tentativas integer default 0,
    created_at timestamp with time zone default now()
);

-- Tabela de Logs de Execução
create table if not exists logs_execucao (
    id uuid default gen_random_uuid() primary key,
    consulta_id uuid references consultas(id) on delete cascade,
    nivel text check (nivel in ('info', 'aviso', 'erro')) default 'info',
    mensagem text not null,
    payload jsonb,
    created_at timestamp with time zone default now()
);

-- =============================================
-- Índices para Performance
-- =============================================
create index if not exists idx_empresas_cnpj on empresas(cnpj);
create index if not exists idx_empresas_ativo on empresas(ativo);
create index if not exists idx_consultas_empresa on consultas(empresa_id);
create index if not exists idx_consultas_tipo_status on consultas(tipo, status);
create index if not exists idx_consultas_data_agendada on consultas(data_agendada);
create index if not exists idx_consultas_status_data on consultas(status, data_agendada);
create index if not exists idx_logs_consulta on logs_execucao(consulta_id);

-- =============================================
-- Trigger para atualizar updated_at
-- =============================================
create or replace function update_updated_at_column()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists update_empresas_updated_at on empresas;
create trigger update_empresas_updated_at
    before update on empresas
    for each row
    execute function update_updated_at_column();

-- =============================================
-- Row Level Security (RLS)
-- =============================================
alter table empresas enable row level security;
alter table consultas enable row level security;
alter table logs_execucao enable row level security;

-- Políticas permissivas (ajustar para multi-tenant)
drop policy if exists "Allow all empresas" on empresas;
create policy "Allow all empresas" on empresas for all using (true) with check (true);

drop policy if exists "Allow all consultas" on consultas;
create policy "Allow all consultas" on consultas for all using (true) with check (true);

drop policy if exists "Allow all logs" on logs_execucao;
create policy "Allow all logs" on logs_execucao for all using (true) with check (true);

-- =============================================
-- Função: Estatísticas por dia (Dashboard)
-- =============================================
create or replace function consultas_por_dia(dias int default 7)
returns table(data date, total bigint, sucessos bigint, erros bigint) as $$
begin
    return query
    select
        date(c.data_execucao) as data,
        count(*) as total,
        count(*) filter (where c.status = 'concluida') as sucessos,
        count(*) filter (where c.status = 'erro') as erros
    from consultas c
    where c.data_execucao >= current_date - dias
    group by date(c.data_execucao)
    order by data desc;
end;
$$ language plpgsql;

-- =============================================
-- Função: Próximas consultas agendadas
-- =============================================
create or replace function proximas_consultas(limite int default 10)
returns table(
    consulta_id uuid,
    cnpj text,
    razao_social text,
    tipo text,
    data_agendada timestamptz
) as $$
begin
    return query
    select
        c.id as consulta_id,
        e.cnpj,
        e.razao_social,
        c.tipo,
        c.data_agendada
    from consultas c
    join empresas e on e.id = c.empresa_id
    where c.status = 'agendada'
      and c.data_agendada >= now()
    order by c.data_agendada asc
    limit limite;
end;
$$ language plpgsql;

-- =============================================
-- Função: Alertas ativos (CND negativa / FGTS irregular)
-- =============================================
create or replace function alertas_ativos(limite int default 20)
returns table(
    consulta_id uuid,
    cnpj text,
    razao_social text,
    tipo text,
    situacao text,
    data_execucao timestamptz
) as $$
begin
    return query
    select
        c.id as consulta_id,
        e.cnpj,
        e.razao_social,
        c.tipo,
        c.situacao,
        c.data_execucao
    from consultas c
    join empresas e on e.id = c.empresa_id
    where c.status = 'concluida'
      and c.situacao in ('negativa', 'irregular', 'erro')
    order by c.data_execucao desc
    limit limite;
end;
$$ language plpgsql;
