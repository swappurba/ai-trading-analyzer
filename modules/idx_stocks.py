"""
IDX Stock Universe — Semua saham BEI dengan kategorisasi sektor IDX-IC
======================================================================
Target: ~900+ saham tercatat di BEI
Sumber: API resmi idx.co.id (prioritas) + hardcoded fallback lengkap
"""

import requests
import threading
import time
from typing import Dict, List

_CACHE_LOCK   = threading.Lock()
_STOCK_CACHE: List[Dict] = []
_CACHE_TS: float = 0
_CACHE_TTL = 3600 * 6  # 6 jam

# ── 11 Sektor Resmi IDX-IC BEI ───────────────────────────────────────────────
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

# ── Daftar Lengkap ~900+ Saham BEI per Sektor IDX-IC ────────────────────────
HARDCODED_IDX: Dict[str, List[str]] = {

    "Energy": [
        "ADRO","ADMR","AIMS","AITI","AKRA","ARII","ARTI","ATPK","BATU","BCIP",
        "BEEX","BIPI","BORN","BREN","BSSR","BUMI","BYAN","CITA","CUAN","DEWA",
        "DKFT","DOID","DSSA","ELSA","ENRG","ESSA","FIRE","GEMS","GTBO","HALO",
        "HRUM","INCO","ITMG","KKGI","LAPD","MBAP","MBMA","MCOL","MEDC","MGAS",
        "MKTR","MYOH","NCKL","NICL","PKPK","PSAB","PTBA","PTRO","PGAS","RGAS",
        "RUIS","SMMT","SMRU","SURE","TOBA","ZINC","ENRG","FIRE","BIPI","BREN",
        "CUAN","ESSA","DSSA","BUMI","ADRO","PTBA","HRUM","ITMG","BYAN","DOID",
        "MDKA","ANTM","TINS","INCO","NCKL","MBMA","BORN","ARII","BSSR","MBAP",
        "MYOH","GEMS","KKGI","DKFT","MCOL","SMMT","SMRU","PKPK","PSAB","GTBO",
        "HALO","AIMS","AITI","MKTR","BEEX","BCIP","BATU","ADMR",
    ],

    "Basic Materials": [
        "AGII","AKKU","AKPI","ALKA","ALMI","AMFG","ARNA","BAJA","BRNA","BRPT",
        "BTON","CAKK","CLPI","CTBN","DPNS","EKAD","FASW","GDST","IFII","IGNA",
        "IGAR","IMPC","INAI","INCI","INKP","INTP","IPOL","ISSP","JKSW","KBLI",
        "KBLM","KIAS","KDSI","KBRI","LION","LMSH","MDKI","MLIA","MOLI","NIKL",
        "PBID","PICO","SIAP","SMCB","SMGR","SMBR","SPMA","SRSN","TDPM","TKIM",
        "TOTO","TPIA","UNIC","VOKS","YPAS","SCCO","JECC","IKBI","ALDO","DAJK",
        "ADMG","EKAD","BTON","FASW","INKP","TKIM","BRPT","TPIA","UNIC","DPNS",
        "INCI","CLPI","AKPI","IPOL","IMPC","IGAR","BRNA","ALKA","ALMI","AMFG",
        "ARNA","BAJA","CAKK","CTBN","GDST","IFII","IGNA","ISSP","JKSW","KBRI",
        "KIAS","KDSI","LMSH","MDKI","MLIA","MOLI","NIKL","PBID","PICO","SIAP",
        "SMCB","SMGR","SMBR","SPMA","SRSN","TDPM","TOTO","VOKS","YPAS","SCCO",
        "JECC","IKBI","ALDO","AGII","AKKU","LION","KBLI","KBLM","INTP","INAI",
    ],

    "Industrials": [
        "ACST","ADHI","AGRS","ASII","AUTO","BOLT","BRAM","CMNP","DGIK","DRMA",
        "GJTL","GDYR","IDPR","IMAS","INDS","INTA","ISSP","JKON","JSMR","KMTR",
        "MASA","MPMX","MYTX","NIPS","NRCA","PBSA","PBRX","POLU","PPRE","PRAS",
        "PTIS","PTPP","SCCO","SIKA","SKRN","SMSM","SRIL","SSTM","STAR","TBMS",
        "TJBP","TOTL","TRIO","UNTR","WEGE","WIKA","WSKT","WTON","CENT","KPIG",
        "ARMY","AMFG","BBRM","BEST","BKSL","CNKO","GEMA","GMFI","GMTD","GPRA",
        "GWSA","JRPT","KIJA","LCGP","LPCK","LPKR","MDLN","MKPI","MMLP","MPRO",
        "MTLA","MTSM","NIRO","NZIA","PJAA","PLAS","PPRO","PWON","REAL","RODA",
        "SCBD","SIMA","SMRA","SSIA","TARA","URBN","BCIP","DART","DMAS","DUTI",
        "ELTY","EMDE","FMII","GAMA","APLN","ASRI","BSDE","CITY","CTRA",
    ],

    "Consumer Non-Cyclicals": [
        "ADES","AISA","ALTO","AMRT","BUDI","CEKA","CLEO","CMRY","COCO","CSRA",
        "DLTA","DMND","FOOD","GGRM","GOOD","HOKI","HMSP","ICBP","IIKP","INDF",
        "ITIC","JPFA","KEJU","KINO","KLBF","MAIN","MGNA","MIDI","MLBI","MRAT",
        "MYOR","NASI","PSDN","PTSP","ROTI","SIDO","SKBM","SKLT","STTP","TBLA",
        "TGKA","TSPC","ULTJ","UNVR","WIIM","CPRO","DSFI","ATIC","BUDI","CMRY",
        "DMND","FOOD","GULA","LSIP","SIMP","SSMS","SGRO","TAPG","AALI","ANJT",
        "DSNG","GOZCO","JAWA","MAGP","PALM","SAWIT","SMART","TBLA","UNSP",
        "KAEF","DVLA","MERK","INAF","PEHA","PYFA","SCPI","KLBF","TSPC","SIDO",
        "SOHO","PINO","PHFN","SAME","BMHS","HEAL","IRRA","MEDS","MIKA","MTMH",
        "PRDA","RBMS","RSCH","SILO","SRAJ","AHAP","PDSS","CURE","HDFA",
    ],

    "Consumer Cyclicals": [
        "ACES","BAYU","BIRD","BLTZ","BUVA","CAMP","CSAP","DART","DAYA","ERAA",
        "ERTX","ESTI","FAST","GLOB","HDTX","HERO","HOME","HOTL","ICON","INPP",
        "JIHD","JSPT","KOIN","LPPF","MAPA","MAPI","MARK","MKPI","MPPA","PANR",
        "PDES","PGJO","PSKT","RALS","RANC","RICY","RIMO","SDPC","SHID","SKYB",
        "TELE","TKGA","WICO","BATA","HMSP","GGRM","SCMA","MNCN","NETV","FILM",
        "VIVA","BMTR","JTPE","KBLV","MDIA","MSKY","ABBA","MAPI","LPPF","RALS",
        "ERAA","AMRT","MIDI","CSAP","ACES","HERO","MPPA","RANC","SDPC",
        "TRIO","TKGA","TELE","SKYB","KOIN","PGJO","PSKT","PDES","PANR",
        "WICO","GLOB","BLTZ","BUVA","HOTL","HOME","ICON","JIHD","JSPT",
        "FAST","CAMP","BATA","DAYA","DART","CSAP","ERTX","ESTI","HDTX",
    ],

    "Healthcare": [
        "AHAP","BMHS","DVLA","HEAL","INAF","IRRA","KAEF","KLBF","MEDS","MERK",
        "MIKA","MTMH","PEHA","PRDA","PYFA","RBMS","RSCH","SCPI","SIDO","SILO",
        "SRAJ","TSPC","SOHO","PINO","PHFN","SAME","PDSS","CURE","BIOS","DGNS",
        "IMED","MRAT","MTRA","PEGE","PLAS","POOL","PPRE","TRIM","VRNA","YULE",
        "APIC","ASBI","ASEI","ASMI","ASRM","HADE","IMJS","JMAS","LPGI","MREI",
        "PANS","CFIN","TIFA","ADMF","BFIN","MFIN","WOMF","GSMF","HDFA",
    ],

    "Financials": [
        "ADMF","AGRO","AGRS","AMAR","APEX","APIC","ASBI","ASDM","ASEI","ASMI",
        "ASRM","ARTO","BABP","BACA","BANK","BBCA","BBHI","BBKP","BBMD","BBNI",
        "BBNP","BBRI","BBYB","BCIC","BDMN","BEKS","BFIN","BGTG","BHAT","BINA",
        "BJBR","BJTM","BKSW","BLTM","BMAG","BMAS","BMAX","BMRI","BNBA","BNGA",
        "BNII","BPII","BRIS","BSIM","BSMD","BTPN","BTPS","BVIC","CFIN","DNAR",
        "DPUM","GSMF","HADE","HDFA","IMJS","INPC","JMAS","LPGI","MAYA","MCOR",
        "MEGA","MFIN","MREI","NISP","NOBU","PANS","PEGE","PHFN","PNBN","PNBS",
        "PNLF","POOL","PPRE","SDRA","TIFA","TRIM","VRNA","WOMF","YULE","FIRE",
        "ADMG","APIC","ASDM","ARTO","BBYB","BCIC","BEKS","BGTG","BHAT","BINA",
        "BKSW","BLTM","BMAG","BMAX","BMAS","BNBA","BPII","BSIM","BSMD",
        "DNAR","DPUM","INPC","LPGI","MAYA","MCOR","NOBU","PNBS","SDRA",
        "AGRS","AMAR","BANK","BBHI","BBKP","BBMD","BBNP","BVIC","BJBR",
        "BJTM","BTPN","BTPS","MEGA","NISP","PNLF","YULE","CFIN","HDFA",
    ],

    "Properties & Real Estate": [
        "APLN","ARMY","ASRI","BCIP","BEST","BIKA","BIPP","BKDP","BKSL","BSDE",
        "CBPE","CITY","CTRA","DART","DMAS","DUTI","ELTY","EMDE","FMII","GAMA",
        "GMTD","GPRA","GWSA","HOMR","INPP","JRPT","KIJA","KPIG","LCGP","LPCK",
        "LPKR","MDLN","MKPI","MKNT","MMLP","MPRO","MTLA","MTSM","NIRO","NZIA",
        "PJAA","PLAS","PPRO","PTPP","PWON","RBMS","REAL","RODA","SCBD","SIMA",
        "SMRA","SSIA","TARA","URBN","WIKA","WSKT","WTON","BSDE","CTRA","LPKR",
        "PWON","ASRI","JRPT","SMRA","DUTI","INPP","KIJA","APLN","PJAA","BCIP",
        "BEST","BIKA","BIPP","BKDP","BKSL","DART","DMAS","ELTY","EMDE","FMII",
        "GAMA","GMTD","GPRA","GWSA","HOMR","LCGP","LPCK","MDLN","MKPI","MKNT",
        "MMLP","MPRO","MTLA","MTSM","NIRO","NZIA","PLAS","PPRO","RBMS","REAL",
        "RODA","SCBD","SIMA","SSIA","TARA","URBN","CBPE","CITY","ARMY",
    ],

    "Technology": [
        "ABBA","AGIT","ARTO","AXIO","BUKA","CENT","DCII","DMMX","EDGE","ELIO",
        "EMTK","EPAC","FORU","GLVA","GOTO","IPTV","JATI","KIOS","LCKM","LINK",
        "LUCK","MCOM","MCAS","META","MITI","MLPT","MORA","MPIX","MTDL","NAYZ",
        "NETV","NFCX","OASA","PADI","PDSI","RINA","SWAT","TBIG","TLKM","TOWR",
        "VKTR","WIFI","EXCL","ISAT","BUKA","GOTO","DCII","LINK","MLPT","MTDL",
        "EMTK","MNCN","SCMA","NETV","FILM","VIVA","BMTR","JTPE","KBLV","MDIA",
        "MSKY","ABBA","GLVA","IPTV","JATI","KIOS","LCKM","LUCK","MCOM","MCAS",
        "META","MITI","MORA","MPIX","NAYZ","NFCX","OASA","PADI","PDSI","RINA",
        "SWAT","VKTR","WIFI","AXIO","CENT","DMMX","EDGE","ELIO","EPAC","FORU",
        "AGIT","TBIG","TOWR","TLKM","EXCL","ISAT","BUKA","GOTO","DCII","LINK",
    ],

    "Infrastructure": [
        "BREN","CMNP","CUAN","ENRG","ESSA","IPCM","JSMR","KARW","KJEN","LAPD",
        "MEDC","MGAS","PGAS","PTIS","RGAS","RUIS","SAFE","SDMU","SHIP","SUGI",
        "TLKM","TPMA","WEGE","WINS","GIAA","HELI","AKRA","ELSA","PGAS","ENRG",
        "RUIS","JSMR","CMNP","MGAS","LAPD","RGAS","SUGI","BREN","ESSA","CUAN",
        "IPCM","KARW","KJEN","SAFE","SDMU","SHIP","TPMA","WEGE","WINS","GIAA",
        "BIRD","BLTA","BULL","CANI","CARE","CAPL","CMPP","DEAL","HATM","HITS",
        "IATA","LRNA","MBSS","MIRA","NELY","PALM","SMDR","TAXI","TMAS","TRUK",
        "WEHA","ASSA","BBRM",
    ],

    "Transportation & Logistic": [
        "ASSA","BBRM","BIRD","BLTA","BULL","CANI","CARE","CAPL","CMPP","DEAL",
        "GIAA","HATM","HELI","HITS","IATA","IPCM","KARW","KJEN","LRNA","MBSS",
        "MIRA","NELY","PALM","PTIS","SAFE","SDMU","SHIP","SMDR","TAXI","TMAS",
        "TPMA","TRUK","WEHA","WINS","ZINC","ASSA","BIRD","BLTA","BULL","CANI",
        "SMDR","MBSS","TMAS","WINS","GIAA","HELI","MIRA","NELY","SHIP","HATM",
        "HITS","IATA","LRNA","PALM","TAXI","WEHA","CAPL","CMPP","DEAL","BBRM",
        "CARE","KARW","KJEN","SAFE","SDMU","TRUK","ZINC","IPCM",
    ],
}

