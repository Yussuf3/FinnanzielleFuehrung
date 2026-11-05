"""
app.py - HSG Financial Analyzer & Wealth Management Decision Support Tool
Vollautomatisches One-Page Dashboard nach dem Magischen Dreieck der finanziellen Führung
(Dr. Daniel Tinner, Universität St. Gallen / ACA-HSG).

Greift direkt auf die Yahoo Finance API zu, lädt ein breites Marktuniversum an Unternehmen
und berechnet automatisch sämtliche KPIs, Rankings und Wealth-Management-Empfehlungen auf einer Seite.
Erlaubt zudem das dynamische Hinzufügen jedes beliebigen weiteren Börsentickers weltweit.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from preloader import load_or_update_cache
from data_loader import fetch_company_data, smart_search_company
from hsg_engine import evaluate_company, format_metric_value

st.set_page_config(
    page_title="Financial Analyzer | Finanzielle Führung",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Styling: Deploy-Button & Toolbar komplett ausblenden + HSG Design
st.markdown("""
<style>
    /* Streamlit Deploy Button, Header, Toolbar und Footer komplett ausblenden */
    header,
    header[data-testid="stHeader"],
    [data-testid="stHeader"],
    .stAppDeployButton,
    [data-testid="stAppDeployButton"],
    [data-testid="stToolbarActions"],
    [data-testid="stToolbar"],
    #MainMenu,
    footer,
    button[kind="header"] {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
        opacity: 0 !important;
    }
    
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
    }
    
    .hsg-banner {
        background: linear-gradient(135deg, #004B33 0%, #006847 100%);
        color: white;
        padding: 24px 30px;
        border-radius: 12px;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0, 104, 71, 0.15);
    }
    .hsg-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0;
        color: #ffffff;
        letter-spacing: -0.5px;
    }
    .hsg-subtitle {
        font-size: 1.05rem;
        color: #e2f4ea;
        margin-top: 6px;
    }
    .kpi-tile {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        text-align: center;
        transition: transform 0.2s;
    }
    .kpi-tile:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .kpi-tile-title {
        font-size: 0.82rem;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-tile-val {
        font-size: 1.7rem;
        font-weight: 800;
        color: #006847;
        margin: 4px 0;
    }
    .kpi-tile-sub {
        font-size: 0.85rem;
        color: #334155;
        font-weight: 600;
    }
    .card-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }
    .badge-pill {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 16px;
        color: white;
        font-size: 0.8rem;
        font-weight: 700;
    }
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# Session State für Ausblendungen & benutzerdefinierte Firmen
if "custom_companies" not in st.session_state:
    st.session_state.custom_companies = []
if "excluded_symbols" not in st.session_state:
    st.session_state.excluded_symbols = set()

# Basisdaten laden (36 Unternehmen aus Cache / API)
raw_companies = load_or_update_cache(force_refresh=False)

# Kombiniere Basis-Universum mit benutzerdefinierten Ticker
all_raw = list(raw_companies)
existing_symbols = set(c['symbol'] for c in all_raw)
for custom in st.session_state.custom_companies:
    if custom['symbol'] not in existing_symbols:
        all_raw.append(custom)
        existing_symbols.add(custom['symbol'])

# Filtere ausgeblendete Unternehmen heraus
active_raw = [c for c in all_raw if c['symbol'] not in st.session_state.excluded_symbols]
if not active_raw:
    # Falls alle ausgeblendet wurden, Reset anbieten
    st.session_state.excluded_symbols = set()
    active_raw = list(all_raw)

