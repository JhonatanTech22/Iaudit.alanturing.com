"""IAudit - Plotly chart components with modern visualizations."""

from __future__ import annotations

import plotly.graph_objects as go


def create_bar_chart(chart_data: list[dict]) -> go.Figure:
    """
    Create a styled bar chart showing queries per day.

    Args:
        chart_data: List of dicts with keys: data, total, sucessos, erros
    """
    dates = [d.get("data", "") for d in chart_data]
    sucessos = [d.get("sucessos", 0) for d in chart_data]
    erros = [d.get("erros", 0) for d in chart_data]

    fig = go.Figure()

    # Success bars with gradient effect
    fig.add_trace(go.Bar(
        name="Sucesso",
        x=dates,
        y=sucessos,
        marker=dict(
            color=sucessos,
            colorscale=[[0, '#10b981'], [1, '#22c55e']],
            line=dict(width=0),
        ),
        opacity=0.95,
        hovertemplate="<b>%{x}</b><br>Sucessos: %{y}<extra></extra>",
    ))

    # Error bars with gradient
    fig.add_trace(go.Bar(
        name="Erro",
        x=dates,
        y=erros,
        marker=dict(
            color=erros,
            colorscale=[[0, '#dc2626'], [1, '#ef4444']],
            line=dict(width=0),
        ),
        opacity=0.95,
        hovertemplate="<b>%{x}</b><br>Erros: %{y}<extra></extra>",
    ))

    fig.update_layout(
        barmode="stack",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#CBD5E1", family="Inter"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=13),
            bgcolor="rgba(30,41,59,0.7)",
            bordercolor="#475569",
            borderwidth=1,
        ),
        margin=dict(l=40, r=20, t=50, b=40),
        height=340,
        xaxis=dict(
            title="Data",
            gridcolor="rgba(71,85,105,0.3)",
            tickfont=dict(size=12),
            showline=True,
            linecolor="rgba(71,85,105,0.5)",
        ),
        yaxis=dict(
            title="Consultas",
            gridcolor="rgba(255,255,255,0.1)",
            tickfont=dict(size=12),
            showline=True,
            linecolor="rgba(71,85,105,0.5)",
        ),
        hovermode="x unified",
    )

    return fig


def create_area_chart(chart_data: list[dict]) -> go.Figure:
    """
    Create an area chart showing consultation trends.
    
    Args:
        chart_data: List of dicts with keys: data, total, sucessos, erros
    """
    dates = [d.get("data", "") for d in chart_data]
    sucessos = [d.get("sucessos", 0) for d in chart_data]
    erros = [d.get("erros", 0) for d in chart_data]
    total = [d.get("total", 0) for d in chart_data]

    fig = go.Figure()

    # Success area with gradient
    fig.add_trace(go.Scatter(
        name="Sucesso",
        x=dates,
        y=sucessos,
        mode='lines',
        line=dict(width=3, color='#22c55e'),
        fill='tozeroy',
        fillcolor='rgba(34, 197, 94, 0.2)',
        hovertemplate="<b>%{x}</b><br>Sucessos: %{y}<extra></extra>",
    ))

    # Error area
    fig.add_trace(go.Scatter(
        name="Erro",
        x=dates,
        y=erros,
        mode='lines',
        line=dict(width=3, color='#ef4444'),
        fill='tozeroy',
        fillcolor='rgba(239, 68, 68, 0.2)',
        hovertemplate="<b>%{x}</b><br>Erros: %{y}<extra></extra>",
    ))

    fig.update_layout(
        plot_bgcolor="rgba(15,23,42,0.5)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0", family="Inter"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=13),
            bgcolor="rgba(30,41,59,0.7)",
            bordercolor="#475569",
            borderwidth=1,
        ),
        margin=dict(l=40, r=20, t=50, b=40),
        height=340,
        xaxis=dict(
            title="Data",
            gridcolor="rgba(71,85,105,0.3)",
            tickfont=dict(size=12),
            showline=True,
            linecolor="rgba(71,85,105,0.5)",
        ),
        yaxis=dict(
            title="Consultas",
            gridcolor="rgba(71,85,105,0.3)",
            tickfont=dict(size=12),
            showline=True,
            linecolor="rgba(71,85,105,0.5)",
        ),
        hovermode="x unified",
    )

    return fig


