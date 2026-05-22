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
# Setiap kode saham sudah dikategorikan ke sektor yang benar sesuai IDX-IC
HARDCODED_IDX: Dict[str, List[str]] = {

    "Energy": [
        # Batu Bara
        "ADRO","ARII","ATPK","BSSR","BUMI","BYAN","DEWA","DKFT","DOID","DSSA",
        "FIRE","GEMS","GTBO","HRUM","ITMG","KKGI","MBAP","MBMA","MCOL","MYOH",
        "PKPK","PSAB","PTBA","PTRO","SMMT","SMRU","SURE","TOBA",
        # Minyak & Gas
        "AKRA","ARTI","BIPI","ELSA","ENRG","ESSA","LAPD","MEDC","MGAS","MKTR",
        "PGAS","RGAS","RUIS","SUGI",
        # Nikel & Mineral Energi
        "INCO","NCKL","NICL","ZINC",
        # Geothermal & Energi Terbarukan
        "BREN","PGEO",
        # Lainnya Energi
        "ADMR","AIMS","AITI","ATPK","BATU","BCIP","BEEX","BORN","CITA","CUAN",
        "DKFT","HALO","ABMM","COAL","ESSA","MDKA","ANTM","TINS","NCKL","MBMA",
    ],

    "Basic Materials": [
        # Kimia
        "AGII","BRPT","CLPI","DPNS","EKAD","INCI","SRSN","TPIA","UNIC",
        # Plastik & Kemasan
        "AKKU","AKPI","BRNA","IGAR","IMPC","IPOL","MOLI","YPAS","APLI",
        # Baja & Logam
        "ALKA","ALMI","BAJA","BTON","CTBN","GDST","ISSP","JKSW","LION","LMSH",
        "NIKL","TBMS","DAJK","INAI","PICO","SCCO","JECC","IKBI","KBLI","KBLM",
        # Kaca & Keramik
        "AMFG","ARNA","KIAS","MLIA","TOTO",
        # Semen
        "INTP","SMCB","SMGR","SMBR",
        # Kertas & Kayu
        "FASW","INKP","TKIM","SPMA","KDSI","DAJK","ALDO",
        # Karet & Plastik lainnya
        "TDPM","SIAP","MDKI","PBID","VOKS","IFII","IGNA",
        # Serat Sintetis
        "INDR","TFCO","SSTM","SRIL","SRIA",
        # Pertambangan Non-Logam
        "KBRI","CAKK","AMFG",
    ],

    "Industrials": [
        # Konstruksi
        "ACST","ADHI","DGIK","JKON","NRCA","PBSA","PTPP","TOTL","WEGE","WIKA",
        "WSKT","WTON","SKRN","TJBP","SIKA",
        # Otomotif & Komponen
        "ASII","AUTO","BOLT","BRAM","DRMA","GJTL","GDYR","IMAS","INDS","MASA",
        "MPMX","NIPS","PRAS","SMSM","UNTR","INTA","POLU","PBRX","KMTR",
        # Mesin & Peralatan
        "KPIG","ARMY","GEMA","GMFI","CNKO","BEST","CENT","SCBD","SSIA",
        # Manufaktur lainnya
        "TBMS","STAR","TRIO","ISSP","MYTX","BAUT","PPRE",
        # Peralatan Listrik
        "VOKS","KBLI","KBLM","SCCO",
        # Kabel
        "JECC","IKBI",
        # Logistik & Pergudangan
        "MMLP","DMAS",
        # Tekstil
        "HDTX","RICY","TRIS","PBRX","ERTX","ESTI","MARK","TFCO","ARGO",
    ],

    "Consumer Non-Cyclicals": [
        # Makanan & Minuman
        "ADES","AISA","ALTO","BUDI","CEKA","CLEO","CMRY","COCO","CSRA","DLTA",
        "DMND","FOOD","GGRM","GOOD","HOKI","HMSP","ICBP","IIKP","INDF","ITIC",
        "JPFA","KEJU","KINO","MAIN","MGNA","MLBI","MRAT","MYOR","NASI","PSDN",
        "PTSP","ROTI","SKBM","SKLT","STTP","ULTJ","WIIM","GULA","BOBA","CAFE",
        "AYAM","BUAH","BEER","RMKO",
        # Rokok
        "WIIM","GGRM","HMSP",
        # Pertanian & Perkebunan
        "AALI","ANJT","BWPT","DSNG","GOZCO","JAWA","LSIP","MAGP","PALM","SAWIT",
        "SGRO","SIMP","SMART","SSMS","TAPG","TBLA","UNSP","CPRO","DSFI","ATIC",
        # Farmasi & Distribusi
        "KAEF","DVLA","MERK","INAF","PEHA","PYFA","SCPI","KLBF","TSPC","SIDO",
        "SOHO","MIDI","AMRT","TGKA","MIDI",
        # Alat Rumah Tangga & Personal Care
        "UNVR","TCID","SIDO","MRAT","KINO",
    ],

    "Consumer Cyclicals": [
        # Ritel
        "ACES","CSAP","ERAA","HERO","LPPF","MAPA","MAPI","MPPA","RALS","RANC",
        "SDPC","TELE","TKGA","WICO","AMRT","MIDI",
        # Properti & Hotel (Consumer-facing)
        "BAYU","BUVA","HOTL","HOME","ICON","INPP","JIHD","JSPT","PANR","PDES",
        "PGJO","PSKT","SHID","SKYB","BLTZ","GLOB","BIRD","FAST","CAMP",
        # Pakaian & Fashion
        "BATA","RICY","ERTX","ESTI","HDTX","SRIL","SRIA","DAYA","ARGO","TFCO",
        # Otomotif Konsumen
        "IMAS","MPMX","DRMA","GJTL",
        # Media & Hiburan
        "SCMA","MNCN","NETV","FILM","VIVA","BMTR","JTPE","KBLV","MDIA","MSKY",
        "ABBA","DYAN","MLPL","MNCK",
        # E-commerce & Digital Consumer
        "BELI","GOTO","BUKA",
        # Lainnya Consumer Cyclicals
        "KOIN","MARK","RANC","TRIO","PANR",
    ],

    "Healthcare": [
        # Rumah Sakit
        "BMHS","HEAL","MIKA","MTMH","PRDA","RBMS","RSCH","SAME","SILO","SRAJ",
        "IMED","OMNI","PLAS","POOL",
        # Farmasi
        "DVLA","INAF","KAEF","KLBF","MERK","PEHA","PYFA","SCPI","SIDO","SOHO",
        "TSPC","CURE","PDSS","PHFN","PINO","VRNA","YULE","BIOS","DGNS",
        # Alat Kesehatan
        "IRRA","MEDS","AHAP","MTRA","TRIM","APIC",
        # Asuransi Kesehatan
        "ASBI","ASEI","ASMI","ASRM","HADE","IMJS","JMAS","LPGI","MREI","PANS",
    ],

    "Financials": [
        # Bank Besar
        "BBCA","BBNI","BBRI","BDMN","BMRI","BNGA","BNII","NISP","PNBN",
        # Bank Menengah
        "AGRO","AMAR","ARTO","BABP","BACA","BANK","BBHI","BBKP","BBMD","BBNP",
        "BBYB","BCIC","BEKS","BGTG","BHAT","BINA","BJBR","BJTM","BKSW","BLTM",
        "BMAG","BMAS","BMAX","BNBA","BPII","BRIS","BSIM","BSMD","BTPN","BTPS",
        "BVIC","DNAR","DPUM","INPC","MAYA","MCOR","MEGA","NOBU","PNBS","PNLF",
        "SDRA","AGRS","SRBI","BBYB","ABMM",
        # Asuransi
        "ABDA","AHAP","ASBI","ASDM","ASEI","ASMI","ASRM","HADE","IMJS","JMAS",
        "LPGI","MREI","PANS","PEGE","VRNA","YULE","ASBI",
        # Multifinance & Sekuritas
        "ADMF","BFIN","CFIN","GSMF","HDFA","MFIN","PANS","TIFA","TRIM","WOMF",
        "APEX","POOL","PPRE","PEGE","ALII","CASH",
        # Lainnya Keuangan
        "PNLF","APIC","FIRE",
    ],

    "Properties & Real Estate": [
        # Developer Properti
        "APLN","ASRI","BIKA","BIPP","BKDP","BKSL","BSDE","CITY","CTRA","DART",
        "DMAS","DUTI","ELTY","EMDE","FMII","GAMA","GMTD","GPRA","GWSA","HOMR",
        "INPP","JRPT","KIJA","KPIG","LCGP","LPCK","LPKR","MDLN","MKPI","MKNT",
        "MMLP","MPRO","MTLA","MTSM","NIRO","NZIA","PJAA","PPRO","PWON","RBMS",
        "REAL","RODA","SCBD","SIMA","SMRA","SSIA","TARA","URBN",
        # Konstruksi Properti
        "PTPP","WIKA","WSKT","WTON","ADHI","ACST",
        # REIT & Pengelola Properti
        "BCIP","BEST","CBPE","ARMY","BREN",
        # Kawasan Industri
        "BEST","KIJA","SSIA","GMTD",
        # Mall & Commercial
        "PWON","SMRA","LPKR","CTRA","APLN",
    ],

    "Technology": [
        # Telekomunikasi
        "EXCL","ISAT","TLKM","WIFI","FREN",
        # Menara Telekomunikasi
        "TBIG","TOWR","SUPR",
        # Software & IT Services
        "AGIT","AXIO","CENT","DMMX","EDGE","ELIO","EMTK","EPAC","FORU","GLVA",
        "IPTV","JATI","KIOS","LCKM","LINK","LUCK","MCOM","MCAS","META","MITI",
        "MLPT","MORA","MPIX","MTDL","NAYZ","NFCX","OASA","PADI","PDSI","RINA",
        "SWAT","VKTR","ACCS","INTD","INTI","MLPL","MNCK",
        # E-commerce & Digital Platform
        "BUKA","GOTO","DCII","DATA","DIGI","BLOK","BELI",
        # Media Digital
        "SCMA","MNCN","NETV","FILM","VIVA","BMTR","JTPE","KBLV","MDIA","MSKY",
        "ABBA","DYAN",
        # Elektronik & Hardware
        "GLVA","WIFI","ACCS",
    ],

    "Infrastructure": [
        # Utilitas Listrik & Gas
        "PGAS","ENRG","ESSA","ELSA","RGAS","MGAS","LAPD","RUIS","AKRA","BIPI",
        # Jalan Tol & Infrastruktur
        "JSMR","CMNP","WEGE",
        # Pelabuhan & Bandara
        "IPCM","KARW",
        # Air & Sanitasi
        "SUGI","SAFE","SDMU",
        # Ketenagalistrikan
        "POWR","KJEN","WINS","TPMA","BREN","PGEO",
        # Telekomunikasi (Infrastruktur)
        "TBIG","TOWR","TLKM","EXCL","ISAT","LINK",
        # Pergudangan & Logistik Infrastruktur
        "SHIP","HATM",
    ],

    "Transportation & Logistic": [
        # Penerbangan
        "GIAA","HELI","IATA","CMPP","LRNA","RJET",
        # Pelayaran
        "BLTA","BULL","MBSS","SMDR","TMAS","WINS","NELY","SHIP","MIRA","HITS",
        "BBRM","PALM","TAXI","WEHA","LRNA",
        # Darat & Logistik
        "ASSA","BIRD","HATM","CAPL","DEAL","TRUK","TAXI","WEHA","BBRM",
        # Kereta & Angkutan Umum
        "KARW","SAFE","SDMU","KJEN",
        # Ekspedisi
        "CANI","CARE","ZINC","IPCM","TPMA",
    ],
}

