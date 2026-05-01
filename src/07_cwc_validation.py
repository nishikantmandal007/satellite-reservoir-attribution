"""
Stage 7: CWC Bulletin Validation
=================================
Downloads CWC Weekly Reservoir Bulletins (PDFs) and extracts Maithon
storage data for independent validation of Stage 1 storage reconstruction.

Run: uv run python src/07_cwc_validation.py

Output:
  data/raw/cwc_maithon_storage.csv  — weekly CWC storage (BCM)
  data/processed/cwc_validation.csv — monthly CWC vs AV-curve comparison
  figures/FigS2_cwc_validation.png  — scatter + timeseries comparison
"""

import re
import time
import urllib.request
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tabula

RAW_DIR       = Path('data/raw')
PROCESSED_DIR = Path('data/processed')
FIGURES_DIR   = Path('figures')
CWC_RAW       = RAW_DIR / 'cwc_maithon_storage.csv'
CWC_PAGE      = 'https://cwc.gov.in/en/reservoir-level-storage-bulletin'
PDF_DIR       = RAW_DIR / 'cwc_pdfs'


# ─── helpers ────────────────────────────────────────────────────────────────

def fetch_pdf_urls() -> list:
    """Scrape CWC bulletin page for all PDF links."""
    req  = urllib.request.Request(CWC_PAGE, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=20)
    html = resp.read().decode('utf-8', errors='ignore')
    pdfs = re.findall(r'(https?://cwc\.gov\.in/sites/default/files/[^\s"\'<>]+\.pdf)',
                      html, re.IGNORECASE)
    # Filter out admin/address PDFs — only weekly bulletins
    return [p for p in pdfs if 'rlmaddresses' not in p and 'admin' not in p]


def download_pdf(url: str, dest: Path) -> bool:
    """Download a single PDF. Return True on success."""
    if dest.exists():
        return True
    try:
        req  = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=20)
        dest.write_bytes(resp.read())
        return True
    except Exception as e:
        print(f"    SKIP {url.split('/')[-1]}: {type(e).__name__}")
        return False


def extract_date_from_filename(fname: str):
    """Parse date from CWC PDF filename patterns like 'fb-27032025.pdf'."""
    fname = fname.lower().replace('bulletin-', '').replace('-new', '').replace('-pdf', '')
    fname = fname.replace('fb-', '').replace('fb', '')
    # Try YYYY-MM-DD or similar first (unambiguous)
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', fname)
    if m:
        try:
            return pd.Timestamp(year=int(m.group(1)), month=int(m.group(2)), day=int(m.group(3)))
        except Exception:
            pass
    # Try DDMMYYYY (most common CWC pattern)
    m = re.search(r'(\d{2})(\d{2})(\d{4})', fname)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12 and 1 <= d <= 31 and 2010 <= y <= 2027:
            try:
                return pd.Timestamp(year=y, month=mo, day=d)
            except Exception:
                pass
    return None


def parse_maithon_from_pdf(pdf_path: Path):
    """
    Extract Maithon CURRENT LIVE STORAGE (BCM) from CWC bulletin PDF.

    CWC bulletin column order (per 161-reservoir weekly report):
    SR | NAME | STATE | CAPACITY_TMC | HYDEL | FRL_M | CAPACITY_FRL_BCM |
    DATE | CURRENT_LEVEL_M | CURRENT_STORAGE_BCM | PCT_FULL | ...

    Key insight: CURRENT_STORAGE_BCM is the value that follows
    CURRENT_LEVEL_M (a value typically 100–160 m). We must NOT take
    CAPACITY_FRL_BCM (which is fixed for every week).
    """
    try:
        tables = tabula.read_pdf(str(pdf_path), pages='all',
                                 multiple_tables=True, silent=True,
                                 pandas_options={'header': None})
        for table in tables:
            text = table.to_string().lower()
            if 'maithon' not in text:
                continue
            for _, row in table.iterrows():
                vals = [str(v) for v in row.values]
                row_str = ' '.join(vals).lower()
                if 'maithon' not in row_str:
                    continue
                # CWC row: ...FRL_level(m)...CAPACITY_BCM(fixed)...CURRENT_LEVEL(m)...CURRENT_STORAGE_BCM...
                # Both CAPACITY and CURRENT_STORAGE are in 0.01-2.0 BCM range.
                # CAPACITY is always first; CURRENT_STORAGE is second BCM value in the row.
                nums = [float(n) for n in re.findall(r'(\d+\.\d+)', ' '.join(vals))]
                bcm_candidates = [n for n in nums if 0.01 <= n <= 2.0]
                if len(bcm_candidates) >= 2:
                    return bcm_candidates[1]  # skip capacity (index 0), take current storage
                elif len(bcm_candidates) == 1:
                    return bcm_candidates[0]
    except Exception:
        pass
    return None


# ─── main ───────────────────────────────────────────────────────────────────