# Header Banner
st.markdown(f"""
<div class="hsg-banner">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
        <div>
            <div class="hsg-title">📊 Financial Analyzer & Performance Dashboard</div>
            <div class="hsg-subtitle">Automatisierte Fundamental- & Kennzahlenanalyse nach dem Magischen Dreieck der finanziellen Führung</div>
        </div>
        <div style="background: rgba(255,255,255,0.15); padding: 8px 16px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.3); font-size: 0.9rem;">
            🟢 <strong>Live-Status:</strong> API Verbunden ({len(active_raw)} von {len(all_raw)} Unternehmen aktiv)
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Steuerungsleiste: Hinzufügen, Entfernen & API-Refresh
col_search, col_remove, col_btn_refresh = st.columns([0.46, 0.38, 0.16])

with col_search:
    new_ticker_input = st.text_input(
        "➕ Weiteres Unternehmen hinzufügen (Name oder Ticker):",
        placeholder="z.B. BMW, Adidas, Netflix, Disney, Porsche...",
        help="Du kannst einfach den bekannten Firmennamen eingeben (z.B. 'BMW' statt 'BMW.DE'). Das Tool findet automatisch das richtige Börsenkürzel und lädt die Bilanzdaten live über die API."
    )
    if new_ticker_input:
        query_str = new_ticker_input.strip()
        with st.spinner(f"Suche und lade Live-Finanzdaten für '{query_str}' über Yahoo Finance API..."):
            c_data, resolved_symbol = smart_search_company(query_str)
            if c_data and resolved_symbol:
                if resolved_symbol in st.session_state.excluded_symbols:
                    st.session_state.excluded_symbols.remove(resolved_symbol)
                    st.success(f"✅ {c_data.get('name')} war ausgeblendet und wurde wieder aktiviert!")
                    st.rerun()
                elif resolved_symbol in existing_symbols:
                    st.info(f"ℹ️ {c_data.get('name')} ({resolved_symbol}) ist bereits aktiv in der Liste.")
                else:
                    st.session_state.custom_companies.append(c_data)
                    st.success(f"✅ Automatisch zugeordnet: **{c_data.get('name')}** (`{resolved_symbol}`) erfolgreich integriert!")
                    st.rerun()
            else:
                st.warning(f"⚠️ Für '{query_str}' konnten über die Yahoo Finance API keine vollständigen Bilanzdaten gefunden werden.")

with col_remove:
    # Liste der aktuell aktiven Firmen für das Entfernen-Dropdown
    active_options = [c['symbol'] for c in active_raw]
    symbols_to_remove = st.multiselect(
        "🗑️ Unternehmen aus Ansicht entfernen (für mehr Übersicht):",
        options=active_options,
        format_func=lambda sym: next((f"{c['name']} ({sym})" for c in active_raw if c['symbol'] == sym), sym),
        placeholder="Unternehmen zum Ausblenden wählen..."
    )
    if symbols_to_remove:
        if st.button(f"❌ {len(symbols_to_remove)} ausgewählte entfernen", use_container_width=True):
            for s in symbols_to_remove:
                st.session_state.excluded_symbols.add(s)
            st.rerun()

with col_btn_refresh:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 API synchronisieren", use_container_width=True):
        with st.spinner(f"Aktualisiere Daten von der Yahoo Finance API..."):
            load_or_update_cache(force_refresh=True)
            st.success("API-Daten erfolgreich aktualisiert!")
            st.rerun()

# Hinweis und Reset-Button, falls Unternehmen ausgeblendet sind
if len(st.session_state.excluded_symbols) > 0:
    col_notice, col_reset = st.columns([0.8, 0.2])
    with col_notice:
        st.info(f"ℹ️ Derzeit sind **{len(st.session_state.excluded_symbols)} Unternehmen** ausgeblendet, um die Ansicht schlanker zu halten.")
    with col_reset:
        if st.button("🔄 Alle wieder einblenden", use_container_width=True):
            st.session_state.excluded_symbols = set()
            st.rerun()

# Berechne Scores & Evaluierung für alle aktiven Unternehmen
evaluated_list = []
for c in active_raw:
    eval_res = evaluate_company(c)
    full = {**c, **eval_res}
    evaluated_list.append(full)

# ==============================================================================
# 1. EXECUTIVE KPI HIGHLIGHTS (KACHELN OBEN)
# ==============================================================================
best_overall = max(evaluated_list, key=lambda x: x['scores']['overall'])
best_roe = max(evaluated_list, key=lambda x: x['profitability']['roe'] or 0)
best_equity = max(evaluated_list, key=lambda x: x['safety']['equity_ratio'] or 0)
best_cr = max(evaluated_list, key=lambda x: x['liquidity']['current_ratio'] or 0)
best_div = max(evaluated_list, key=lambda x: x['valuation']['dividend_yield'] or 0)

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(f"""
    <div class="kpi-tile" style="border-top: 4px solid #006847;">
        <div class="kpi-tile-title">🏆 Gesamtsieger (Score)</div>
        <div class="kpi-tile-val">{best_overall['scores']['overall']} / 100</div>
        <div class="kpi-tile-sub">{best_overall['name']} ({best_overall['symbol']})</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-tile" style="border-top: 4px solid #1E88E5;">
        <div class="kpi-tile-title">📈 Höchste Rendite (ROE)</div>
        <div class="kpi-tile-val">{best_roe['profitability']['roe']:.1f}%</div>
        <div class="kpi-tile-sub">{best_roe['name']} ({best_roe['symbol']})</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-tile" style="border-top: 4px solid #FB8C00;">
        <div class="kpi-tile-title">🛡️ Höchste Eigenkapitalquote</div>
        <div class="kpi-tile-val">{best_equity['safety']['equity_ratio']:.1f}%</div>
        <div class="kpi-tile-sub">{best_equity['name']} ({best_equity['symbol']})</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-tile" style="border-top: 4px solid #8E24AA;">
        <div class="kpi-tile-title">💧 Beste Liquidität (Grad III)</div>
        <div class="kpi-tile-val">{best_cr['liquidity']['current_ratio']:.1f}%</div>
        <div class="kpi-tile-sub">{best_cr['name']} ({best_cr['symbol']})</div>
    </div>
    """, unsafe_allow_html=True)

with k5:
    st.markdown(f"""
    <div class="kpi-tile" style="border-top: 4px solid #2E7D32;">
        <div class="kpi-tile-title">💰 Höchste Dividendenrendite</div>
        <div class="kpi-tile-val">{best_div['valuation']['dividend_yield']:.1f}%</div>
        <div class="kpi-tile-sub">{best_div['name']} ({best_div['symbol']})</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

# ==============================================================================
# 2. FILTER & INTERAKTIVE KENNZAHLEN-GESAMTTABELLE
# ==============================================================================
st.markdown(f"### 📊 1. Automatische KPI-Gesamtmatrix ({len(evaluated_list)} Unternehmen)")

col_fil1, col_fil2, col_fil3 = st.columns([1, 1, 1])

all_sectors = ["Alle Branchen"] + sorted(list(set(c['sector'] for c in evaluated_list if c['sector'] != 'N/A')))
with col_fil1:
    selected_sector = st.selectbox("🎯 Filtern nach Branche:", all_sectors)

market_options = ["Alle Regionen", "🇨🇭 Schweiz (SMI / SPI)", "🇪🇺 Europa (DAX / EuroStoxx)", "🇺🇸 USA (Global Leaders)"]
with col_fil2:
    selected_market = st.selectbox("🌍 Filtern nach Markt:", market_options)

profile_types = ["Alle Profile"] + sorted(list(set(c['profile']['type'] for c in evaluated_list)))
with col_fil3:
    selected_profile = st.selectbox("💼 Filtern nach Anlegerprofil:", profile_types)

# Gefilterte Liste
filtered = evaluated_list
if selected_sector != "Alle Branchen":
    filtered = [c for c in filtered if c['sector'] == selected_sector]

if selected_market == "🇨🇭 Schweiz (SMI / SPI)":
    filtered = [c for c in filtered if c['symbol'].endswith('.SW')]
elif selected_market == "🇪🇺 Europa (DAX / EuroStoxx)":
    filtered = [c for c in filtered if c['symbol'].endswith('.DE') or c['symbol'].endswith('.PA') or c['symbol'].endswith('.AS')]
elif selected_market == "🇺🇸 USA (Global Leaders)":
    filtered = [c for c in filtered if not ('.' in c['symbol'])]

if selected_profile != "Alle Profile":
    filtered = [c for c in filtered if c['profile']['type'] == selected_profile]

# Automatisch absteigend nach Score sortieren (Bester ganz oben, Schlechtester ganz unten)
filtered = sorted(filtered, key=lambda c: c['scores']['overall'], reverse=True)

rows = []
for c in filtered:
    p = c['profitability']
    s = c['safety']
    l = c['liquidity']
    v = c['valuation']
    sc = c['scores']
    prof = c['profile']
    
    rows.append({
        "Unternehmen": c['name'],
        "Börsenkürzel": c['symbol'],
        "Branche": c['sector'],
        "Score": sc['overall'],
        "Eigenkapitalrendite (ROE, %)": p.get('roe'),
        "EBIT-Marge (%)": p.get('ebit_margin'),
        "Rendite d. eingesetzten Kapitals (ROIC, %)": p.get('roic'),
        "Eigenkapitalquote (%)": s.get('equity_ratio'),
        "Verschuldungsgrad (Debt/Equity, %)": s.get('debt_to_equity'),
        "Nettoverschuldung / EBITDA": s.get('net_debt_ebitda'),
        "Liquiditätsgrad III (Current Ratio, %)": l.get('current_ratio'),
        "Cashflow-Verhältnis (%)": l.get('cashflow_ratio'),
        "Kurs-Gewinn-Verhältnis (KGV)": v.get('pe_trailing'),
        "Dividendenrendite (%)": v.get('dividend_yield'),
        "Anlegerprofil": prof['type']
    })

df_all = pd.DataFrame(rows)
df_all = df_all.sort_values(by="Score", ascending=False).reset_index(drop=True)

format_dict = {
    "Score": "{:.1f}",
    "Eigenkapitalrendite (ROE, %)": "{:.1f}%",
    "EBIT-Marge (%)": "{:.1f}%",
    "Rendite d. eingesetzten Kapitals (ROIC, %)": "{:.1f}%",
    "Eigenkapitalquote (%)": "{:.1f}%",
    "Verschuldungsgrad (Debt/Equity, %)": "{:.1f}%",
    "Nettoverschuldung / EBITDA": "{:.2f}x",
    "Liquiditätsgrad III (Current Ratio, %)": "{:.1f}%",
    "Cashflow-Verhältnis (%)": "{:.1f}%",
    "Kurs-Gewinn-Verhältnis (KGV)": "{:.1f}x",
    "Dividendenrendite (%)": "{:.2f}%"
}

st.dataframe(
    df_all.style.format(format_dict, na_rep="–")
    .background_gradient(subset=["Score"], cmap="Greens")
    .background_gradient(subset=["Eigenkapitalrendite (ROE, %)"], cmap="Blues")
    .background_gradient(subset=["Eigenkapitalquote (%)"], cmap="YlGn"),
    use_container_width=True,
    height=480
)

# Export-Button
csv_bytes = df_all.to_csv(index=False).encode('utf-8-sig')
st.download_button(
    label="📥 Komplette KPI-Tabelle als CSV für Excel exportieren",
    data=csv_bytes,
    file_name="hsg_kpi_gesamtvergleich.csv",
    mime="text/csv"
)

st.divider()

# ==============================================================================
# 3. INTERAKTIVE VISUALISIERUNG DES MAGISCHEN DREIECKS
# ==============================================================================
st.markdown("### 📐 2. Visualisierung: Das Magische Dreieck (Rendite, Sicherheit, Liquidität)")
st.write(
    "Die drei Kernziele **Rendite**, **Sicherheit & Stabilität** und **Liquidität** stehen in einem konkurrierenden Verhältnis zueinander. "
    "Das Radar-Diagramm zeigt die Balance, während der Scatter-Plot den Trade-Off zwischen Rendite und Sicherheit visualisiert."
)

col_vis1, col_vis2 = st.columns([1, 1])

with col_vis1:
    st.markdown("#### 🕸️ Spider-Chart (Magisches Dreieck)")
    
    comp_symbols = [c['symbol'] for c in filtered]
    default_radar = comp_symbols[:4] if len(comp_symbols) >= 4 else comp_symbols
    
    selected_for_radar = st.multiselect(
        "Unternehmen im Radar-Chart vergleichen:",
        options=comp_symbols,
        default=default_radar,
        format_func=lambda s: next((f"{c['name']} ({s})" for c in filtered if c['symbol'] == s), s)
    )
    
    categories = ['Rendite', 'Sicherheit & Stabilität', 'Liquidität']
    fig_radar = go.Figure()
    
    palette = ['#006847', '#1E88E5', '#D81B60', '#FB8C00', '#8E24AA', '#00ACC1', '#43A047']
    
    for idx, sym in enumerate(selected_for_radar):
        target = next((c for c in filtered if c['symbol'] == sym), None)
        if target:
            sc = target['scores']
            vals = [sc['profitability'], sc['safety'], sc['liquidity']]
            vals.append(vals[0])
            c_color = palette[idx % len(palette)]
            
            fig_radar.add_trace(go.Scatterpolar(
                r=vals,
                theta=categories + [categories[0]],
                fill='toself',
                name=f"{target['name']}",
                line=dict(color=c_color, width=2.5),
                opacity=0.60
            ))
            
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor='#cbd5e1'),
            angularaxis=dict(tickfont=dict(size=11, family="Arial"), gridcolor='#cbd5e1')
        ),
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
        margin=dict(l=30, r=30, t=30, b=40),
        height=380
    )
    st.plotly_chart(fig_radar, use_container_width=True)