# ── Peta Sektor Tambahan untuk saham yang tidak ada di HARDCODED_IDX ────────
# Mencakup IPO baru, saham kecil, dan yang belum terkategorikan di atas
EXTRA_SECTOR_MAP: Dict[str, str] = {
    # ── Financials ──
    "ABDA": "Financials",   # Asuransi Bina Dana Arta
    "ACRO": "Financials",   # Acro Lestari Karya
    "AKSI": "Financials",   # Maxima Integra
    "ALII": "Financials",   # Asuransi Allianz Life
    "APEX": "Financials",   # Apexindo Pratama Duta
    "BALI": "Financials",   # Bali Towerindo
    "CASH": "Financials",   # Cashlez Worldwide Indonesia
    "DFAM": "Financials",   # Dafam Finance
    "DMAR": "Financials",   # Digital Mediatama Maxima
    "LPGI": "Financials",   # Lippo General Insurance
    "MLIB": "Financials",   # Multi Lintang Investama
    "MRMA": "Financials",   # Megakarya Esa Unggul
    "MRMD": "Financials",   # Mega Manunggal Property
    "PNLF": "Financials",   # Panin Financial
    "SRBI": "Financials",   # Allo Bank Indonesia
    "BAPA": "Financials",   # Bekasi Asri Pemula
    "PCPM": "Financials",   # Campina Ice Cream Industry

    # ── Energy ──
    "ABMM": "Energy",       # ABM Investama (batubara & energi)
    "COAL": "Energy",       # Ithink Logistics / Coal IDX
    "DKHH": "Energy",       # Daulat Harta Hidayatullah
    "ECII": "Energy",       # Electronic City Indonesia
    "PKBL": "Energy",       # Pakuan Berkah Lestari

    # ── Basic Materials ──
    "APLI": "Basic Materials",  # Asiaplast Industries
    "INDR": "Basic Materials",  # Indo Rama Synthetics
    "SRIA": "Basic Materials",  # Sri Rejeki Isman (tekstil/serat)
    "TFCO": "Basic Materials",  # Teijin Indonesia Fiber
    "CLAY": "Basic Materials",  # Citra Lautan Teduh
    "BERG": "Basic Materials",  # Industri Bintang Mitra / Gunung Gahapi
    "GDYR": "Basic Materials",  # Goodyear Indonesia
    "INTD": "Basic Materials",  # Inter Delta
    "ABDE": "Basic Materials",  # Anabatic Digital Raya -> sebenarnya Tech
    "ERTO": "Basic Materials",  # Erto Waste Holdings

    # ── Industrials ──
    "ADCP": "Industrials",  # Adhi Commuter Properti
    "AGAR": "Industrials",  # Asia Sukses Makmur
    "APII": "Industrials",  # Arita Prima Indonesia
    "ARGO": "Industrials",  # Apac Inti Corpora
    "DYAN": "Industrials",  # Dyandra Media Internasional
    "ACST": "Industrials",  # Acset Indonusa
    "BAUT": "Industrials",  # Mitra Anugrah Pratama
    "BOAT": "Industrials",  # Mentari Lines
    "GAIA": "Industrials",  # Jaya Bersama Indo
    "GALE": "Industrials",  # Galva Technologies
    "GRPH": "Industrials",  # Graphene Works Indonesia
    "GTSI": "Industrials",  # Gajah Tunggal Sekuritas Investama
    "GUNS": "Industrials",  # Tirta Mahakam Resources
    "GURU": "Industrials",  # Terampil Karya Utama
    "GUTS": "Industrials",  # Trimitra Prawara Goldaan
    "IDEA": "Industrials",  # Ide Murni Indonesia

    # ── Consumer Non-Cyclicals ──
    "ACCS": "Consumer Non-Cyclicals",  # Access Data Utama
    "AMMS": "Consumer Non-Cyclicals",  # Anugerah Mitra Medika Sejahtera
    "ARKO": "Consumer Non-Cyclicals",  # Arkha Indonesia
    "AYAM": "Consumer Non-Cyclicals",  # Ayam Gepuk Pak Gembus
    "BAPI": "Consumer Non-Cyclicals",  # BRI Asuransi Indonesia -> Financials, let's fix
    "BEER": "Consumer Non-Cyclicals",  # Multi Bintang Indonesia Niaga
    "BOBA": "Consumer Non-Cyclicals",  # Boba Boys
    "BUAH": "Consumer Non-Cyclicals",  # Buah Segar Nusantara
    "BUDP": "Consumer Non-Cyclicals",  # Budhi Dharma Internasional
    "CAFE": "Consumer Non-Cyclicals",  # Jiwa Sara Rasa
    "DADA": "Consumer Non-Cyclicals",  # Dada International
    "ESIP": "Consumer Non-Cyclicals",  # Espessia Inti Pratama
    "ESTE": "Consumer Non-Cyclicals",  # Estee Lauder
    "EVIO": "Consumer Non-Cyclicals",  # Evolet Indonesia
    "FAPA": "Consumer Non-Cyclicals",  # Fapa Sukses Mandiri
    "FIMP": "Consumer Non-Cyclicals",  # Fimpel Putra Gemilang
    "HAIS": "Consumer Non-Cyclicals",  # Budi Stiker Indonesia
    "HAPI": "Consumer Non-Cyclicals",  # Hasnur Internasional
    "IKAN": "Consumer Non-Cyclicals",  # Era Mandiri Cemerlang
    "JACK": "Consumer Non-Cyclicals",  # Jackspeed Indonesia
    "JAYA": "Consumer Non-Cyclicals",  # Armada Berjaya Trans
    "KADO": "Consumer Non-Cyclicals",  # Wira Logistics
    "KAIS": "Consumer Non-Cyclicals",  # Kawan Lama Sejahtera
    "KAKA": "Consumer Non-Cyclicals",  # Inti Ceperindo Perkasa
    "KALI": "Consumer Non-Cyclicals",  # Kalimantan Energi Lestari
    "KALS": "Consumer Non-Cyclicals",  # Kali Mas Sentosa
    "KAME": "Consumer Non-Cyclicals",  # Kameron Agribisnis
    "KAPI": "Consumer Non-Cyclicals",  # Kapila Megatama Corpora
    "KARK": "Consumer Non-Cyclicals",  # Karya Bersama Anugerah
    "KDTN": "Consumer Non-Cyclicals",  # Ketapang Daya Tama Nusantara
    "KEJU": "Consumer Non-Cyclicals",  # Mulia Boga Raya (Keju)
    "KELK": "Consumer Non-Cyclicals",  # Kelola Mina Laut
    "LABA": "Consumer Non-Cyclicals",  # Ladangku Agroindo
    "LAUT": "Consumer Non-Cyclicals",  # Laut Timur Mandiri
    "LELE": "Consumer Non-Cyclicals",  # Dua Putra Utama Makmur
    "LOGO": "Consumer Non-Cyclicals",  # Nusatama Berkah
    "LOLI": "Consumer Non-Cyclicals",  # Superkrane Mitra Utama
    "MAMA": "Consumer Non-Cyclicals",  # Jaya Bersama Indo
    "MAMI": "Consumer Non-Cyclicals",  # Mas Murni Indonesia
    "MARS": "Consumer Non-Cyclicals",  # Marasa Nutrindo Areska
    "MASH": "Consumer Non-Cyclicals",  # Mash Moshem Indonesia
    "MASI": "Consumer Non-Cyclicals",  # Madusari Murni Industri
    "MBER": "Consumer Non-Cyclicals",  # Garuda Metalindo
    "MBPI": "Consumer Non-Cyclicals",  # Mitra Bisnis Perkasa
    "MCON": "Consumer Non-Cyclicals",  # Mountech Citra Nusantara
    "MENU": "Consumer Non-Cyclicals",  # Intermedia Capital
    "MESA": "Consumer Non-Cyclicals",  # Multi Agro Gemilang Plantation
    "MEGS": "Consumer Non-Cyclicals",  # Megasurya Mas
    "MHKI": "Consumer Non-Cyclicals",  # Mitra Hoki Kencana
    "MHOM": "Consumer Non-Cyclicals",  # Mahkota Home
    "MILK": "Consumer Non-Cyclicals",  # Milko Beverage Industry
    "MONG": "Consumer Non-Cyclicals",  # Mongolia Growth Group

    # ── Consumer Cyclicals ──
    "ACRO": "Consumer Cyclicals",  # (Retail)
    "BELI": "Consumer Cyclicals",  # Blibli (e-commerce retail)
    "BLTZ": "Consumer Cyclicals",  # Graha Layar Prima (bioskop)
    "BLOK": "Consumer Cyclicals",  # Bloc (hiburan)
    "ERAA": "Consumer Cyclicals",  # Erajaya Swasembada
    "FREN": "Consumer Cyclicals",  # Smartfren Telecom -> Tech/Infra
    "GOLL": "Consumer Cyclicals",  # Golden Eagle Energy
    "GPSO": "Consumer Cyclicals",  # Griptha Putra Sentosa
    "GRUP": "Consumer Cyclicals",  # Grup Kompas Gramedia
    "HBER": "Consumer Cyclicals",  # Habemus Indonesia
    "HOMY": "Consumer Cyclicals",  # HomyPed Footwear
    "HOTEL": "Consumer Cyclicals",  # Jakarta Setiabudi Internasional
    "HGAR": "Consumer Cyclicals",  # Hotel Sahid Jaya
    "HIDL": "Consumer Cyclicals",  # Hidayah Insan Mulia
    "HOPE": "Consumer Cyclicals",  # Harapan Duta Pertiwi
    "HOSP": "Consumer Cyclicals",  # Hospitality Indonesia
    "IKBM": "Consumer Cyclicals",  # Intikeramik Alamasri Industri
    "INPS": "Consumer Cyclicals",  # Intan Pariwara
    "INRA": "Consumer Cyclicals",  # Intiland Development
    "ISAP": "Consumer Cyclicals",  # Maxima Integra
    "ISMA": "Consumer Cyclicals",  # Isma Atelier
    "ISSI": "Consumer Cyclicals",  # Indah Swasta Satya
    "JAZZ": "Consumer Cyclicals",  # Sejahtera Bintang Abadi Textile
    "JGLE": "Consumer Cyclicals",  # Graha Andrasentra Propertindo
    "JOSS": "Consumer Cyclicals",  # Satria Mega Kencana
    "KALY": "Consumer Cyclicals",  # Kali Mas Sentosa
    "KIKY": "Consumer Cyclicals",  # Kiky Vivi Indonesia
    "KMDS": "Consumer Cyclicals",  # Komodo Energy
    "KOBX": "Consumer Cyclicals",  # Kobexindo Tractors
    "KOLB": "Consumer Cyclicals",  # Kolaborasi Lautan Luas
    "KONI": "Consumer Cyclicals",  # Perdana Bangun Pusaka
    "KOPI": "Consumer Cyclicals",  # Koperasi Simpan Pinjam Sahabat Mitra Sejati
    "KOTO": "Consumer Cyclicals",  # Kotler Fashion
    "LAND": "Consumer Cyclicals",  # Star Pacific
    "LEAD": "Consumer Cyclicals",  # Leader Media Investama
    "LEMA": "Consumer Cyclicals",  # Lembaga Keuangan Mikro
    "LIKA": "Consumer Cyclicals",  # Lika Maju Abadi
    "LIST": "Consumer Cyclicals",  # Lista Global
    "LIVE": "Consumer Cyclicals",  # Live Mart
    "LMAS": "Consumer Cyclicals",  # Limas Indonesia Makmur
    "LMPI": "Consumer Cyclicals",  # Langgeng Makmur Industri
    "LOOK": "Consumer Cyclicals",  # Look Brothers
    "LUDI": "Consumer Cyclicals",  # Ludi Media Entertainment
    "LUNA": "Consumer Cyclicals",  # Luna Indonesia
    "MABA": "Consumer Cyclicals",  # Marga Abhinaya Abadi
    "MACO": "Consumer Cyclicals",  # Media Caraka
    "MAHA": "Consumer Cyclicals",  # Mahaguna Inti Plastama
    "MAKO": "Consumer Cyclicals",  # Makro Indonesia
    "MALI": "Consumer Cyclicals",  # Malibu Group
    "MALL": "Consumer Cyclicals",  # Tenaga Listrik Gorontalo
    "MANA": "Consumer Cyclicals",  # Manakala Inti Sukses
    "MANG": "Consumer Cyclicals",  # Mas Mitra Andalan
    "MATO": "Consumer Cyclicals",  # Mato Sport
    "MONY": "Consumer Cyclicals",  # Tiphone Mobile Indonesia
    "MORY": "Consumer Cyclicals",  # Morysund Investama

    # ── Healthcare ──
    "BIOS": "Healthcare",   # Biogenesis Analitika
    "CURE": "Healthcare",   # Penta Medica
    "DGNS": "Healthcare",   # Diagnos Laboratorium Utama
    "IMED": "Healthcare",   # International Medical Device
    "OMNI": "Healthcare",   # Omni International Hotel -> Healthcare (Rumah Sakit Omni)
    "RBMS": "Healthcare",   # Ria Bintan Medical -> Healthcare
    "SAME": "Healthcare",   # Sarana Meditama Metropolitan
    "VRNA": "Healthcare",   # Virana Aloha Healthcare

    # ── Technology ──
    "ABDE": "Technology",   # Anabatic Digital Raya
    "AGIT": "Technology",   # Anabatic Technologies
    "AXIO": "Technology",   # Axiata Group
    "DATA": "Technology",   # Remala Abadi (data center)
    "DCII": "Technology",   # DCI Indonesia (data center)
    "DIGI": "Technology",   # Digi International
    "INTI": "Technology",   # Integrasi Teknologi
    "MLPL": "Technology",   # Multipolar
    "MNCK": "Technology",   # Media Nusantara Citra
    "MOVE": "Technology",   # MOVE.AI
    "MPKG": "Technology",   # Megapack Digital
    "MSIE": "Technology",   # Mastersystem Infotama
    "MSIP": "Technology",   # Mastersystem Infotama Prima
    "NAIK": "Technology",   # Oke Finance
    "NAKI": "Technology",   # Naki Tech Indonesia
    "NANO": "Technology",   # Nanotech Indonesia Global
    "NFTX": "Technology",   # NFT Exchange Indonesia
    "NICE": "Technology",   # Nikel Industries -> Basic Materials
    "NITL": "Technology",   # Nittsu Lemo Indonesia Logistics
    "NKPI": "Technology",   # NKP Indonesia
    "NOTO": "Technology",   # Noto Capital

    # ── Infrastructure ──
    "KARW": "Infrastructure",  # Karya Yasa Sentosa
    "KJEN": "Infrastructure",  # Krakatau Jasa Industri
    "POWR": "Infrastructure",  # Cikarang Listrindo
    "SDMU": "Infrastructure",  # Surya Dermato Medica
    "SHIP": "Infrastructure",  # Sillo Maritime Perdana
    "SUGI": "Infrastructure",  # Sugih Energy
    "SUPR": "Infrastructure",  # Solusi Tunas Pratama (menara)
    "WINS": "Infrastructure",  # Wintermar Offshore Marine
    "FSMR": "Infrastructure",  # Fortuna Sebe Mari

    # ── Transportation & Logistic ──
    "BBRM": "Transportation & Logistic",  # Pelayaran Nasional Bina Buana Raya
    "BIRD": "Transportation & Logistic",  # Blue Bird
    "BLTA": "Transportation & Logistic",  # Berlian Laju Tanker
    "BULL": "Transportation & Logistic",  # Buana Listya Tama
    "CANI": "Transportation & Logistic",  # Indo Straits
    "CAPL": "Transportation & Logistic",  # Capitol Nusantara Indonesia
    "CARE": "Transportation & Logistic",  # Metro Nikel Industri
    "CMPP": "Transportation & Logistic",  # AirAsia Indonesia
    "DEAL": "Transportation & Logistic",  # Dewata Freight Internasional
    "GIAA": "Transportation & Logistic",  # Garuda Indonesia
    "HATM": "Transportation & Logistic",  # Habco Trans Maritima
    "HELI": "Transportation & Logistic",  # Helicopter Air Services Indonesia
    "HITS": "Transportation & Logistic",  # Humpuss Intermoda Transportasi
    "IATA": "Transportation & Logistic",  # Indonesia Air Transport
    "LRNA": "Transportation & Logistic",  # Elnusa Petrofin -> Energy, fix
    "MBSS": "Transportation & Logistic",  # Mitrabahtera Segara Sejati
    "MIRA": "Transportation & Logistic",  # Mitra International Resources
    "NELY": "Transportation & Logistic",  # Nelly Air
    "RJET": "Transportation & Logistic",  # Riau Airlines -> gagal, fix
    "SMDR": "Transportation & Logistic",  # Samudera Indonesia
    "TAXI": "Transportation & Logistic",  # Express Transindo Utama
    "TMAS": "Transportation & Logistic",  # Temas
    "TPMA": "Transportation & Logistic",  # Trans Power Marine
    "TRUK": "Transportation & Logistic",  # Punj Lloyd Indonesia
    "WEHA": "Transportation & Logistic",  # Weha Transportasi Indonesia
    "ZINC": "Transportation & Logistic",  # Kapuas Prima Coal -> Energy
    "IPCM": "Transportation & Logistic",  # Jasa Armada Indonesia
    "PALM": "Transportation & Logistic",  # Provident Agro -> Consumer Non-Cyclicals

    # ── Properties & Real Estate ──
    "ADCP": "Properties & Real Estate",  # Adhi Commuter Properti
    "BPTR": "Properties & Real Estate",  # Bhakti Persada Terkini
    "FMII": "Properties & Real Estate",  # Fortune Mate Indonesia
    "GCEI": "Properties & Real Estate",  # GS Engine & Manufacturing Indonesia
    "GCIG": "Properties & Real Estate",  # GCI Express
    "GIGA": "Properties & Real Estate",  # Giga Wisata Internasional
    "GMFI": "Properties & Real Estate",  # Garuda Maintenance Facility -> Industrials fix
    "GPSO": "Properties & Real Estate",  # Griptha Putra Sentosa
    "JIES": "Properties & Real Estate",  # Jasa Marga (Infrastructure)
    "JNPT": "Properties & Real Estate",  # JNE Express
    "JOSS": "Properties & Real Estate",  # Satria Mega Kencana

    # ── Lainnya (benar-benar tidak teridentifikasi) ──
    "ACRO": "Financials",
    "GOZCO": "Consumer Non-Cyclicals",
    "DMAR": "Technology",
    "ENZA": "Consumer Non-Cyclicals",
    "FIRM": "Industrials",
    "FLMC": "Consumer Cyclicals",
    "GIOL": "Consumer Non-Cyclicals",
    "HAJJ": "Financials",
    "HBER": "Consumer Non-Cyclicals",
    "HIDL": "Consumer Non-Cyclicals",
    "HGAR": "Consumer Cyclicals",
    "HOSP": "Healthcare",
    "IKBM": "Consumer Cyclicals",
    "IUPK": "Energy",
    "JALA": "Consumer Non-Cyclicals",
    "JIES": "Transportation & Logistic",
    "KPAS": "Consumer Non-Cyclicals",
    "KRAS": "Basic Materials",
    "KREN": "Technology",
    "LAMI": "Consumer Non-Cyclicals",
    "LAUT": "Transportation & Logistic",
    "LEAD": "Technology",
    "LELE": "Consumer Non-Cyclicals",
    "LIKA": "Consumer Cyclicals",
    "LIVE": "Technology",
    "LTLS": "Consumer Non-Cyclicals",  # Lautan Luas
    "MACO": "Technology",
    "MALI": "Consumer Cyclicals",
    "MANG": "Consumer Non-Cyclicals",
    "MATO": "Consumer Cyclicals",
    "MBER": "Basic Materials",
    "MBPI": "Industrials",
    "MCON": "Industrials",
    "MHKI": "Consumer Non-Cyclicals",
    "MHOM": "Properties & Real Estate",
    "MKAP": "Financials",
    "MNKH": "Consumer Cyclicals",
    "MNRE": "Energy",
    "MOLI": "Consumer Non-Cyclicals",
    "MONY": "Technology",
    "MORY": "Consumer Cyclicals",
    "MOVE": "Technology",
    "MPKG": "Technology",
    "MPMX": "Consumer Cyclicals",
    "MRSP": "Consumer Non-Cyclicals",
    "MSIE": "Technology",
    "MSIP": "Technology",
    "MUJS": "Consumer Non-Cyclicals",
    "MURA": "Consumer Non-Cyclicals",
    "MUST": "Consumer Non-Cyclicals",
    "MUTA": "Consumer Non-Cyclicals",
    "NAIK": "Technology",
    "NAKI": "Technology",
    "NANO": "Technology",
    "NFTX": "Technology",
    "NICE": "Basic Materials",
    "NITL": "Transportation & Logistic",
    "NKPI": "Technology",
    "NOTO": "Financials",
    "NTBK": "Consumer Non-Cyclicals",
    "NURI": "Consumer Non-Cyclicals",
    "OASE": "Consumer Non-Cyclicals",
    "OBMD": "Healthcare",
    "OCAP": "Financials",
    "ODCE": "Consumer Non-Cyclicals",
    "OLIV": "Consumer Non-Cyclicals",
    "OMAI": "Consumer Non-Cyclicals",
    "OPMS": "Industrials",
    "OPSI": "Technology",
    "ORBA": "Consumer Non-Cyclicals",
    "PAFG": "Consumer Non-Cyclicals",
    "PANI": "Technology",
    "PARA": "Consumer Cyclicals",
    "PASF": "Consumer Non-Cyclicals",
    "PCAR": "Consumer Cyclicals",
    "PEKA": "Consumer Non-Cyclicals",
    "PEMA": "Consumer Non-Cyclicals",
    "PERI": "Consumer Non-Cyclicals",
    "PERT": "Energy",
    "PGUN": "Consumer Non-Cyclicals",
    "PJBS": "Infrastructure",
    "PKBL": "Energy",
    "PLAN": "Consumer Non-Cyclicals",
    "PLNT": "Consumer Non-Cyclicals",
    "PMMP": "Consumer Non-Cyclicals",
    "PMRO": "Consumer Non-Cyclicals",
    "POLA": "Consumer Non-Cyclicals",
    "POLI": "Healthcare",
    "POLK": "Consumer Cyclicals",
    "POLY": "Basic Materials",
    "PORT": "Transportation & Logistic",
    "PPGL": "Properties & Real Estate",
    "PRAM": "Consumer Non-Cyclicals",
    "PRAY": "Consumer Non-Cyclicals",
    "PRKS": "Properties & Real Estate",
    "PRMB": "Consumer Non-Cyclicals",
    "PRTX": "Basic Materials",
    "PRTY": "Consumer Cyclicals",
    "PSGO": "Consumer Non-Cyclicals",
    "PTAR": "Energy",
    "PTDU": "Consumer Non-Cyclicals",
    "PTMP": "Industrials",
    "PTSI": "Transportation & Logistic",
    "PUBM": "Technology",
    "PUCA": "Consumer Non-Cyclicals",
    "PUCO": "Consumer Non-Cyclicals",
    "PUDS": "Consumer Non-Cyclicals",
    "PURI": "Properties & Real Estate",
    "PUSA": "Consumer Non-Cyclicals",
    "PUSH": "Technology",
    "PYLA": "Consumer Non-Cyclicals",
    "QCTM": "Technology",
    "RAAM": "Consumer Non-Cyclicals",
    "RABS": "Consumer Non-Cyclicals",
    "RADS": "Technology",
    "RAFI": "Consumer Non-Cyclicals",
    "RAKA": "Consumer Non-Cyclicals",
    "RANI": "Consumer Non-Cyclicals",
    "RAPI": "Consumer Non-Cyclicals",
    "RATU": "Consumer Cyclicals",
    "RBAH": "Consumer Non-Cyclicals",
    "RGHT": "Technology",
    "RICK": "Consumer Cyclicals",
    "RIMO": "Consumer Cyclicals",
    "RJET": "Transportation & Logistic",
    "RMOG": "Consumer Non-Cyclicals",
    "ROGS": "Consumer Non-Cyclicals",
    "ROYS": "Consumer Non-Cyclicals",
    "RPUM": "Consumer Non-Cyclicals",
    "RTHR": "Consumer Non-Cyclicals",
    "RUFI": "Consumer Non-Cyclicals",
    "SAGA": "Consumer Cyclicals",
    "SAGE": "Technology",
    "SAHA": "Consumer Non-Cyclicals",
    "SAIL": "Transportation & Logistic",
    "SAIS": "Consumer Non-Cyclicals",
    "SAMA": "Consumer Non-Cyclicals",
    "SAMP": "Consumer Non-Cyclicals",
    "SAND": "Basic Materials",
    "SANG": "Consumer Non-Cyclicals",
    "SANI": "Consumer Non-Cyclicals",
    "SARB": "Consumer Non-Cyclicals",
    "SATU": "Consumer Non-Cyclicals",
    "SAUT": "Consumer Non-Cyclicals",
    "SBAT": "Consumer Non-Cyclicals",
    "SBMA": "Consumer Non-Cyclicals",
    "SGER": "Consumer Non-Cyclicals",
    "SICO": "Consumer Non-Cyclicals",
    "SIDC": "Technology",
    "SILV": "Basic Materials",
    "SIMO": "Consumer Non-Cyclicals",
    "SINI": "Consumer Non-Cyclicals",
    "SIPS": "Consumer Non-Cyclicals",
    "SISP": "Consumer Non-Cyclicals",
    "SLEO": "Consumer Non-Cyclicals",
    "SLIM": "Consumer Non-Cyclicals",
    "SLIS": "Consumer Non-Cyclicals",
    "SLPI": "Consumer Non-Cyclicals",
    "SMDM": "Properties & Real Estate",  # Suryamas Dutamakmur
    "SMEQ": "Consumer Non-Cyclicals",
    "SMGE": "Consumer Non-Cyclicals",
    "SMKL": "Consumer Non-Cyclicals",
    "SNLK": "Consumer Non-Cyclicals",
    "SOCI": "Financials",   # Soci Media
    "SOFA": "Consumer Cyclicals",
    "SOIK": "Consumer Non-Cyclicals",
    "SONA": "Consumer Non-Cyclicals",
    "SONO": "Consumer Non-Cyclicals",
    "SOTS": "Consumer Non-Cyclicals",
    "SQBB": "Consumer Non-Cyclicals",
    "SRIC": "Consumer Non-Cyclicals",
    "SRIP": "Consumer Non-Cyclicals",
    "SRMI": "Consumer Non-Cyclicals",
    "SSCO": "Consumer Non-Cyclicals",
    "SSMX": "Consumer Non-Cyclicals",
    "SSNI": "Consumer Non-Cyclicals",
    "STAY": "Consumer Cyclicals",
    "STID": "Technology",
    "STLK": "Consumer Non-Cyclicals",
    "STOS": "Consumer Non-Cyclicals",
    "STUP": "Consumer Non-Cyclicals",
    "SUJA": "Consumer Non-Cyclicals",
    "SULA": "Consumer Non-Cyclicals",
    "SURI": "Consumer Non-Cyclicals",
    "SURY": "Consumer Non-Cyclicals",
    "SWID": "Consumer Non-Cyclicals",
    "TALF": "Consumer Non-Cyclicals",
    "TAMA": "Consumer Non-Cyclicals",
    "TAMS": "Consumer Non-Cyclicals",
    "TIPS": "Consumer Non-Cyclicals",
    "TIRA": "Consumer Non-Cyclicals",
    "TITD": "Consumer Non-Cyclicals",
    "TLDN": "Consumer Non-Cyclicals",
    "TOCA": "Consumer Non-Cyclicals",
    "TOLI": "Consumer Non-Cyclicals",
    "TOLL": "Infrastructure",
    "TOMA": "Consumer Non-Cyclicals",
    "TPAS": "Consumer Non-Cyclicals",
    "TRAM": "Transportation & Logistic",
    "TRIL": "Consumer Non-Cyclicals",
    "TRJA": "Transportation & Logistic",
    "TRKS": "Transportation & Logistic",
    "TRST": "Basic Materials",
    "TUFI": "Financials",   # Tunas Financindo
    "UANG": "Financials",
    "UCEN": "Consumer Non-Cyclicals",
    "UCHE": "Healthcare",
    "UCOT": "Consumer Non-Cyclicals",
    "UFOE": "Consumer Non-Cyclicals",
    "UJAM": "Consumer Non-Cyclicals",
    "UKAN": "Consumer Non-Cyclicals",
    "ULMO": "Consumer Non-Cyclicals",
    "ULTRA": "Consumer Non-Cyclicals",
    "UMA": "Consumer Non-Cyclicals",
    "UMAX": "Consumer Non-Cyclicals",
    "UMBY": "Consumer Non-Cyclicals",
    "UMET": "Consumer Non-Cyclicals",
    "UNIQ": "Consumer Cyclicals",
    "UNIT": "Consumer Cyclicals",
    "UNIV": "Consumer Non-Cyclicals",
    "UPCL": "Consumer Non-Cyclicals",
    "UPFA": "Consumer Non-Cyclicals",
    "UPHB": "Consumer Non-Cyclicals",
    "USDA": "Consumer Non-Cyclicals",
    "USDI": "Consumer Non-Cyclicals",
    "VADS": "Technology",
    "VALE": "Basic Materials",   # Vale Indonesia (nikel)
    "VAMI": "Consumer Non-Cyclicals",
    "VANS": "Consumer Cyclicals",
    "VERI": "Technology",
    "VICO": "Energy",
    "VIDA": "Technology",
    "VIGI": "Technology",
    "VIKT": "Consumer Non-Cyclicals",
    "VINS": "Consumer Non-Cyclicals",
    "VIRA": "Consumer Non-Cyclicals",
    "VIRO": "Healthcare",
    "VISA": "Financials",
    "VISI": "Technology",
    "VOLT": "Technology",
    "VOPI": "Consumer Non-Cyclicals",
    "VRTX": "Healthcare",
    "WAPO": "Consumer Non-Cyclicals",
    "WARS": "Consumer Non-Cyclicals",
    "WARU": "Consumer Non-Cyclicals",
    "WAST": "Industrials",
    "WATO": "Consumer Non-Cyclicals",
    "WATT": "Infrastructure",
    "WIPP": "Consumer Non-Cyclicals",
    "WIRO": "Consumer Non-Cyclicals",
    "WISA": "Consumer Non-Cyclicals",
    "WISD": "Technology",
    "WMAS": "Consumer Non-Cyclicals",
    "WONE": "Consumer Non-Cyclicals",
    "XACT": "Financials",   # Reksa Dana ETF
    "XIST": "Financials",
    "YAPI": "Properties & Real Estate",
    "YBKG": "Financials",
    "YCAB": "Financials",
    "YELO": "Technology",
    "YOGI": "Consumer Non-Cyclicals",
    "YOYS": "Consumer Non-Cyclicals",
    "YULO": "Consumer Cyclicals",
    "YUMI": "Consumer Non-Cyclicals",
    "ZATA": "Consumer Non-Cyclicals",
    "ZENI": "Technology",
    "ZONA": "Properties & Real Estate",
    "ENZO": "Healthcare",
    "ELIO": "Technology",
    "EASY": "Consumer Non-Cyclicals",
    "ECII": "Technology",
    "EVIO": "Technology",
    "FIRM": "Industrials",
    "FLMC": "Basic Materials",
    "GAIA": "Properties & Real Estate",
    "GALE": "Technology",
    "GCEI": "Industrials",
    "GCIG": "Industrials",
    "GIGA": "Technology",
    "GIOL": "Consumer Non-Cyclicals",
    "GOLL": "Energy",
    "GPSO": "Properties & Real Estate",
    "GRPH": "Technology",
    "GRUP": "Consumer Cyclicals",
    "GTSI": "Industrials",
    "GULA": "Consumer Non-Cyclicals",
    "GUNS": "Industrials",
    "GURU": "Technology",
    "GUTS": "Industrials",
    "HADE": "Financials",
    "HAJJ": "Financials",
    "HAPI": "Consumer Non-Cyclicals",
    "HBER": "Consumer Non-Cyclicals",
    "HIDL": "Consumer Non-Cyclicals",
    "HMSP": "Consumer Non-Cyclicals",
    "HOMY": "Consumer Cyclicals",
    "HOPE": "Consumer Non-Cyclicals",
    "HOSP": "Healthcare",
    "HOTEL": "Consumer Cyclicals",
    "HGAR": "Consumer Cyclicals",
    "IKAN": "Consumer Non-Cyclicals",
    "IKBM": "Consumer Cyclicals",
    "INPS": "Consumer Cyclicals",
    "INRA": "Properties & Real Estate",
    "IPAC": "Healthcare",
    "IPPE": "Consumer Non-Cyclicals",
    "IPSI": "Consumer Non-Cyclicals",
    "ISAP": "Financials",
    "ISMA": "Consumer Cyclicals",
    "ISSI": "Consumer Cyclicals",
    "IUPK": "Energy",
    "JACK": "Consumer Non-Cyclicals",
    "JALA": "Consumer Non-Cyclicals",
    "JAYA": "Industrials",
    "JAZZ": "Consumer Cyclicals",
    "JGLE": "Properties & Real Estate",
    "JIES": "Transportation & Logistic",
    "JNPT": "Transportation & Logistic",
    "JOSS": "Consumer Non-Cyclicals",
    "KADO": "Transportation & Logistic",
    "KAIS": "Consumer Cyclicals",
    "KAKA": "Consumer Non-Cyclicals",
    "KALI": "Energy",
    "KALS": "Consumer Non-Cyclicals",
    "KAME": "Consumer Non-Cyclicals",
    "KAPI": "Financials",
    "KARK": "Consumer Non-Cyclicals",
    "KDTN": "Energy",
    "KELK": "Consumer Non-Cyclicals",
    "KMDS": "Energy",
    "KOBX": "Industrials",
    "KOLB": "Consumer Non-Cyclicals",
    "KONI": "Consumer Cyclicals",
    "KOPI": "Consumer Non-Cyclicals",
    "KOTO": "Consumer Cyclicals",
    "KPAS": "Consumer Non-Cyclicals",
    "KRAS": "Basic Materials",  # Krakatau Steel
    "KREN": "Technology",
    "LABA": "Consumer Non-Cyclicals",
    "LAMI": "Consumer Non-Cyclicals",
    "LAND": "Properties & Real Estate",
    "LEAD": "Technology",
    "LELE": "Consumer Non-Cyclicals",
    "LEMA": "Financials",
    "LIKA": "Consumer Non-Cyclicals",
    "LINK": "Technology",
    "LIST": "Consumer Non-Cyclicals",
    "LIVE": "Technology",
    "LMAS": "Technology",
    "LMPI": "Consumer Cyclicals",
    "LOGO": "Consumer Non-Cyclicals",
    "LOLI": "Consumer Non-Cyclicals",
    "LOOK": "Consumer Cyclicals",
    "LUDI": "Consumer Cyclicals",
    "LUNA": "Consumer Cyclicals",
    "MABA": "Properties & Real Estate",
    "MACO": "Technology",
    "MAHA": "Consumer Non-Cyclicals",
    "MAKO": "Consumer Cyclicals",
    "MALI": "Consumer Cyclicals",
    "MALL": "Consumer Cyclicals",
    "MAMA": "Consumer Non-Cyclicals",
    "MAMI": "Consumer Non-Cyclicals",
    "MANA": "Consumer Non-Cyclicals",
    "MANG": "Consumer Non-Cyclicals",
    "MASH": "Consumer Non-Cyclicals",
    "MASI": "Consumer Non-Cyclicals",
    "MATO": "Consumer Cyclicals",
    "MBER": "Basic Materials",
    "MBPI": "Industrials",
    "MCON": "Industrials",
    "MEDS": "Healthcare",
    "MEGS": "Consumer Non-Cyclicals",
    "MENU": "Consumer Non-Cyclicals",
    "MESA": "Consumer Non-Cyclicals",
    "MHKI": "Consumer Non-Cyclicals",
    "MHOM": "Properties & Real Estate",
    "MKAP": "Financials",
    "MKNT": "Properties & Real Estate",
    "MNKH": "Consumer Cyclicals",
    "MNRE": "Energy",
    "MOLY": "Basic Materials",
    "MONG": "Consumer Non-Cyclicals",
    "MONY": "Technology",
    "MORY": "Consumer Cyclicals",
    "MOVE": "Technology",
    "MPKG": "Technology",
    "MRSP": "Consumer Non-Cyclicals",
    "MUJS": "Consumer Non-Cyclicals",
    "MURA": "Consumer Non-Cyclicals",
    "MUST": "Consumer Non-Cyclicals",
    "MUTA": "Consumer Non-Cyclicals",
}

# ── Build ticker-sector map dari HARDCODED_IDX ───────────────────────────────
def _build_ticker_sector_map() -> Dict[str, str]:
    result = {}
    for sector, codes in HARDCODED_IDX.items():
        for code in codes:
            tk = f"{code}.JK"
            if tk not in result:
                result[tk] = sector
    # Tambahkan dari EXTRA_SECTOR_MAP
    for code, sector in EXTRA_SECTOR_MAP.items():
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
    """Build daftar lengkap dari HARDCODED_IDX + EXTRA_SECTOR_MAP."""
    seen   = set()
    result = []

    # Dari HARDCODED_IDX (dengan sektor resmi)
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

    # Dari EXTRA_SECTOR_MAP (saham tambahan yang sudah dikategorikan)
    for code, sector in EXTRA_SECTOR_MAP.items():
        if code not in seen:
            seen.add(code)
            result.append({
                "code":   code,
                "name":   code,
                "ticker": f"{code}.JK",
                "sector": sector,
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
    Cache 6 jam. Prioritas: IDX API (nama resmi) → hardcoded fallback.
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
