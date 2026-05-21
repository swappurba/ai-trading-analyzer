import os
import requests
import threading
from dotenv import load_dotenv

load_dotenv(override=True)

# ── Fetch semua saham IDX dari API resmi IDX.co.id ────────────────────────────
_idx_all_stocks_cache: list = []
_idx_cache_lock = threading.Lock()

def fetch_all_idx_stocks() -> list[str]:
    """
    Ambil seluruh daftar saham tercatat di BEI (IDX) via API resmi.
    Return list ticker format Yahoo Finance (e.g. 'BBCA.JK').
    Cache hasil agar tidak fetch ulang di session yang sama.
    """
    global _idx_all_stocks_cache
    with _idx_cache_lock:
        if _idx_all_stocks_cache:
            return _idx_all_stocks_cache

        url = "https://www.idx.co.id/primary/StockData/GetSecurities"
        params = {"code": "", "start": 0, "length": 9999, "market": "regularmarket"}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.idx.co.id/",
        }
        try:
            r = requests.get(url, params=params, headers=headers, timeout=10)
            data = r.json()
            stocks = []
            for item in data.get("data", []):
                code = item.get("Code", "").strip()
                if code and len(code) <= 6:
                    stocks.append(f"{code}.JK")
            if stocks:
                _idx_all_stocks_cache = sorted(set(stocks))
                return _idx_all_stocks_cache
        except Exception:
            pass

        # Fallback: gunakan POPULAR_IDX_STOCKS jika API gagal
        _idx_all_stocks_cache = list(POPULAR_IDX_STOCKS)
        return _idx_all_stocks_cache

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

