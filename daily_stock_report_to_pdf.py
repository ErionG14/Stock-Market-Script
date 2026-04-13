import os
import datetime
import pandas as pd
import time
from polygon import RESTClient
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# ────────────────────────────────────────────────
# CONFIGURATION
# ────────────────────────────────────────────────

STOCKS = ['UEC', 'NXE', 'UUUU', 'CCJ', 'LEU', 'BWXT', 'OKLO', 'SMR', 'D', 'DUK',
          'USAR', 'KTOS', 'ORCL', 'NVDA']

API_KEY = "gw54ry5iqial485WVE0vqdKu3tegUSHZ"

client = RESTClient(API_KEY)
PDF_FILENAME = f"daily_stock_report_{datetime.date.today().isoformat()}.pdf"

# ────────────────────────────────────────────────
# DATA FETCHING
# ────────────────────────────────────────────────

def fetch_daily_data(ticker):
    try:
        today = datetime.date.today()
        from_date = (today - datetime.timedelta(days=10)).isoformat()
        to_date = today.isoformat()

        aggs = client.get_aggs(ticker, 1, 'day', from_date, to_date)
        if not aggs or len(aggs) < 2:
            return None

        df = pd.DataFrame([vars(a) for a in aggs])
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms').dt.date

        latest = df.iloc[-1]
        prev_close = df.iloc[-2]['close']
        change_pct = (latest['close'] - prev_close) / prev_close * 100
        ma_7 = df['close'].tail(7).mean()

        outlook = 'Increase' if latest['close'] > ma_7 * 1.005 else \
                  'Decrease' if latest['close'] < ma_7 * 0.995 else 'Sideways'

        return {
            'Ticker': ticker,
            'Price': round(latest['close'], 2),
            'Volume': f"{int(latest['volume']):,}",
            '% Change': round(change_pct, 2),
            '7d MA': round(ma_7, 2),
            'Outlook': outlook
        }
    except Exception as e:
        print(f"Error for {ticker}: {e}")
        return None

# ────────────────────────────────────────────────
# PDF GENERATION
# ────────────────────────────────────────────────

def save_to_pdf(df):
    doc = SimpleDocTemplate(PDF_FILENAME, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    title = f"Daily Stock Update Report – {datetime.date.today().strftime('%B %d, %Y')}"
    elements.append(Paragraph(title, styles['Heading1']))
    elements.append(Spacer(1, 12))

    data = [df.columns.tolist()] + df.values.tolist()
    table = Table(data)

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])

    for i in range(1, len(data)):
        if i % 2 == 0:
            style.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)

    table.setStyle(style)
    elements.append(table)
    doc.build(elements)
    print(f"Report successfully saved to: {PDF_FILENAME}")

# ────────────────────────────────────────────────
# MAIN EXECUTION
# ────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Starting data fetch for {len(STOCKS)} stocks...")
    print("Note: Using 12-second delays to respect Free Tier limits.\n")
    
    data_list = []
    
    for index, ticker in enumerate(STOCKS):
        if index > 0:
            print(f"--- Waiting 12s for next request... ({index}/{len(STOCKS)}) ---")
            time.sleep(12)
            
        row = fetch_daily_data(ticker)
        if row:
            data_list.append(row)
            print(f"Fetched: {ticker} - ${row['Price']}")

    if not data_list:
        print("No data retrieved. Check your API key or market hours.")
    else:
        df_final = pd.DataFrame(data_list)
        print("\n--- Summary ---")
        print(df_final.to_string(index=False))
        
        print("\nGenerating PDF...")
        save_to_pdf(df_final)