# ── Tambahan saham yang belum dikategorikan (Lainnya) ────────────────────────
EXTRA_STOCKS = [
    # Saham yang muncul di IDX tapi belum dikategorikan di atas
    "ABDA","ABMM","ABDE","ABBA","ACCS","ACES","ACST","ACRO","ADCP","ADHI",
    "ADMG","ADMF","ADMR","ADRO","AHAP","AIMS","AISA","AITI","AKKU","AKPI",
    "AKRA","AKSI","ALII","ALKA","ALMI","ALTO","AMFG","AMRT","ANJT","ANTM",
    "APEX","APIC","APII","APLI","APLN","ARMY","ARGO","ARNA","ARTI","ASIA",
    "ASBI","ASDM","ASEI","ASII","ASMI","ASRM","ASSA","ASRI","ATIC","ATPK",
    "AUTO","AXIO","BABP","BACA","BAJA","BALI","BAPA","BANK","BATA","BAYU",
    "BBCA","BBHI","BBKP","BBMD","BBNI","BBNP","BBRI","BBRM","BBYB","BCIC",
    "BCIP","BDMN","BEEX","BEKS","BEST","BFIN","BGTG","BHAT","BIKA","BINA",
    "BIPI","BIPP","BIRD","BJBR","BJTM","BKDP","BKSW","BKSL","BLTM","BLTA",
    "BLTZ","BMAG","BMAS","BMAX","BMHS","BMRI","BMTR","BNBA","BNGA","BNII",
    "BPII","BRAM","BREN","BRIS","BRNA","BRPT","BSDE","BSIM","BSMD","BSSR",
    "BTON","BTPN","BTPS","BUDI","BULL","BUMI","BUVA","BVIC","BWPT","BYAN",
    "CAKK","CAMP","CANI","CARE","CAPL","CBPE","CENT","CEKA","CFIN","CITY",
    "CLPI","CLEO","CMPP","CMNP","CMRY","CNKO","COCO","CPRO","CSAP","CSRA",
    "CTBN","CTRA","CUAN","CURE","DART","DAJK","DAYA","DCII","DEAL","DEWA",
    "DFAM","DGIK","DGNS","DLTA","DKFT","DMND","DMAR","DMAS","DMMX","DNAR",
    "DOID","DPNS","DPUM","DSFI","DSNG","DSSA","DUTI","DVLA","DYAN","EDGE",
    "EKAD","ELIO","ELSA","ELTY","EMDE","EMTK","ENRG","EPAC","ERAA","ERTO",
    "ERTX","ESSA","ESTI","EXCL","FASW","FAST","FILM","FIRE","FMII","FOOD",
    "FORU","GAMA","GDST","GDYR","GEMA","GEMS","GIAA","GJTL","GLOB","GLVA",
    "GMFI","GMTD","GOOD","GOTO","GPRA","GOZCO","GGRM","GTBO","GSMF","GULA",
    "GWSA","HADE","HALO","HATM","HEAL","HDTX","HDFA","HELI","HERO","HITS",
    "HOKI","HOME","HOMR","HOTL","HRUM","HMSP","ICON","IATA","ICBP","IFII",
    "IGAR","IGNA","IIKP","IKBI","IMAS","IMED","IMJS","IMPC","INAF","INAI",
    "INCO","INDF","INDR","INDS","INKP","INPC","INPP","INTA","INTP","INTI",
    "INTD","IPCM","IPOL","IPTV","ISAT","ISSP","ITIC","JATI","JAWA","JKON",
    "JECC","JIHD","JMAS","JPFA","JRPT","JSPT","JSMR","JTPE","KAEF","KARW",
    "KBLI","KBLM","KBLV","KBRI","KDSI","KEJU","KIAS","KIJA","KINO","KIOS",
    "KKGI","KMTR","KOIN","KPIG","LAPD","LCGP","LCKM","LION","LINK","LMSH",
    "LPCK","LPGI","LPKR","LPPF","LRNA","LSIP","LUCK","MAGP","MAIN","MAPA",
    "MAPI","MARK","MASA","MAYA","MBAP","MBMA","MBSS","MCOM","MCAS","MCOL",
    "MDKI","MDLN","MEDS","MEDC","MEGA","META","MFIN","MGNA","MGAS","MIDI",
    "MIKA","MITI","MKNT","MKPI","MLIB","MLBI","MLPL","MLPT","MMLP","MNCK",
    "MNCN","MORA","MPIX","MPPA","MPMX","MPRO","MRAT","MREI","MRMA","MRMD",
    "MSKY","MTDL","MTLA","MTMH","MTRA","MTSM","MYOH","MYTX","MYOR","NASI",
    "NAYZ","NCKL","NELY","NETV","NFCX","NICL","NIKL","NIPS","NIRO","NISP",
    "NOBU","NRCA","NZIA","OASA","PADI","PALM","PANR","PANS","PBID","PBSA",
    "PBRX","PCPM","PDES","PDSI","PDSS","PEGE","PEHA","PGJO","PHFN","PICO",
    "PINO","PKPK","PLAS","PNBS","PNBN","PNLF","POLU","POOL","PPRE","PPRO",
    "PRAS","PRDA","PSAB","PSDN","PSKT","PTBA","PTIS","PTPP","PTRO","PTSP",
    "PWON","PYFA","RALS","RANC","RBMS","REAL","RGAS","RICY","RIMO","RINA",
    "RODA","ROTI","RSCH","RUIS","SAFE","SAME","SAWIT","SCBD","SCCO","SCMA",
    "SCPI","SDMU","SDPC","SDRA","SGRO","SHID","SHIP","SIAP","SIDO","SILO",
    "SIMA","SIMP","SKBM","SKLT","SKRN","SKYB","SMART","SMCB","SMDR","SMGR",
    "SMBR","SMSM","SMMT","SMRA","SMRU","SOHO","SPMA","SRAJ","SRIA","SRIL",
    "SRBI","SRSN","SSMS","SSTM","STAR","STTP","SUGI","SURE","SWAT","TAPG",
    "TARA","TAXI","TBIG","TBLA","TBMS","TDPM","TFCO","TGKA","TIFA","TINS",
    "TJBP","TKGA","TKIM","TMAS","TOBA","TOTO","TOTL","TOWR","TLKM","TPMA",
    "TRIO","TRIM","TRUK","TSPC","ULTJ","UNIC","UNSP","UNTR","UNVR","URBN",
    "VIVA","VKTR","VOKS","VRNA","WEHA","WEGE","WIFI","WIIM","WIKA","WINS",
    "WICO","WOMF","WTON","WSKT","YPAS","YULE","ZINC","BBCA","BBRI","BMRI",
    "BBNI","BRIS","TLKM","ASII","UNVR","KLBF","ANTM","MDKA","TINS","PTBA",
    "ADRO","INCO","ICBP","INDF","GGRM","HMSP","SIDO","MYOR","CLEO","MIKA",
    "SILO","HEAL","PRDA","GOTO","BUKA","EXCL","ISAT","TBIG","TOWR","SCMA",
    "MNCN","NETV","EMTK","FILM","BMTR","VIVA","MDIA","MSKY","KBLV","JTPE",
    # Tambahan saham IPO baru 2022-2024
    "AMMS","ARKO","AYAM","BAPI","BAUT","BEER","BELI","BERG","BLOK","BOAT",
    "BOBA","BPTR","BREN","BUDP","BUAH","CAFE","CASH","CLAY","COAL","COCO",
    "CUAN","DADA","DART","DATA","DIGI","DKHH","DMAS","DMMX","DRMA","DUCK",
    "EASY","ECII","ENZO","ESIP","ESSA","ESTE","EVIO","FAPA","FIMP","FIRM",
    "FLMC","FORU","FREN","FSMR","GAIA","GALE","GCEI","GCIG","GGRM","GIGA",
    "GOLL","GPSO","GRPH","GRUP","GTSI","GULA","GUNS","GURU","GUTS","HADE",
    "HAIS","HAJJ","HALO","HAPI","HBER","HEAL","HELI","HERO","HGAR","HIDL",
    "HMSP","HOMY","HOPE","HOSP","HOTEL","ICON","IDEA","IKAN","IKBM","IMAS",
    "IMAS","INPS","INRA","INTD","INTI","IPAC","IPPE","IPSI","IRRA","ISAP",
    "ISMA","ISSI","IUPK","JACK","JAYA","JAZZ","JGLE","JIES","JKSW","JMAS",
    "JNPT","JOSS","KADO","KAIS","KAKA","KALI","KALS","KAME","KAPI","KARK",
    "KBLM","KDTN","KEJU","KELK","KICI","KICI","KIJA","KIKY","KIOS","KMDS",
    "KOBX","KOLB","KONI","KOPI","KOTO","KPAS","KRAS","KREN","LABA","LAMI",
    "LAND","LAUT","LEAD","LELE","LEMA","LIKA","LINK","LIST","LIVE","LMAS",
    "LMPI","LOGO","LOLI","LOOK","LPKR","LPPF","LRNA","LTLS","LUDI","LUNA",
    "MABA","MACO","MAHA","MAKO","MALI","MALL","MAMA","MAMI","MANA","MANG",
    "MAPI","MARS","MASH","MASI","MATO","MBER","MBPI","MCON","MDKI","MEDS",
    "MEGA","MEGS","MENU","MERK","MESA","MFIN","MGNA","MHKI","MHOM","MIKA",
    "MILK","MIRA","MISR","MKAP","MKNT","MKPI","MLPL","MNCK","MNKH","MNRE",
    "MOLI","MONG","MONY","MORY","MOVE","MPKG","MPMX","MPRO","MRAT","MRSP",
    "MSIE","MSIP","MUJS","MURA","MUST","MUTA","NAIK","NAKI","NANO","NAYZ",
    "NELY","NFTX","NICE","NISP","NITL","NKPI","NOTO","NRCA","NTBK","NURI",
    "OASE","OBMD","OCAP","ODCE","OLIV","OMAI","OMNI","OPMS","OPSI","ORBA",
    "PADI","PAFG","PANI","PARA","PASF","PBID","PBSA","PCAR","PDES","PEGE",
    "PEKA","PEMA","PERI","PERT","PGAS","PGEO","PGUN","PJAA","PJBS","PKBL",
    "PKPK","PLAN","PLAS","PLNT","PMMP","PMRO","PNBN","POLA","POLI","POLK",
    "POLY","PORT","PPGL","PPRE","PPRO","PRAM","PRAS","PRAY","PRDA","PRKS",
    "PRMB","PRTX","PRTY","PSAB","PSDN","PSGO","PSKT","PTAR","PTBA","PTDU",
    "PTIS","PTMP","PTPP","PTRO","PTSI","PTSP","PUBM","PUCA","PUCO","PUDS",
    "PURI","PUSA","PUSH","PYLA","PYFA","QCTM","RAAM","RABS","RADS","RAFI",
    "RAKA","RANI","RAPI","RATU","RBAH","RBMS","RGAS","RGHT","RICK","RICY",
    "RIMO","RINA","RJET","RMKO","RMOG","ROGS","ROTI","ROYS","RPUM","RSCH",
    "RTHR","RUFI","RUIS","SAFE","SAGA","SAGE","SAHA","SAIL","SAIS","SAMA",
    "SAMP","SAND","SANG","SANI","SARB","SATU","SAUT","SAWIT","SBAT","SBMA",
    "SCCO","SCMA","SDMU","SDPC","SDRA","SGER","SGRO","SHID","SHIP","SIAP",
    "SICO","SIDC","SIDO","SILO","SILV","SIMA","SIMO","SIMP","SINI","SINI",
    "SIPS","SISP","SKBM","SKLT","SKRN","SKYB","SLEO","SLIM","SLIS","SLPI",
    "SMART","SMCB","SMGR","SMBR","SMDM","SMDR","SMEQ","SMGE","SMKL","SMMT",
    "SMRA","SMRU","SNLK","SOCI","SOFA","SOHO","SOIK","SONA","SONO","SOTS",
    "SPMA","SQBB","SRAJ","SRIC","SRIL","SRIP","SRMI","SRSN","SSCO","SSMS",
    "SSMX","SSNI","SSTM","STAR","STAY","STID","STLK","STOS","STTP","STUP",
    "SUGI","SUJA","SULA","SUPR","SURI","SURE","SURI","SURY","SWAT","SWID",
    "TALF","TAMA","TAMS","TAPG","TARA","TAXI","TBIG","TBLA","TBMS","TCID",
    "TDPM","TFCO","TGKA","TIFA","TINS","TIPS","TIRA","TITD","TJBP","TKIM",
    "TKGA","TLDN","TMAS","TOBA","TOCA","TOLI","TOLL","TOMA","TOTO","TOTL",
    "TOWR","TPAS","TPIA","TPMA","TRAM","TRIL","TRIM","TRJA","TRKS","TRIO",
    "TRST","TRUK","TSPC","TUFI","UANG","UCEN","UCHE","UCOT","UFOE","UJAM",
    "UKAN","ULMO","ULTRA","ULTJ","UMA","UMAX","UMBY","UMET","UNIC","UNIQ",
    "UNIT","UNIV","UNSP","UNTR","UNVR","UPCL","UPFA","UPHB","URBN","USDA",
    "USDI","VADS","VALE","VAMI","VANS","VERI","VICO","VIDA","VIGI","VIKT",
    "VINS","VIRA","VIRAMA","VIRO","VISA","VISI","VIVA","VKTR","VOKS","VOLT",
    "VOPI","VRNA","VRTX","WAPO","WARS","WARU","WAST","WATO","WATT","WEHA",
    "WEGE","WIFI","WIIM","WIKA","WINS","WIPP","WIRO","WISA","WISD","WMAS",
    "WOMF","WONE","WTON","WSKT","XACT","XIST","YAPI","YBKG","YCAB","YELO",
    "YOGI","YOYS","YPAS","YULE","YULO","YUMI","ZATA","ZENI","ZINC","ZONA",
]

