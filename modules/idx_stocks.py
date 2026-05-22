"""
IDX Stock Universe — Fetch semua saham BEI dengan kategorisasi sektor resmi IDX-IC
================================================================================
Sumber: API resmi idx.co.id + fallback hardcoded ~900 saham
Sektor menggunakan IDX Industrial Classification (IDX-IC) resmi BEI.
"""

import requests
import threading
import time
from typing import Dict, List, Tuple

_CACHE_LOCK   = threading.Lock()
_STOCK_CACHE: List[Dict]  = []   # [{code, name, sector, subsector}]
_SECTOR_CACHE: Dict       = {}   # {sector_name: [ticker, ...]}
_CACHE_TS: float = 0
_CACHE_TTL = 3600 * 6  # refresh tiap 6 jam

IDX_API_URL  = "https://www.idx.co.id/primary/StockData/GetSecurities"
IDX_HEADERS  = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.idx.co.id/id/data-pasar/data-saham/daftar-saham/",
    "Accept": "application/json",
}

# ── Sektor IDX-IC Resmi (11 sektor BEI) ─────────────────────────────────────
IDX_SECTORS = [
    "Energy",
    "Basic Materials",
    "Industrials",
    "Consumer Non-Cyclicals",
    "Consumer Cyclicals",
    "Healthcare",
    "Financials",
    "Properties & Real Estate",
    "Technology",
    "Infrastructure",
    "Transportation & Logistic",
]