def create_gauge_chart(value: float, title: str = "Taxa de Sucesso") -> go.Figure:
    """
    Create a gauge chart for percentage metrics.
    
    Args:
        value: Percentage value (0-100)
        title: Chart title
    """
    # Determine color based on value
    if value >= 90:
        color = "#22c55e"  # Green
    elif value >= 70:
        color = "#fbbf24"  # Yellow
    else:
        color = "#ef4444"  # Red

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 18, 'color': '#e2e8f0'}},
        number={'suffix': "%", 'font': {'size': 40, 'color': color}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#475569"},
            'bar': {'color': color},
            'bgcolor': "rgba(30,41,59,0.5)",
            'borderwidth': 2,
            'bordercolor': "#475569",
            'steps': [
                {'range': [0, 50], 'color': 'rgba(239, 68, 68, 0.2)'},
                {'range': [50, 80], 'color': 'rgba(251, 191, 36, 0.2)'},
                {'range': [80, 100], 'color': 'rgba(34, 197, 94, 0.2)'}
            ],
            'threshold': {
                'line': {'color': "#60a5fa", 'width': 4},
                'thickness': 0.75,
                'value': 95
            }
        }
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font={'color': "#e2e8f0", 'family': "Inter"},
        height=280,
        margin=dict(l=20, r=20, t=60, b=20),
    )

    return fig


def create_donut_chart(positivas: int, negativas: int, erros: int) -> go.Figure:
    """Create a donut chart for consultation status distribution."""
    labels = ["Positiva/Regular", "Negativa/Irregular", "Erro"]
    values = [positivas, negativas, erros]
    colors = ["#22c55e", "#ef4444", "#f97316"]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(
            colors=colors, 
            line=dict(color="#0a0e1a", width=3)
        ),
        textfont=dict(color="#e2e8f0", size=13, family="Inter"),
        hovertemplate="<b>%{label}</b><br>%{value} consultas<br>%{percent}<extra></extra>",
    )])

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0", family="Inter"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(size=12),
            bgcolor="rgba(30,41,59,0.7)",
            bordercolor="#475569",
            borderwidth=1,
        ),
        margin=dict(l=20, r=20, t=20, b=50),
        height=300,
        annotations=[dict(
            text=f'<b>{sum(values)}</b><br>Total',
            x=0.5, y=0.5,
            font_size=20,
            font_color="#60a5fa",
            showarrow=False
        )]
    )

    return fig


def create_line_chart(chart_data: list[dict]) -> go.Figure:
    """
    Create a line chart for trend analysis.
    
    Args:
        chart_data: List of dicts with keys: data, total, sucessos, erros
    """
    dates = [d.get("data", "") for d in chart_data]
    total = [d.get("total", 0) for d in chart_data]
    sucessos = [d.get("sucessos", 0) for d in chart_data]
    erros = [d.get("erros", 0) for d in chart_data]

    fig = go.Figure()

    # Total line
    fig.add_trace(go.Scatter(
        name="Total",
        x=dates,
        y=total,
        mode='lines+markers',
        line=dict(width=3, color='#60a5fa'),
        marker=dict(size=8, color='#60a5fa', line=dict(width=2, color='#0a0e1a')),
        hovertemplate="<b>%{x}</b><br>Total: %{y}<extra></extra>",
    ))

    # Success line
    fig.add_trace(go.Scatter(
        name="Sucesso",
        x=dates,
        y=sucessos,
        mode='lines+markers',
        line=dict(width=2.5, color='#22c55e', dash='dot'),
        marker=dict(size=7, color='#22c55e'),
        hovertemplate="<b>%{x}</b><br>Sucessos: %{y}<extra></extra>",
    ))

    # Error line
    fig.add_trace(go.Scatter(
        name="Erro",
        x=dates,
        y=erros,
        mode='lines+markers',
        line=dict(width=2.5, color='#ef4444', dash='dot'),
        marker=dict(size=7, color='#ef4444'),
        hovertemplate="<b>%{x}</b><br>Erros: %{y}<extra></extra>",
    ))

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#CBD5E1", family="Inter"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=13),
            bgcolor="rgba(30,41,59,0.7)",
            bordercolor="#475569",
            borderwidth=1,
        ),
        margin=dict(l=40, r=20, t=50, b=40),
        height=340,
        xaxis=dict(
            title="Data",
            gridcolor="rgba(71,85,105,0.3)",
            tickfont=dict(size=12),
            showline=True,
            linecolor="rgba(71,85,105,0.5)",
        ),
        yaxis=dict(
            title="Consultas",
            gridcolor="rgba(71,85,105,0.3)",
            tickfont=dict(size=12),
            showline=True,
            linecolor="rgba(71,85,105,0.5)",
        ),
        hovermode="x unified",
    )

    return fig