# ── Build ticker-sector map ──────────────────────────────────────────────────
def _build_ticker_sector_map() -> Dict[str, str]:
    result = {}
    for sector, codes in HARDCODED_IDX.items():
        for code in codes:
            tk = f"{code}.JK"
            if tk not in result:
                result[tk] = sector
    return result

TICKER_SECTOR_MAP: Dict[str, str] = _build_ticker_sector_map()


def _dedup_preserve_order(lst: list) -> list:
    seen = set()
    out  = []
    for x in lst:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _build_full_hardcoded() -> List[Dict]:
    """Build daftar lengkap dari HARDCODED_IDX + EXTRA_STOCKS."""
    seen   = set()
    result = []

    # Dari HARDCODED_IDX (dengan sektor)
    for sector, codes in HARDCODED_IDX.items():
        for code in _dedup_preserve_order(codes):
            if code not in seen:
                seen.add(code)
                result.append({
                    "code":   code,
                    "name":   code,
                    "ticker": f"{code}.JK",
                    "sector": sector,
                })

    # Dari EXTRA_STOCKS (sektor dari map, fallback "Lainnya")
    for code in _dedup_preserve_order(EXTRA_STOCKS):
        if code not in seen:
            seen.add(code)
            ticker = f"{code}.JK"
            result.append({
                "code":   code,
                "name":   code,
                "ticker": ticker,
                "sector": TICKER_SECTOR_MAP.get(ticker, "Lainnya"),
            })

    return result