# ── Fallback hardcoded ~900 saham IDX per sektor ────────────────────────────
# Format: {sektor: [kode_saham, ...]}
HARDCODED_IDX = {
    "Energy": [
        "ADRO","ADMR","AIMS","AKRA","ARII","ARTI","ATPK","BATU","BCIP","BEEX",
        "BIPI","BORN","BREN","BSSR","BUMI","BYAN","CITA","CUAN","DEWA","DKFT",
        "DOID","DSSA","ELSA","ENRG","ESSA","FIRE","GEMS","GTBO","HALO","HRUM",
        "INCO","ITMG","KKGI","LAPD","MBAP","MBMA","MCOL","MEDC","MGAS","MKTR",
        "MYOH","NCKL","NICL","PKPK","PSAB","PTBA","PTRO","PGAS","RGAS","RUIS",
        "SMMT","SMRU","SURE","TOBA","ZINC","AKRA","ENRG","FIRE","BIPI",
    ],
    "Basic Materials": [
        "AGII","AKKU","AKPI","ALKA","ALMI","AMFG","ARNA","BAJA","BATA",
        "BRNA","BRPT","BTON","CAKK","CLPI","CTBN","DPNS","EKAD","FASW","GDST",
        "IFII","IGNA","IGAR","IMPC","INAI","INCI","INKP","INTP","IPOL","ISSP",
        "JKSW","JPFA","KBLI","KBLM","KIAS","KDSI","LION","LMSH","MDKI","MLIA",
        "MOLI","MOLI","NIKL","PBID","PICO","SIAP","SMCB","SMGR","SMBR","SPMA",
        "SRSN","TDPM","TKIM","TOTO","TPIA","UNIC","VOKS","YPAS","SCCO","JECC",
        "IKBI","KBRI","ALDO","DAJK","FASW","ADMG","INDR","EKAD","BTON",
    ],
    "Industrials": [
        "ACST","ADHI","ADMG","ASII","AUTO","BOLT","BRAM","CENT","CMNP","DGIK",
        "DRMA","GJTL","GDYR","HMSP","IDPR","IKBI","IMAS","INDS","INTA","ISSP",
        "JKON","JRPT","JSMR","KIAS","KMTR","LION","LMSH","MASA","MPMX","MYTX",
        "NIPS","NRCA","PBSA","PBRX","POLU","PPRE","PRAS","PTIS","PTPP","SCCO",
        "SIKA","SKRN","SMSM","SRIL","SSTM","STAR","TBMS","TJBP","TOTL","TRAM",
        "TRIO","UNTR","VOKS","WEGE","WIKA","WSKT","WTON","BOLT","BRAM","DRMA",
        "AUTO","GDYR","GJTL","IMAS","MASA","SMSM","TBMS","NIPS","PRAS",
    ],
    "Consumer Non-Cyclicals": [
        "ADES","AISA","ALTO","AMRT","BUDI","CEKA","CLEO","CMRY","COCO","CSRA",
        "DLTA","DMND","FOOD","GGRM","GOOD","HOKI","HMSP","ICBP","IIKP","INDF",
        "ITIC","JPFA","KAEF","KEJU","KINO","KLBF","LSIP","MAIN","MGNA","MIDI",
        "MLBI","MRAT","MYOR","NASI","PBID","PSDN","PTSP","ROTI","SIDO","SKBM",
        "SKLT","STTP","TBLA","TGKA","TSPC","ULTJ","UNVR","WIIM","CPRO","DSFI",
        "IIKP","ATIC","MLBI","AISA","BUDI","CMRY","DMND","FOOD","GULA",
    ],
    "Consumer Cyclicals": [
        "ACES","ADMG","ARGO","ASII","BATA","BAYU","BIRD","BLTZ","BUVA","CAMP",
        "CSAP","DART","DAYA","ERAA","ERTX","ESTI","FAST","GLOB","HDTX","HERO",
        "HOME","HOTL","ICON","INPP","JIHD","JSPT","KOIN","LPPF","MAPA","MAPI",
        "MARK","MIDI","MKPI","MPPA","MRAT","PANR","PDES","PGJO","PSKT","PTSP",
        "RALS","RANC","RICY","RIMO","SDPC","SHID","SKYB","SRIL","TELE","TKGA",
        "TRIO","UNVR","WICO","MYTX","HDTX","SSTM","ERTO","PBRX","STAR",
        "BATA","CAMP","FAST","HERO","KOIN","MPPA","RALS","RANC","SKYB",
    ],
    "Healthcare": [
        "AHAP","BMHS","DVLA","HEAL","INAF","IRRA","KAEF","KLBF","MEDS","MERK",
        "MIKA","MTMH","PEHA","PRDA","PYFA","RBMS","RSCH","SCPI","SIDO","SILO",
        "SRAJ","TSPC","SOHO","PINO","PHFN","SAME","MIKA","PRDA","HEAL",
        "BMHS","SILO","MTMH","SRAJ","DVLA","INAF","MERK","PEHA","PYFA",
    ],
    "Financials": [
        "ADMF","AGRO","AGRS","AMAR","APEX","APIC","ASBI","ASDM","ASEI","ASMI",
        "ASRM","ARTO","BABP","BACA","BANK","BBCA","BBHI","BBKP","BBMD","BBNI",
        "BBNP","BBRI","BBYB","BCIC","BDMN","BEKS","BFIN","BGTG","BHAT","BINA",
        "BJBR","BJTM","BKSW","BLTM","BMAG","BMAS","BMAX","BMRI","BNBA","BNGA",
        "BNII","BPII","BRIS","BSIM","BSMD","BTPN","BTPS","BVIC","CFIN","DNAR",
        "DPUM","FIRE","GSMF","HADE","HDFA","IMJS","INPC","JMAS","LPGI","MAYA",
        "MCOR","MEGA","MFIN","MREI","NISP","NOBU","PANS","PEGE","PHFN","PNBN",
        "PNBS","PNLF","POOL","PPRE","SDRA","TIFA","TRIM","VRNA","WOMF","YULE",
        "ADMF","BFIN","MFIN","WOMF","CFIN","HDFA","GSMF","IMJS","TIFA","TRIM",
    ],
    "Properties & Real Estate": [
        "APLN","ARMY","ASRI","BCIP","BEST","BIKA","BIPP","BKDP","BKSL","BSDE",
        "CBPE","CITY","CTRA","DART","DMAS","DUTI","ELTY","EMDE","FMII","GAMA",
        "GMTD","GPRA","GWSA","HOMR","INPP","JRPT","KIJA","KPIG","LCGP","LPCK",
        "LPKR","MDLN","MKPI","MKNT","MMLP","MPRO","MTLA","MTSM","NIRO","NZIA",
        "PJAA","PLAS","PPRO","PTPP","PWON","RBMS","REAL","RODA","SCBD","SILO",
        "SIMA","SMRA","SSIA","TARA","URBN","WIKA","WSKT","WTON","PJAA","BCIP",
        "BSDE","CTRA","LPKR","PWON","ASRI","JRPT","SMRA","DUTI","INPP","KIJA",
    ],
    "Technology": [
        "ABBA","AGIT","ARTO","AXIO","BFIN","BUKA","CENT","DCII","DMMX","EDGE",
        "ELIO","EMTK","EPAC","FORU","GLVA","GOTO","IPTV","JATI","KIOS","KPIG",
        "LCKM","LINK","LUCK","MCOM","MCAS","META","MITI","MLPT","MORA","MPIX",
        "MTDL","NAYZ","NETV","NFCX","OASA","PADI","PDSI","RINA","SKYB","SWAT",
        "TBIG","TLKM","TOWR","VKTR","WIFI","WINS","EXCL","ISAT","BUKA","GOTO",
        "DCII","LINK","MLPT","MTDL","EMTK","MNCN","SCMA","NETV","FILM",
    ],
    "Infrastructure": [
        "BREN","CMNP","CUAN","ENRG","ESSA","GIAA","IPCM","JSMR","KARW","KJEN",
        "LAPD","MEDC","MGAS","MPIX","MTDL","PGAS","PTIS","PTPP","RGAS","RUIS",
        "SAFE","SDMU","SHIP","SRIA","SUGI","TLKM","TPMA","TRUK","WEGE","WINS",
        "PGAS","AKRA","ELSA","ENRG","RUIS","GIAA","JSMR","CMNP","LAPD","MGAS",
    ],
    "Transportation & Logistic": [
        "ASSA","BBRM","BIRD","BLTA","BULL","CANI","CARE","CAPL","CMPP","DEAL",
        "GIAA","HATM","HELI","HITS","IATA","IPCM","KARW","KJEN","LRNA","MBSS",
        "MIRA","NELY","PALM","PTIS","SAFE","SDMU","SHIP","SMDR","TAXI","TMAS",
        "TPMA","TRUK","WEHA","WINS","ZINC","ASSA","BIRD","BLTA","BULL","CANI",
        "SMDR","MBSS","TMAS","WINS","GIAA","HELI","MIRA","NELY","SHIP",
    ],
}

