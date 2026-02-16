"""Loading animations and utility components for IAudit."""

import streamlit as st


def loading_skeleton(lines=3, height="20px"):
    """Display animated loading skeleton."""
    skeleton_html = """
    <style>
        @keyframes skeleton-loading {
            0% {
                background-position: -200px 0;
            }
            100% {
                background-position: calc(200px + 100%) 0;
            }
        }
        
        .skeleton {
            background: linear-gradient(90deg, #1e293b 0px, #334155 40px, #1e293b 80px);
            background-size: 200px 100px;
            animation: skeleton-loading 1.3s ease-in-out infinite;
            border-radius: 8px;
            margin-bottom: 12px;
        }
    </style>
    """
    
    skeleton_html += "<div style='padding: 1rem;'>"
    for i in range(lines):
        skeleton_html += f"<div class='skeleton' style='height: {height}; width: {90 - (i * 10)}%;'></div>"
    skeleton_html += "</div>"
    
    st.markdown(skeleton_html, unsafe_allow_html=True)


def animated_success(message, duration=3):
    """Show animated success message."""
    st.markdown(f"""
    <style>
        @keyframes slideInRight {{
            from {{
                transform: translateX(100%);
                opacity: 0;
            }}
            to {{
                transform: translateX(0);
                opacity: 1;
            }}
        }}
        
        @keyframes checkmark {{
            0% {{
                transform: scale(0) rotate(0deg);
            }}
            50% {{
                transform: scale(1.2) rotate(360deg);
            }}
            100% {{
                transform: scale(1) rotate(360deg);
            }}
        }}
        
        .success-toast {{
            background: linear-gradient(135deg, #065f46, #059669);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(5, 150, 105, 0.4);
            animation: slideInRight 0.5s ease-out;
            display: flex;
            align-items: center;
            gap: 1rem;
            margin: 1rem 0;
        }}
        
        .success-checkmark {{
            font-size: 2rem;
            animation: checkmark 0.6s ease-out 0.2s backwards;
        }}
    </style>
    
    <div class="success-toast">
        <span class="success-checkmark">✓</span>
        <span style="font-weight: 600; font-size: 1.05rem;">{message}</span>
    </div>
    """, unsafe_allow_html=True)
    

def progress_ring(percentage, label="", size=120):
    """Display animated progress ring."""
    color = "#22c55e" if percentage >= 75 else "#fbbf24" if percentage >= 50 else "#ef4444"
    
    st.markdown(f"""
    <style>
        @keyframes progress-ring-fill {{
            from {{
                stroke-dashoffset: 339;
            }}
            to {{
                stroke-dashoffset: {339 - (339 * percentage / 100)};
            }}
        }}
        
        .progress-ring-circle {{
            stroke-dasharray: 339;
            stroke-dashoffset: 339;
            animation: progress-ring-fill 1.5s ease-out forwards;
            transform: rotate(-90deg);
            transform-origin: 50% 50%;
        }}
    </style>
    
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center;">
        <svg width="{size}" height="{size}">
            <circle
                cx="{size/2}" cy="{size/2}" r="54"
                stroke="#1e293b"
                stroke-width="12"
                fill="none"
            />
            <circle
                class="progress-ring-circle"
                cx="{size/2}" cy="{size/2}" r="54"
                stroke="{color}"
                stroke-width="12"
                fill="none"
                stroke-linecap="round"
            />
            <text
                x="50%" y="50%"
                text-anchor="middle"
                dy=".3em"
                style="font-size: 28px; font-weight: 700; fill: {color};"
            >
                {percentage}%
            </text>
        </svg>
        {f'<p style="color: #cbd5e1; margin-top: 0.5rem; font-weight: 500;">{label}</p>' if label else ''}
    </div>
    """, unsafe_allow_html=True)


def data_card(title, value, icon="📊", trend=None):
    """Display animated data card with optional trend."""
    trend_html = ""
    if trend:
        trend_color = "#22c55e" if trend > 0 else "#ef4444" if trend < 0 else "#94a3b8"
        trend_arrow = "↑" if trend > 0 else "↓" if trend < 0 else "→"
        trend_html = f"""
        <div style="font-size: 0.9rem; color: {trend_color}; font-weight: 600; margin-top: 0.5rem;">
            {trend_arrow} {abs(trend)}%
        </div>
        """
    
    st.markdown(f"""
    <style>
        .data-card {{
            background: linear-gradient(135deg, #1e293b, #334155);
            border-radius: 16px;
            padding: 1.5rem;
            border: 1px solid #475569;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .data-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #3b82f6, #60a5fa, #3b82f6);
            background-size: 200% 100%;
            animation: shimmer 3s linear infinite;
        }}
        
        .data-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 32px rgba(59, 130, 246, 0.3);
            border-color: #60a5fa;
        }}
        
        .data-card-icon {{
            font-size: 2.5rem;
            margin-bottom: 0.8rem;
        }}
        
        .data-card-value {{
            font-size: 2.5rem;
            font-weight: 700;
            color: #60a5fa;
            margin: 0.5rem 0;
        }}
    </style>
    
    <div class="data-card">
        <div class="data-card-icon">{icon}</div>
        <div style="color: #94a3b8; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">{title}</div>
        <div class="data-card-value">{value}</div>
        {trend_html}
    </div>
    """, unsafe_allow_html=True)


def export_button(data, filename="data.json", label="📥 Exportar Dados"):
    """Create an export button for data."""
    import json
    
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    
    st.download_button(
        label=label,
        data=json_str,
        file_name=filename,
        mime="application/json",
        use_container_width=True
    )