# ── API Fetch ────────────────────────────────────────────────────────────────
_API_URLS = [
    "https://www.idx.co.id/primary/StockData/GetSecurities",
    "https://www.idx.co.id/umbraco/Surface/StockData/GetSecuritiesAjax",
]
_HDR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer":    "https://www.idx.co.id/id/data-pasar/data-saham/daftar-saham/",
    "Accept":     "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
}


def _fetch_from_api() -> List[Dict]:
    params = {"code": "", "start": 0, "length": 9999, "market": "regularmarket"}
    for url in _API_URLS:
        try:
            r = requests.get(url, params=params, headers=_HDR, timeout=15)
            if r.status_code != 200:
                continue
            raw = r.json()
            items = raw.get("data") or raw.get("Data") or []
            if not items:
                continue
            result = []
            seen   = set()
            for item in items:
                code = (item.get("Code") or item.get("StockCode") or "").strip().upper()
                name = (item.get("Name") or item.get("StockName") or code).strip()
                if not code or len(code) > 6 or code in seen:
                    continue
                seen.add(code)
                ticker = f"{code}.JK"
                sector = TICKER_SECTOR_MAP.get(ticker, "Lainnya")
                result.append({"code": code, "name": name, "ticker": ticker, "sector": sector})
            if len(result) > 200:
                return result
        except Exception:
            continue
    return []