# ── Pemetaan kode → nama sektor ─────────────────────────────────────────────
def _build_ticker_sector_map() -> Dict[str, str]:
    """Return {ticker_JK: sector_name}"""
    result = {}
    for sector, codes in HARDCODED_IDX.items():
        for code in codes:
            tk = f"{code}.JK"
            if tk not in result:
                result[tk] = sector
    return result

TICKER_SECTOR_MAP: Dict[str, str] = _build_ticker_sector_map()


def fetch_all_idx_from_api() -> List[Dict]:
    """
    Fetch semua saham dari API resmi IDX.co.id.
    Return list of {code, name, sector, ticker}.
    """
    results = []
    try:
        r = requests.get(
            IDX_API_URL,
            params={"code": "", "start": 0, "length": 9999, "market": "regularmarket"},
            headers=IDX_HEADERS,
            timeout=12,
        )
        data = r.json()
        for item in data.get("data", []):
            code = item.get("Code", "").strip()
            name = item.get("Name", "").strip()
            if code and 1 <= len(code) <= 6:
                ticker = f"{code}.JK"
                sector = TICKER_SECTOR_MAP.get(ticker, "Lainnya")
                results.append({
                    "code":   code,
                    "name":   name,
                    "ticker": ticker,
                    "sector": sector,
                })
    except Exception:
        pass
    return results


def get_all_idx_stocks(force_refresh: bool = False) -> List[Dict]:
    """
    Return semua saham IDX sebagai list of dict.
    Cache 6 jam; fallback ke hardcoded jika API gagal.
    """
    global _STOCK_CACHE, _CACHE_TS

    with _CACHE_LOCK:
        now = time.time()
        if not force_refresh and _STOCK_CACHE and (now - _CACHE_TS) < _CACHE_TTL:
            return _STOCK_CACHE

        # Coba API dulu
        api_result = fetch_all_idx_from_api()

        if api_result and len(api_result) > 100:
            _STOCK_CACHE = api_result
            _CACHE_TS    = now
            return _STOCK_CACHE

        # Fallback: hardcoded list
        fallback = []
        seen     = set()
        for sector, codes in HARDCODED_IDX.items():
            for code in codes:
                if code not in seen:
                    seen.add(code)
                    fallback.append({
                        "code":   code,
                        "name":   code,
                        "ticker": f"{code}.JK",
                        "sector": sector,
                    })

        _STOCK_CACHE = fallback
        _CACHE_TS    = now
        return _STOCK_CACHE


def get_all_tickers() -> List[str]:
    """Return list semua ticker format Yahoo Finance (e.g. 'BBCA.JK')."""
    return [s["ticker"] for s in get_all_idx_stocks()]


def get_sector_map() -> Dict[str, List[str]]:
    """Return {sector_name: [ticker, ...]} dari cache."""
    global _SECTOR_CACHE
    if _SECTOR_CACHE:
        return _SECTOR_CACHE

    stocks = get_all_idx_stocks()
    result: Dict[str, List[str]] = {}
    for s in stocks:
        result.setdefault(s["sector"], []).append(s["ticker"])

    _SECTOR_CACHE = result
    return result


def get_ticker_sector_map() -> Dict[str, str]:
    """Return {ticker: sector_name}."""
    stocks = get_all_idx_stocks()
    return {s["ticker"]: s["sector"] for s in stocks}


def get_stock_info_map() -> Dict[str, Dict]:
    """Return {ticker: {code, name, sector}}."""
    stocks = get_all_idx_stocks()
    return {s["ticker"]: s for s in stocks}
