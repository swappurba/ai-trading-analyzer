import os
from dotenv import load_dotenv

load_dotenv(override=True)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
NEWS_API_KEY      = os.getenv("NEWS_API_KEY", "")
FINNHUB_API_KEY   = os.getenv("FINNHUB_API_KEY", "")

INDONESIAN_INDICES = {
    "IHSG (^JKSE)": "^JKSE",
    "LQ45": "^JKLQ45",
}

GLOBAL_INDICES = {
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "Dow Jones": "^DJI",
    "Nikkei 225": "^N225",
    "Hang Seng": "^HSI",
    "FTSE 100": "^FTSE",
    "DAX": "^GDAXI",
    "Shanghai": "000001.SS",
}

COMMODITIES = {
    "Gold": "GC=F",
    "Silver": "SI=F",
    "Crude Oil (WTI)": "CL=F",
    "Natural Gas": "NG=F",
    "Copper": "HG=F",
    "Coal": "MTF=F",
    "Palm Oil (Malaysia)": "FCPO=F",
    "Nickel": "NI=F",
}

CURRENCIES = {
    "USD/IDR": "USDIDR=X",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "JPY/USD": "JPYUSD=X",
    "CNY/USD": "CNYUSD=X",
    "AUD/USD": "AUDUSD=X",
}

# ── Daftar lengkap saham IDX — LQ45 + IDXBUMN20 + sektor leaders (~120 saham) ──
POPULAR_IDX_STOCKS = [
    # ── Perbankan ──
    "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "BRIS.JK",
    "BTPS.JK", "BJTM.JK", "BJBR.JK", "NISP.JK", "MEGA.JK",
    "PNBN.JK", "BNGA.JK", "BDMN.JK", "BNII.JK", "AGRO.JK",

    # ── Keuangan & Multifinance ──
    "ADMF.JK", "BFIN.JK", "MFIN.JK", "WOMF.JK",

    # ── Konsumer & Makanan ──
    "UNVR.JK", "ICBP.JK", "INDF.JK", "KLBF.JK", "HMSP.JK",
    "GGRM.JK", "SIDO.JK", "MYOR.JK", "ULTJ.JK", "CLEO.JK",
    "ADES.JK", "DLTA.JK", "MLBI.JK", "ROTI.JK", "HOKI.JK",
    "GOOD.JK", "JPFA.JK", "CPIN.JK", "MAIN.JK",

    # ── Teknologi & Telekomunikasi ──
    "TLKM.JK", "EXCL.JK", "ISAT.JK", "GOTO.JK", "BUKA.JK",
    "EMTK.JK", "MNCN.JK", "SCMA.JK", "MTDL.JK", "DMMX.JK",
    "TOWR.JK", "TBIG.JK",

    # ── Pertambangan & Energi ──
    "ADRO.JK", "PTBA.JK", "ITMG.JK", "HRUM.JK", "INCO.JK",
    "ANTM.JK", "MDKA.JK", "MEDC.JK", "ESSA.JK", "MBMA.JK",
    "TINS.JK", "DOID.JK", "BYAN.JK", "ARII.JK", "BORN.JK",

    # ── Minyak & Gas ──
    "PGAS.JK", "AKRA.JK", "ELSA.JK", "ENRG.JK", "RUIS.JK",

    # ── Properti ──
    "BSDE.JK", "CTRA.JK", "LPKR.JK", "PWON.JK", "ASRI.JK",
    "JRPT.JK", "SMRA.JK", "DUTI.JK", "INPP.JK", "KIJA.JK",
    "APLN.JK", "PJAA.JK",

    # ── Konstruksi & Infrastruktur ──
    "WIKA.JK", "WSKT.JK", "PTPP.JK", "ADHI.JK", "WTON.JK",
    "JSMR.JK", "SIKA.JK", "NRCA.JK",

    # ── Semen & Material ──
    "SMGR.JK", "INTP.JK", "SMCB.JK", "SMBR.JK",

    # ── Otomotif & Industri ──
    "ASII.JK", "UNTR.JK", "ASTRA.JK", "AUTO.JK", "GJTL.JK",
    "SMSM.JK", "IMAS.JK",

    # ── Perkebunan ──
    "AALI.JK", "SIMP.JK", "SSMS.JK", "LSIP.JK", "BWPT.JK",
    "SGRO.JK", "TAPG.JK",

    # ── Kesehatan & Farmasi ──
    "MIKA.JK", "SILO.JK", "HEAL.JK", "PRDA.JK", "KLBF.JK",
    "KAEF.JK", "SIDO.JK", "MERK.JK",

    # ── Retail & Perdagangan ──
    "MAPI.JK", "LPPF.JK", "RALS.JK", "ERAA.JK", "AMRT.JK",
    "MIDI.JK", "CSAP.JK", "ACES.JK",

    # ── Media & Entertainment ──
    "SCMA.JK", "MNCN.JK", "NETV.JK", "FILM.JK",

    # ── Logistik & Pelayaran ──
    "SMDR.JK", "MBSS.JK", "TMAS.JK", "WINS.JK",

    # ── Lain-lain (LQ45/IDX30) ──
    "INKP.JK", "TKIM.JK", "BRPT.JK", "INAI.JK", "ARNA.JK",
]