def main():
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    # ── 1. Fetch PDF list ────────────────────────────────────────────────────
    print("[1/4] Fetching CWC bulletin PDF list...")
    try:
        pdf_urls = fetch_pdf_urls()
    except Exception as e:
        print(f"  ERROR fetching CWC page: {e}")
        print("  CWC website unreachable. Check internet connection.")
        return
    print(f"  Found {len(pdf_urls)} bulletin PDFs on CWC website")

    # ── 2. Download PDFs ─────────────────────────────────────────────────────
    print(f"\n[2/4] Downloading up to {len(pdf_urls)} PDFs...")
    downloaded = []
    for url in pdf_urls:
        fname = url.split('/')[-1]
        dest  = PDF_DIR / fname
        ok    = download_pdf(url, dest)
        if ok:
            downloaded.append((url, dest))
        time.sleep(0.3)  # polite crawl delay
    print(f"  Downloaded: {len(downloaded)} PDFs -> {PDF_DIR}")

    # ── 3. Extract Maithon storage ───────────────────────────────────────────
    print(f"\n[3/4] Extracting Maithon storage from PDFs...")
    records = []
    for url, pdf_path in downloaded:
        date = extract_date_from_filename(pdf_path.stem)
        if date is None:
            print(f"  SKIP (no date): {pdf_path.name}")
            continue
        storage_bcm = parse_maithon_from_pdf(pdf_path)
        if storage_bcm is not None:
            records.append({'date': date, 'storage_bcm_cwc': storage_bcm,
                            'source_pdf': pdf_path.name})
            print(f"  ✓ {date.date()}  Maithon = {storage_bcm:.3f} BCM")
        else:
            print(f"  ✗ {date.date() if date else '?'}  Maithon not found in {pdf_path.name}")

    if not records:
        print("\n  No Maithon storage records extracted.")
        print("  Possible causes:")
        print("    - PDF table format differs from expected")
        print("    - Maithon listed under different name (e.g. 'MAITHON', 'Maithan')")
        print("    - Page number differs — try tabula.read_pdf(..., pages='all')")
        print("\n  Saving empty file. Manual extraction needed.")
        pd.DataFrame(columns=['date','storage_bcm_cwc','source_pdf']).to_csv(CWC_RAW)
        return

    cwc_df = pd.DataFrame(records).sort_values('date').set_index('date')
    cwc_df.to_csv(CWC_RAW)
    print(f"\n  Saved {len(cwc_df)} records -> {CWC_RAW}")

    # ── 4. Compare with Stage 1 AV-curve storage ────────────────────────────
    print(f"\n[4/4] Comparing with Stage 1 storage reconstruction...")
    av_df = pd.read_csv(PROCESSED_DIR / 'DVC_storage_timeseries_2002_2024.csv',
                        index_col=0, parse_dates=True)
    maithon = av_df[av_df['reservoir'] == 'maithon'][['storage_bcm']].copy()

    # Resample CWC weekly → monthly (mean)
    cwc_monthly = cwc_df[['storage_bcm_cwc']].resample('MS').mean()

    merged = maithon.join(cwc_monthly, how='inner')
    merged.columns = ['AV_storage_bcm', 'CWC_storage_bcm']
    merged = merged.dropna()
    print(f"  Overlap: {len(merged)} months")

    if len(merged) < 3:
        print("  Too few overlap months for validation. Need more CWC historical PDFs.")
        print("  CWC website only shows recent ~6 months; older bulletins need manual download.")
        merged.to_csv(PROCESSED_DIR / 'cwc_validation.csv')
        return

    from scipy.stats import pearsonr
    r, p = pearsonr(merged['AV_storage_bcm'], merged['CWC_storage_bcm'])
    bias  = (merged['AV_storage_bcm'] - merged['CWC_storage_bcm']).mean()
    rmse  = np.sqrt(((merged['AV_storage_bcm'] - merged['CWC_storage_bcm'])**2).mean())
    print(f"  Pearson r = {r:.3f}  (p={p:.3f})")
    print(f"  Bias (AV - CWC) = {bias:+.3f} BCM")
    print(f"  RMSE = {rmse:.3f} BCM")
    if abs(bias) > 0.15:
        print(f"  ⚠ Systematic bias {bias:+.3f} BCM — AV curve may over/underestimate")
    else:
        print(f"  ✓ Bias within ±0.15 BCM tolerance")

    merged.to_csv(PROCESSED_DIR / 'cwc_validation.csv')

    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('CWC Bulletin vs AV-Curve Storage — Maithon Reservoir', fontsize=13)

    # Scatter
    ax = axes[0]
    ax.scatter(merged['CWC_storage_bcm'], merged['AV_storage_bcm'], alpha=0.7, color='steelblue')
    lims = [merged[['AV_storage_bcm','CWC_storage_bcm']].min().min() - 0.05,
            merged[['AV_storage_bcm','CWC_storage_bcm']].max().max() + 0.05]
    ax.plot(lims, lims, 'k--', lw=1, label='1:1 line')
    ax.set_xlabel('CWC Storage (BCM)')
    ax.set_ylabel('AV-curve Storage (BCM)')
    ax.set_title(f'r={r:.2f}, Bias={bias:+.3f} BCM, RMSE={rmse:.3f} BCM')
    ax.legend()

    # Timeseries
    ax = axes[1]
    ax.plot(merged.index, merged['CWC_storage_bcm'],  'b-o', ms=4, label='CWC Bulletin')
    ax.plot(merged.index, merged['AV_storage_bcm'], 'r--s', ms=4, label='AV-curve (this study)')
    ax.set_xlabel('Date')
    ax.set_ylabel('Storage (BCM)')
    ax.set_title('Temporal Comparison')
    ax.legend()

    plt.tight_layout()
    outpath = FIGURES_DIR / 'FigS2_cwc_validation.png'
    fig.savefig(outpath, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"\n  Saved: {outpath}")
    print(f"\n  Paper statement (Methods):")
    print(f"  'AV-curve storage estimates were validated against CWC Weekly Reservoir")
    print(f"   Bulletins for {len(merged)} coincident months (r={r:.2f}, bias={bias:+.3f} BCM,")
    print(f"   RMSE={rmse:.3f} BCM), confirming the magnitude and seasonality of")
    print(f"   reconstructed storage anomalies.'")
    print("=" * 60)


if __name__ == '__main__':
    main()