# ── Daftar lengkap saham IDX ~600+ saham (fallback jika API IDX tidak tersedia) ──
POPULAR_IDX_STOCKS = [
    # ── Perbankan ──
    "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "BRIS.JK",
    "BTPS.JK", "BJTM.JK", "BJBR.JK", "NISP.JK", "MEGA.JK",
    "PNBN.JK", "BNGA.JK", "BDMN.JK", "BNII.JK", "AGRO.JK",
    "BMAS.JK", "ARTO.JK", "BABP.JK", "BACA.JK", "BBHI.JK",
    "BBKP.JK", "BBMD.JK", "BBNP.JK", "BCIC.JK", "BDMN.JK",
    "BEKS.JK", "BGTG.JK", "BHAT.JK", "BINA.JK", "BKSW.JK",
    "BLTM.JK", "BMAG.JK", "BMAX.JK", "BNBA.JK", "BNGA.JK",
    "BPII.JK", "BSIM.JK", "BTPN.JK", "BVIC.JK", "DNAR.JK",
    "INPC.JK", "MAYA.JK", "MCOR.JK", "NOBU.JK", "PNBS.JK",
    "SDRA.JK", "AGRS.JK", "AMAR.JK", "BANK.JK",

    # ── Keuangan & Multifinance ──
    "ADMF.JK", "BFIN.JK", "MFIN.JK", "WOMF.JK",
    "AFPI.JK", "AMAG.JK", "APEX.JK", "ASBI.JK", "ASDM.JK",
    "ASEI.JK", "ASMI.JK", "ASRM.JK", "DPUM.JK", "FIRE.JK",
    "GSMF.JK", "HADE.JK", "HDFA.JK", "IMJS.JK", "JMAS.JK",
    "LPGI.JK", "MREI.JK", "PANS.JK", "PEGE.JK", "PHFN.JK",
    "POOL.JK", "PPRE.JK", "TIFA.JK", "TRIM.JK", "VRNA.JK",
    "YULE.JK",

    # ── Konsumer & Makanan & Minuman ──
    "UNVR.JK", "ICBP.JK", "INDF.JK", "KLBF.JK", "HMSP.JK",
    "GGRM.JK", "SIDO.JK", "MYOR.JK", "ULTJ.JK", "CLEO.JK",
    "ADES.JK", "DLTA.JK", "MLBI.JK", "ROTI.JK", "HOKI.JK",
    "GOOD.JK", "JPFA.JK", "CPIN.JK", "MAIN.JK",
    "AISA.JK", "ALTO.JK", "CAMP.JK", "CBSA.JK", "CEKA.JK",
    "CMRY.JK", "COCO.JK", "CSRA.JK", "DMND.JK", "FOOD.JK",
    "GULA.JK", "IIKP.JK", "INAF.JK", "ITIC.JK", "KEJU.JK",
    "KINO.JK", "LSIP.JK", "MGNA.JK", "MRMA.JK", "MRAT.JK",
    "MYOR.JK", "NASI.JK", "NIPS.JK", "PCAR.JK", "PSDN.JK",
    "PTSP.JK", "SKBM.JK", "SKLT.JK", "STTP.JK", "TBLA.JK",
    "TGKA.JK", "TSPC.JK", "UNVR.JK", "WIIM.JK",

    # ── Teknologi & Telekomunikasi ──
    "TLKM.JK", "EXCL.JK", "ISAT.JK", "GOTO.JK", "BUKA.JK",
    "EMTK.JK", "MNCN.JK", "SCMA.JK", "MTDL.JK", "DMMX.JK",
    "TOWR.JK", "TBIG.JK",
    "ABBA.JK", "AXIO.JK", "CENT.JK", "DCII.JK", "EDGE.JK",
    "ELIO.JK", "EPAC.JK", "FORU.JK", "GLVA.JK", "IPTV.JK",
    "JATI.JK", "KIOS.JK", "KPIG.JK", "LCKM.JK", "LINK.JK",
    "LUCK.JK", "MCOM.JK", "MCAS.JK", "META.JK", "MITI.JK",
    "MLPT.JK", "MORA.JK", "MPIX.JK", "NAYZ.JK", "NFCX.JK",
    "PADI.JK", "PDSI.JK", "RINA.JK", "SKYB.JK", "SWAT.JK",
    "VKTR.JK", "WIFI.JK", "WINS.JK",

    # ── Pertambangan & Energi ──
    "ADRO.JK", "PTBA.JK", "ITMG.JK", "HRUM.JK", "INCO.JK",
    "ANTM.JK", "MDKA.JK", "MEDC.JK", "ESSA.JK", "MBMA.JK",
    "TINS.JK", "DOID.JK", "BYAN.JK", "ARII.JK", "BORN.JK",
    "ARTI.JK", "ATPK.JK", "BIPI.JK", "BSSR.JK", "BUMI.JK",
    "DEWA.JK", "DKFT.JK", "DSSA.JK", "FIRE.JK", "GEMS.JK",
    "GTBO.JK", "HALO.JK", "KKGI.JK", "MBAP.JK", "MYOH.JK",
    "NCKL.JK", "NICL.JK", "PKPK.JK", "PSAB.JK", "PTRO.JK",
    "SMMT.JK", "SURE.JK", "TOBA.JK", "ZINC.JK",

    # ── Minyak & Gas ──
    "PGAS.JK", "AKRA.JK", "ELSA.JK", "ENRG.JK", "RUIS.JK",
    "ARTI.JK", "BEEX.JK", "BIPI.JK", "BREN.JK", "CMPP.JK",
    "CUAN.JK", "DEWA.JK", "ERAA.JK", "FIMP.JK", "LAPD.JK",
    "MGAS.JK", "PNLF.JK", "PTIS.JK", "RGAS.JK", "SUGI.JK",
    "TPMA.JK",

    # ── Properti ──
    "BSDE.JK", "CTRA.JK", "LPKR.JK", "PWON.JK", "ASRI.JK",
    "JRPT.JK", "SMRA.JK", "DUTI.JK", "INPP.JK", "KIJA.JK",
    "APLN.JK", "PJAA.JK",

    # ── Konstruksi & Infrastruktur ──
    "WIKA.JK", "WSKT.JK", "PTPP.JK", "ADHI.JK", "WTON.JK",
    "JSMR.JK", "SIKA.JK", "NRCA.JK",
    "ACST.JK", "CASS.JK", "DGIK.JK", "IDPR.JK", "IKBI.JK",
    "JKON.JK", "MTRA.JK", "PBSA.JK", "PPRO.JK", "PTIS.JK",
    "SKRN.JK", "SSIA.JK", "TOTL.JK", "TRIO.JK", "WEGE.JK",

    # ── Semen & Material Bangunan ──
    "SMGR.JK", "INTP.JK", "SMCB.JK", "SMBR.JK",
    "ARNA.JK", "CAKK.JK", "DPNS.JK", "EKAD.JK", "IFII.JK",
    "INAI.JK", "ISSP.JK", "JKSW.JK", "KIAS.JK", "LION.JK",
    "LMSH.JK", "MLIA.JK", "MOLI.JK", "NIKL.JK", "PBID.JK",
    "PICO.JK", "SIAP.JK", "SRSN.JK", "TOTO.JK", "YPAS.JK",

    # ── Otomotif & Industri ──
    "ASII.JK", "UNTR.JK", "AUTO.JK", "GJTL.JK",
    "SMSM.JK", "IMAS.JK",
    "ADMG.JK", "BOLT.JK", "BRAM.JK", "DRMA.JK", "GDYR.JK",
    "INTA.JK", "INTP.JK", "IPOL.JK", "MASA.JK", "MPMX.JK",
    "MYTX.JK", "NIPS.JK", "PRAS.JK", "SRIL.JK", "TBMS.JK",

    # ── Perkebunan ──
    "AALI.JK", "SIMP.JK", "SSMS.JK", "LSIP.JK", "BWPT.JK",
    "SGRO.JK", "TAPG.JK",
    "ANJT.JK", "DSNG.JK", "GOZCO.JK", "JAWA.JK", "MAGP.JK",
    "PALM.JK", "PSGO.JK", "PTPW.JK", "SAWIT.JK", "SMART.JK",
    "TBLA.JK", "UNSP.JK",

    # ── Kesehatan & Farmasi ──
    "MIKA.JK", "SILO.JK", "HEAL.JK", "PRDA.JK", "KLBF.JK",
    "KAEF.JK", "SIDO.JK", "MERK.JK",
    "AHAP.JK", "AISA.JK", "BMHS.JK", "DVLA.JK", "INAF.JK",
    "IRRA.JK", "KLBF.JK", "MEDS.JK", "MTMH.JK", "PEHA.JK",
    "PYFA.JK", "RBMS.JK", "RSCH.JK", "SCPI.JK", "SRAJ.JK",

    # ── Retail & Perdagangan ──
    "MAPI.JK", "LPPF.JK", "RALS.JK", "ERAA.JK", "AMRT.JK",
    "MIDI.JK", "CSAP.JK", "ACES.JK",
    "CENT.JK", "CLPI.JK", "DAYA.JK", "EPMT.JK", "GLOB.JK",
    "HERO.JK", "KOIN.JK", "MAPI.JK", "MARK.JK", "MPPA.JK",
    "RANC.JK", "RIMO.JK", "SDPC.JK", "SKYB.JK", "TELE.JK",
    "TKGA.JK", "TRIO.JK",

    # ── Media & Entertainment ──
    "SCMA.JK", "MNCN.JK", "NETV.JK", "FILM.JK",
    "BMTR.JK", "JTPE.JK", "KBLV.JK", "MDIA.JK", "MSKY.JK",
    "VIVA.JK",

    # ── Logistik & Pelayaran & Transportasi ──
    "SMDR.JK", "MBSS.JK", "TMAS.JK", "WINS.JK",
    "ASSA.JK", "BBRM.JK", "BIRD.JK", "BLTA.JK", "BULL.JK",
    "CANI.JK", "CARE.JK", "CMNP.JK", "CMPP.JK", "DEAL.JK",
    "GIAA.JK", "HATM.JK", "HELI.JK", "INDX.JK", "IPCM.JK",
    "KARW.JK", "KJEN.JK", "LRNA.JK", "MBSS.JK", "MIRA.JK",
    "NELY.JK", "PALM.JK", "PTIS.JK", "SAFE.JK", "SDMU.JK",
    "SHIP.JK", "SMDR.JK", "TAXI.JK", "TPMA.JK", "TRUK.JK",
    "WEHA.JK", "ZINC.JK",

    # ── Kimia & Petrokimia ──
    "BRPT.JK", "TPIA.JK", "DPNS.JK", "EKAD.JK", "INCI.JK",
    "MDKI.JK", "MOLI.JK", "SRSN.JK", "TDPM.JK", "UNIC.JK",

    # ── Tekstil & Garmen ──
    "ARGO.JK", "ERTX.JK", "ESTI.JK", "HDTX.JK", "INDR.JK",
    "MYTX.JK", "PBRX.JK", "POLU.JK", "RICY.JK", "SRIL.JK",
    "SSTM.JK", "STAR.JK", "TEJA.JK", "TFCO.JK",

    # ── Pulp, Kertas & Percetakan ──
    "INKP.JK", "TKIM.JK", "FASW.JK", "DAJK.JK", "ALDO.JK",
    "DYAN.JK", "KBRI.JK", "KDSI.JK", "SPMA.JK",

    # ── Elektronik & Kabel ──
    "KBLI.JK", "KBLM.JK", "SCCO.JK", "VOKS.JK", "JECC.JK",
    "ADMG.JK", "IKBI.JK",

    # ── Hotel, Restoran & Pariwisata ──
    "PJAA.JK", "BAYU.JK", "BUVA.JK", "FAST.JK", "HOME.JK",
    "HOTL.JK", "ICON.JK", "INPP.JK", "JIHD.JK", "JSPT.JK",
    "MABA.JK", "PANR.JK", "PDES.JK", "PGJO.JK", "PSKT.JK",
    "PTSP.JK", "SHID.JK",

    # ── Investasi & Holding ──
    "BMTR.JK", "DSSA.JK", "GEMA.JK", "HADE.JK", "LPCK.JK",
    "MLPL.JK", "MNCN.JK", "MPMX.JK", "PLAS.JK", "PNLF.JK",
    "POOL.JK", "SILO.JK", "SIMA.JK", "SRTG.JK",

    # ── Lain-lain ──
    "ABDA.JK", "ABMM.JK", "ACST.JK", "AIMS.JK", "AKKU.JK",
    "AKPI.JK", "ALKA.JK", "ALMI.JK", "ALTO.JK", "AMFG.JK",
    "APII.JK", "APLI.JK", "ARGO.JK", "ASIA.JK", "ATPK.JK",
    "BAJA.JK", "BALI.JK", "BAPA.JK", "BATA.JK", "BAYU.JK",
    "BCIP.JK", "BIKA.JK", "BIMA.JK", "BIPP.JK", "BKDP.JK",
    "BKSL.JK", "BLTZ.JK", "BMSR.JK", "BNBR.JK", "BPFI.JK",
    "BRNA.JK", "BTON.JK", "BUVA.JK", "BVIC.JK", "CANI.JK",
    "CEKA.JK", "CFIN.JK", "CITA.JK", "CLPI.JK", "CMPP.JK",
    "CPIN.JK", "CPRO.JK", "CSAP.JK", "CTTH.JK", "DART.JK",
    "DEWA.JK", "DFAM.JK", "DKFT.JK", "DMAS.JK", "DSFI.JK",
    "DSNG.JK", "DUTI.JK", "DVLA.JK", "DYAN.JK", "ELTY.JK",
    "EMDE.JK", "EPMT.JK", "ESSA.JK", "FMII.JK", "FORZ.JK",
    "GAMA.JK", "GDST.JK", "GEMA.JK", "GMTD.JK", "GPRA.JK",
    "GWSA.JK", "HERO.JK", "HITS.JK", "HOMR.JK", "HRME.JK",
    "IATA.JK", "IBST.JK", "ICBP.JK", "IGAR.JK", "IMPC.JK",
    "INDS.JK", "INDX.JK", "ISAT.JK", "ISSP.JK", "ITIC.JK",
    "JAST.JK", "JAWA.JK", "JECC.JK", "JIHD.JK", "JPFA.JK",
    "JRPT.JK", "JSPT.JK", "KAEF.JK", "KARW.JK", "KBLI.JK",
    "KBLM.JK", "KDSI.JK", "KEJU.JK", "KIAS.JK", "KINO.JK",
    "KMTR.JK", "KOIN.JK", "KPIG.JK", "LINK.JK", "LION.JK",
    "LMSH.JK", "LPGI.JK", "LPPF.JK", "LSIP.JK", "LTLS.JK",
    "MABA.JK", "MAGP.JK", "MAPI.JK", "MARK.JK", "MASA.JK",
    "MBAP.JK", "MDIA.JK", "MEDS.JK", "MITI.JK", "MKNT.JK",
    "MLIA.JK", "MLPL.JK", "MPPA.JK", "MRAT.JK", "MREI.JK",
    "MSKY.JK", "MTDL.JK", "MYOH.JK", "NELY.JK", "NIKL.JK",
    "NIPS.JK", "NOBU.JK", "OASA.JK", "PANR.JK", "PDES.JK",
    "PEGE.JK", "PEHA.JK", "PICO.JK", "PNBS.JK", "POLU.JK",
    "POOL.JK", "PPRO.JK", "PRAS.JK", "PSAB.JK", "PSKT.JK",
    "PTBA.JK", "PTPP.JK", "PTRO.JK", "PYFA.JK", "RALS.JK",
    "RANC.JK", "RBMS.JK", "RICY.JK", "RIMO.JK", "ROTI.JK",
    "SAFE.JK", "SCCO.JK", "SCPI.JK", "SDMU.JK", "SDPC.JK",
    "SGRO.JK", "SHID.JK", "SHIP.JK", "SILO.JK", "SIMP.JK",
    "SKBM.JK", "SKLT.JK", "SKRN.JK", "SKYB.JK", "SMART.JK",
    "SMSM.JK", "SPMA.JK", "SRAJ.JK", "SRBI.JK", "SRIL.JK",
    "SRTG.JK", "SSMS.JK", "SSTM.JK", "STAR.JK", "STTP.JK",
    "SUGI.JK", "SURE.JK", "TAXI.JK", "TBIG.JK", "TBLA.JK",
    "TBMS.JK", "TDPM.JK", "TFCO.JK", "TGKA.JK", "TINS.JK",
    "TKGA.JK", "TKIM.JK", "TLKM.JK", "TMAS.JK", "TOBA.JK",
    "TOTO.JK", "TOTL.JK", "TOWR.JK", "TPMA.JK", "TRIO.JK",
    "TRUK.JK", "TSPC.JK", "ULTJ.JK", "UNIC.JK", "UNSP.JK",
    "UNTR.JK", "UNVR.JK", "VIVA.JK", "VKTR.JK", "VOKS.JK",
    "WEHA.JK", "WIFI.JK", "WIIM.JK", "WIKA.JK", "WINS.JK",
    "WTON.JK", "WSKT.JK", "YPAS.JK", "ZINC.JK",
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