# Hapus duplikat sambil pertahankan urutan
_seen = set()
_unique = []
for _t in POPULAR_IDX_STOCKS:
    if _t not in _seen:
        _seen.add(_t)
        _unique.append(_t)
POPULAR_IDX_STOCKS = _unique

POPULAR_GLOBAL_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "META", "TSLA", "BABA", "TCEHY", "TSM",
    "JPM", "BAC", "GS", "WMT", "JNJ",
]

SECTOR_MAP = {
    "Perbankan":          ["BBCA.JK","BBRI.JK","BMRI.JK","BBNI.JK","BRIS.JK","BTPS.JK","BJTM.JK","BJBR.JK","NISP.JK","MEGA.JK","PNBN.JK","BNGA.JK","BDMN.JK","BNII.JK","AGRO.JK"],
    "Keuangan":           ["ADMF.JK","BFIN.JK","MFIN.JK","WOMF.JK"],
    "Konsumer":           ["UNVR.JK","ICBP.JK","INDF.JK","KLBF.JK","HMSP.JK","GGRM.JK","SIDO.JK","MYOR.JK","ULTJ.JK","CLEO.JK","ADES.JK","DLTA.JK","MLBI.JK","ROTI.JK","HOKI.JK","GOOD.JK"],
    "Teknologi & Telko":  ["TLKM.JK","EXCL.JK","ISAT.JK","GOTO.JK","BUKA.JK","EMTK.JK","MNCN.JK","SCMA.JK","MTDL.JK","TOWR.JK","TBIG.JK"],
    "Pertambangan":       ["ADRO.JK","PTBA.JK","ITMG.JK","HRUM.JK","INCO.JK","ANTM.JK","MDKA.JK","MEDC.JK","ESSA.JK","MBMA.JK","TINS.JK","DOID.JK","BYAN.JK"],
    "Energi & Migas":     ["PGAS.JK","AKRA.JK","ELSA.JK","ENRG.JK","RUIS.JK"],
    "Properti":           ["BSDE.JK","CTRA.JK","LPKR.JK","PWON.JK","ASRI.JK","JRPT.JK","SMRA.JK","DUTI.JK","INPP.JK","KIJA.JK","APLN.JK"],
    "Konstruksi":         ["WIKA.JK","WSKT.JK","PTPP.JK","ADHI.JK","WTON.JK","JSMR.JK","NRCA.JK"],
    "Semen & Material":   ["SMGR.JK","INTP.JK","SMCB.JK","SMBR.JK"],
    "Otomotif & Industri":["ASII.JK","UNTR.JK","AUTO.JK","GJTL.JK","SMSM.JK","IMAS.JK"],
    "Perkebunan":         ["AALI.JK","SIMP.JK","SSMS.JK","LSIP.JK","SGRO.JK","TAPG.JK"],
    "Kesehatan":          ["MIKA.JK","SILO.JK","HEAL.JK","PRDA.JK","KAEF.JK","MERK.JK"],
    "Retail":             ["MAPI.JK","LPPF.JK","RALS.JK","ERAA.JK","AMRT.JK","MIDI.JK","ACES.JK"],
    "Poultry & Agri":     ["JPFA.JK","CPIN.JK","MAIN.JK"],
    "Pulp & Kertas":      ["INKP.JK","TKIM.JK","BRPT.JK"],
    "Lainnya":            ["SMDR.JK","MBSS.JK","TMAS.JK","WINS.JK","INAI.JK","ARNA.JK","NETV.JK","FILM.JK"],
}

RSI_OVERBOUGHT   = 70
RSI_OVERSOLD     = 30
MACD_SIGNAL_PERIOD = 9

TIMEFRAMES = {
    "1 Bulan":  "1mo",
    "3 Bulan":  "3mo",
    "6 Bulan":  "6mo",
    "1 Tahun":  "1y",
    "2 Tahun":  "2y",
    "5 Tahun":  "5y",
}

INTERVALS = {
    "Harian":   "1d",
    "Mingguan": "1wk",
    "Bulanan":  "1mo",
}