with col_vis2:
    st.markdown("#### ⚖️ Rendite vs. Sicherheit (Scatter-Tradeoff)")
    st.caption("Bläschengröße = Liquiditätsgrad III (Current Ratio), Farbe = Score")
    
    scatter_data = []
    for c in filtered:
        scatter_data.append({
            "Unternehmen": f"{c['name']} ({c['symbol']})",
            "Eigenkapitalrendite (ROE, %)": c['profitability']['roe'] or 0,
            "Eigenkapitalquote (%)": c['safety']['equity_ratio'] or 0,
            "Liquiditätsgrad III (%)": min(350, max(50, c['liquidity']['current_ratio'] or 100)),
            "Score": c['scores']['overall'],
            "Branche": c['sector']
        })
    df_scatter = pd.DataFrame(scatter_data)
    
    fig_scatter = px.scatter(
        df_scatter,
        x="Eigenkapitalquote (%)",
        y="Eigenkapitalrendite (ROE, %)",
        size="Liquiditätsgrad III (%)",
        color="Score",
        hover_name="Unternehmen",
        text="Unternehmen",
        color_continuous_scale="Viridis",
        title="Spannungsfeld Rendite (ROE) vs. Sicherheit (Eigenkapitalquote)"
    )
    fig_scatter.update_traces(textposition='top center', textfont=dict(size=9))
    fig_scatter.update_layout(height=380, margin=dict(l=30, r=30, t=40, b=30))
    st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()