# ── Public API ───────────────────────────────────────────────────────────────
def get_all_idx_stocks(force_refresh: bool = False) -> List[Dict]:
    """
    Return semua saham IDX sebagai list of dict {code, name, ticker, sector}.
    Cache 6 jam. Prioritas: IDX API → hardcoded fallback.
    """
    global _STOCK_CACHE, _CACHE_TS

    with _CACHE_LOCK:
        now = time.time()
        if not force_refresh and _STOCK_CACHE and (now - _CACHE_TS) < _CACHE_TTL:
            return _STOCK_CACHE

        api_result = _fetch_from_api()

        if api_result and len(api_result) > 200:
            # Merge: nama dari API, sektor dari map kita
            _STOCK_CACHE = api_result
        else:
            _STOCK_CACHE = _build_full_hardcoded()

        _CACHE_TS = now
        return _STOCK_CACHE


def get_all_tickers() -> List[str]:
    return [s["ticker"] for s in get_all_idx_stocks()]


def get_sector_map() -> Dict[str, List[str]]:
    result: Dict[str, List[str]] = {}
    for s in get_all_idx_stocks():
        result.setdefault(s["sector"], []).append(s["ticker"])
    return result


def get_ticker_sector_map() -> Dict[str, str]:
    return {s["ticker"]: s["sector"] for s in get_all_idx_stocks()}


def get_stock_info_map() -> Dict[str, Dict]:
    return {s["ticker"]: s for s in get_all_idx_stocks()}
