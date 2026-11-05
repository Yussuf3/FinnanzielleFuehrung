# 📊 Financial Analyzer & Wealth Management Decision Tool
**Hackathon 2026 – Modul 'Finanzielle Führung'**

---

## 📌 Übersicht & Aufgabenstellung

Dieses Tool wurde für den **Hackathon 2026** entwickelt, um Unternehmen anhand ihrer fundamentalen Bilanz- und Erfolgskennzahlen interaktiv zu vergleichen.
Es bezieht Live-Finanzdaten über die **öffentliche Yahoo Finance API** und visualisiert das in der Vorlesung vermittelte **"Magische Dreieck der finanziellen Führung"** (Rendite, Sicherheit, Liquidität) sowie die **DuPont-Zerlegung**.

Darüber hinaus fungiert das Tool als **Wealth Management Decision Engine**: Es ordnet Unternehmen automatisch passenden Anlegerprofilen zu (z.B. defensiver Dividendentitel, dynamischer Wachstumswert, Value-Chance) und generiert aussagekräftige Argumentationshilfen (Pitches) für Kundengespräche.

---

## 📐 Das Magische Dreieck & Methodik nach Vorlesung 7

Die Analyse orientiert sich exakt an den Kennzahlen und Fallstudien der Vorlesung (u.a. *Geberit / Sanitec-Übernahme* und *Air Berlin*):

### 1. Rentabilitätskennzahlen (Rendite)
* **Eigenkapitalrendite (ROE):** $\frac{\text{Jahresgewinn}}{\varnothing \text{Eigenkapital}}$
* **Gesamtkapitalrendite (ROA):** $\frac{\text{Jahresgewinn + Zinsaufwand}}{\varnothing \text{Gesamtkapital}}$
* **Return on Invested Capital (ROIC):** $\frac{\text{NOPAT}}{\text{Invested Capital}}$
* **Reingewinnmarge (ROS):** $\frac{\text{Jahresgewinn}}{\text{Nettoumsatz}}$
* **EBIT- & EBITDA-Marge:** Operative Margenstärke vor Zinsen/Steuern.

### 2. Sicherheitskennzahlen (Risiko & Stabilität)
* **Eigenkapitalquote (Eigenfinanzierungsgrad):** $\frac{\text{Eigenkapital}}{\text{Gesamtkapital}}$ (Zielwert: $> 30-40\%$)
* **Debt to Equity Ratio (Verschuldungsgrad):** $\frac{\text{Fremdkapital}}{\text{Eigenkapital}}$
* **Anlagedeckungsgrad II:** $\frac{\text{Eigenkapital + lfr. Fremdkapital}}{\text{Anlagevermögen}}$  
  *(Goldene Finanzierungsregel: Langfristiges Vermögen muss langfristig finanziert sein, Ziel $\ge 100\%$)*
* **Net Debt / EBITDA:** Dynamische Tilgungsdauer in Jahren ($< 2.5\text{x}$ gesund).
* **Zinsdeckungsgrad (Interest Coverage):** $\frac{\text{EBIT}}{\text{Zinsaufwand}}$ ($> 4-5\text{x}$).

### 3. Liquiditätskennzahlen (Liquidität)
* **Liquiditätsgrad I (Cash Ratio):** $\frac{\text{Flüssige Mittel}}{\text{Kurzfristiges Fremdkapital}}$ (Ziel: $20-30\%$)
* **Liquiditätsgrad II (Quick Ratio):** $\frac{\text{Flüssige Mittel + Forderungen}}{\text{Kurzfristiges Fremdkapital}}$ (Ziel: $\approx 100\%$)
* **Liquiditätsgrad III (Current Ratio):** $\frac{\text{Umlaufvermögen}}{\text{Kurzfristiges Fremdkapital}}$ (Ziel: $> 150-200\%$)
* **Cashflow Ratio:** $\frac{\text{CF aus Geschäftstätigkeit}}{\text{Kurzfristige Verbindlichkeiten}}$ (dynamischer Liquiditätsnachweis)
* **Free Cash Flow (FCF):** Cashflow nach Investitionen.

### 4. DuPont-Schema (ROI-Baum, Folie 34)
Zerlegt die Eigenkapitalrendite in ihre drei Treiber:
$$\text{ROE} = \text{Nettogewinnmarge (ROS)} \times \text{Kapitalumschlag (CTO)} \times \text{Verschuldungshebel (Equity Multiplier)}$$

---

## 🚀 Features des Tools

1. **Vollautomatische API-Anbindung (Yahoo Finance):**
   * Das Tool greift direkt auf die offizielle Yahoo Finance API zu und lädt automatisch ein breites Marktuniversum von **über 36 führenden Unternehmen** (Schweizer SMI/SPI inkl. Geberit, Lonza, Sika, Nestlé etc., europäische Champions wie SAP, Siemens, LVMH, ASML und globale US-Tech-Leader wie Apple, Nvidia, Microsoft, Amazon).
   * **Kein manuelles Hinzufügen nötig:** Alle 36+ Unternehmen werden sofort beim Laden der Seite mit allen KPIs berechnet und übersichtlich dargestellt.
   * **Flexibel erweiterbar:** Über das interaktive Suchfeld `➕ Beliebiges weiteres Unternehmen hinzufügen` kann jeder beliebige Firmenname weltweit (z.B. `BMW`, `Adidas`, `Porsche`, `Netflix`, `Disney`) on-the-fly nachgeladen werden.
   * **Entfernen & Ausblenden für maximale Übersicht:** Über die Auswahl `🗑️ Unternehmen aus Ansicht entfernen` können einzelne oder mehrere Unternehmen per Klick ausgeblendet werden. Ein Button `🔄 Alle wieder einblenden` stellt bei Bedarf den Ausgangszustand sofort wieder her.
2. **One-Page KPI-Dashboard:**
   * **Executive Highlights:** Direkte Kacheln mit den Spitzenreitern für Rendite (ROE), Sicherheit (EK-Quote), Liquidität (Current Ratio) und Gesamtscore.
   * **Gesamt-Benchmarkmatrix:** Alle Unternehmen und alle Kennzahlen in einer sortierbaren, filterbaren Tabelle (nach Branche, Region oder Anlegerprofil).
3. **Interaktives Radar-/Netzdiagramm & Scatter-Plot:**
   * Visualisiert das Magische Dreieck für den direkten Vergleich.
   * Scatter-Plot "Rendite vs. Sicherheit" zur Darstellung des Zielkonflikts.
4. **Wealth Management Decision Engine:**
   * Automatische Einordnung der Titel in Anlegerprofile (Defensive Dividende, High Growth, Ausgewogene Qualität, Value).
   * Automatisch generierte Kundengesprächs-Pitches.
5. **DuPont-Zerlegung (Folie 34):**
   * Vollständige Aufschlüsselung der Rentabilitätstreiber für alle Unternehmen.
   * Generierung von Gesprächs-Pitches für den Vermögensverwalter.
6. **Benchmark-Balkendiagramme & CSV-Export:**
   * Direkter optischer Vergleich einzelner Metriken und Download der Datenmatrix als Excel-taugliche CSV.

---

## 💻 Schnellstart

### 1. Voraussetzungen
Python 3.10+ ist installiert. Benötigte Bibliotheken:
```bash
pip install streamlit yfinance plotly pandas
```

### 2. Anwendung starten
Einfach die Datei **`start_app.bat`** doppelklicken  
*oder* im Terminal folgenden Befehl ausführen:
```bash
streamlit run app.py
```

Die Web-Oberfläche öffnet sich automatisch im Browser unter `http://localhost:8501`.