# ==============================================================================
# 4. WEALTH MANAGEMENT ENTSCHEIDUNGSHILFE & AKTIENTIPPS
# ==============================================================================
st.markdown("### 💼 3. Wealth Management Decision Center: Automatische Aktientipps & Pitches")
st.write(
    "Der Algorithmus klassifiziert jedes Unternehmen automatisch anhand seiner Fundamentalwerte in passende Anlegerprofile "
    "und formuliert fertige Argumentationshilfen (Pitches) für die Kundenberatung."
)

wm_cols = st.columns(3)
profiles_grouped = {
    "🛡️ Defensive Dividenden- & Qualitätswerte": [c for c in filtered if "Defensiv" in c['profile']['type']],
    "🚀 High Profitability & Wachstumswerte": [c for c in filtered if "Wachstum" in c['profile']['type']],
    "⚖️ Ausgewogene Titel & Value-Chancen": [c for c in filtered if "Ausgewogen" in c['profile']['type'] or "Value" in c['profile']['type']]
}

for col_idx, (group_title, comp_list) in enumerate(profiles_grouped.items()):
    with wm_cols[col_idx]:
        st.markdown(f"#### {group_title} ({len(comp_list)})")
        if not comp_list:
            st.info("Keine Unternehmen in diesem Filterkriterium.")
        for comp in comp_list:
            sc = comp['scores']
            prof = comp['profile']
            val = comp['valuation']
            
            with st.container():
                st.markdown(f"""
                <div class="card-box" style="border-left: 5px solid {prof['color']};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong style="font-size: 1.05rem; color: #1e293b;">{comp['name']}</strong>
                        <span class="badge-pill" style="background-color: {prof['color']};">{sc['overall']}/100</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #64748b; margin-bottom: 6px;">{comp['symbol']} | {comp['sector']}</div>
                    <div style="font-size: 0.85rem; font-weight: 600; color: #334155; margin-bottom: 8px;">
                        🎯 <strong>Zielgruppe:</strong> {prof['target_client']}
                    </div>
                    <div style="background-color: #f8fafc; padding: 10px 12px; border-radius: 6px; font-size: 0.83rem; margin-bottom: 8px;">
                        <strong style="color: #006847;">Argumentation für Kundengespräch:</strong>
                        <ul style="margin: 4px 0 0 0; padding-left: 16px; color: #334155;">
                            {''.join([f"<li>{pt}</li>" for pt in prof['pitch_points']])}
                        </ul>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #475569; border-top: 1px solid #f1f5f9; padding-top: 6px;">
                        <span>KGV: <strong>{format_metric_value(val.get('pe_trailing'), 'x')}</strong></span>
                        <span>Dividendenrendite: <strong>{format_metric_value(val.get('dividend_yield'), '%')}</strong></span>
                        <span>Eigenkapitalrendite (ROE): <strong>{format_metric_value(comp['profitability'].get('roe'), '%')}</strong></span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

st.divider()

# ==============================================================================
# 5. DUPONT-ZERLEGUNG
# ==============================================================================
st.markdown("### 🌳 4. DuPont-Zerlegung")
st.write(
    "Die DuPont-Analyse zerlegt die Eigenkapitalrendite in drei operative Hebel:\n"
    "$$\\text{ROE} = \\text{Nettomarge (ROS)} \\times \\text{Kapitalumschlag (CTO)} \\times \\text{Verschuldungshebel}$$"
)

dupont_data = []
for c in filtered:
    dp = c['dupont']
    dupont_data.append({
        "Unternehmen": c['name'],
        "Eigenkapitalrendite (ROE, %)": dp.get('roe'),
        "1. Reingewinnmarge (ROS, %)": dp.get('ros'),
        "2. Kapitalumschlag (CTO, x)": dp.get('capital_turnover'),
        "3. Verschuldungshebel (x)": dp.get('equity_multiplier'),
        "Primärer Renditetreiber": (
            "Hohe Gewinnmarge" if (dp.get('ros') or 0) > 18 else
            "Hoher Kapitalumschlag" if (dp.get('capital_turnover') or 0) > 0.9 else
            "Finanzierungshebel" if (dp.get('equity_multiplier') or 0) > 2.5 else "Ausgewogen"
        )
    })
df_dp = pd.DataFrame(dupont_data)
st.dataframe(
    df_dp.style.format({
        "Eigenkapitalrendite (ROE, %)": "{:.1f}%",
        "1. Reingewinnmarge (ROS, %)": "{:.1f}%",
        "2. Kapitalumschlag (CTO, x)": "{:.2f}x",
        "3. Verschuldungshebel (x)": "{:.2f}x"
    }, na_rep="–"),
    use_container_width=True,
    height=340
)

st.markdown("""
<div style="text-align: center; color: #94a3b8; font-size: 0.85rem; margin-top: 40px; padding: 15px 0; border-top: 1px solid #e2e8f0;">
    HSG Hackathon 2026 | Finanzielle Führung | Datenquelle: Yahoo Finance API
</div>
""", unsafe_allow_html=True)
