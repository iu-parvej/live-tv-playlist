import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Strict regex definitions with word boundaries and negative lookahead/lookbehind

# 1. BD SPORTS
RE_BD_SPORTS = [
    r'\bt[\s\-_]?sports\b',
    r'\b(?:gazi|gtv)\b(?!\s*home|\s*garden|\s*cgtv)'
]

# 2. BD NEWS
RE_BD_NEWS = [
    r'\bsomoy\b',
    r'\bjamuna\b',
    r'\bdbc\s*news\b',
    r'\b(?:ekattor|71\s*tv)\b',
    r'\bchannel\s*24\b',
    r'\bindependent\s*tv\b',
    r'\bnews\s*24(?:\s*hd|\s*bd|\s*television)?\b',
    r'\batn\s*news\b',
    r'\bbtv(?:\s*national|\s*world|\s*chattogram|\s*chittagong|\s*ctg)?\b',
    r'\bsangsad\b',
    r'\bjago\s*news\b',
    r'\bnews\s*21\s*bangla\b'
]

# Exclude foreign 24/news channels that match 'news 24' or 'channel 24'
RE_FOREIGN_NEWS_EXCLUDE = [
    r'\blac\b', r'\brai\b', r'\brtve\b', r'\bcity\s*news\b', r'\bitaly\b',
    r'\bfrance\b', r'\bspain\b', r'\bcanada\b', r'\bntv\s*telugu\b', r'\bashwaveega\b',
    r'\b22scope\b', r'\b4tv\b', r'\b6tv\b', r'\b99tv\b', r'\baagaaz\b', r'\baaj\s*i\s*habar\b'
]

# 3. BD ENTERTAINMENT & DRAMA
RE_BD_ENT = [
    r'\bchannel\s*i\b',
    r'\bntv(?:\s*hd|\s*bd)?\b',
    r'\brtv(?:\s*hd|\s*bd)?\b',
    r'\bbanglavision\b',
    r'\bmaasranga\b',
    r'\bdeepto\b',
    r'\batn\s*bangla\b',
    r'\bnagorik\b',
    r'\bchannel\s*9\b',
    r'\bboishakhi\b',
    r'\bdesh\s*tv\b',
    r'\bbijoy\s*tv\b',
    r'\bbangla\s*tv\b',
    r'\bananda\s*tv\b',
    r'\bmohona\b',
    r'\bsa\s*tv\b',
    r'\bmy\s*tv(?:\s*hd|\s*bd)?\b',
    r'\basian\s*tv\b',
    r'\bsananda\s*tv\b'
]

RE_FOREIGN_ENT_EXCLUDE = [
    r'\bnoord\b', r'\boost\b', r'\brijnmond\b', r'\butrecht\b', r'\btoscana\b',
    r'\bnasa\b', r'\baristanis\b', r'\bfeh[eé]rv[aá]r\b', r'\bidman\b', r'\bintv\b',
    r'\bradiosa\b', r'\bsantvani\b', r'\bvissa\b', r'\beurope\b', r'\bze\b'
]

# 4. INDIAN NEWS BLACKLIST (Strictly Excluded)
RE_INDIAN_NEWS = [
    r'\baaj\s*tak\b', r'\babp\b', r'\bindia\s*tv\b', r'\brepublic\b', r'\bndtv\b',
    r'\bzee\s*(?:news|24|hindustan|bharat)\b', r'\bnews\s*18\b', r'\btv9\b',
    r'\bdd\s*news\b', r'\bwion\b', r'\bsansad\b', r'\bnews\s*nation\b', r'\bindia\s*today\b',
    r'\btimes\s*now\b', r'\bmirror\s*now\b', r'\bcnbc\s*awaz\b', r'\bkhabar\b', r'\bsamachar\b',
    r'\bpratham\s*khabar\b', r'\bkalash\s*news\b'
]

# 5. KOLKATA & INDIAN ENTERTAINMENT & MOVIES
RE_KOLKATA_AND_INDIAN_ENT = [
    # Kolkata / Bangla
    r'\bzee\s*bangla\b', r'\bstar\s*jalsha\b', r'\bjalsha\s*movies\b', r'\bcolors\s*bangla\b',
    r'\bsony\s*aath\b', r'\baakash\s*aath\b', r'\bruposhi\s*bangla\b', r'\bdhoom\s*music\b',
    r'\bsangeet\s*bangla\b',
    # Hindi Entertainment
    r'\bstar\s*plus\b', r'\bsony\s*sab\b', r'\bsab\s*tv\b', r'\bzee\s*tv\b', r'\bcolors\s*hd\b',
    r'\bcolors\s*tv\b', r'\bsony\s*entertainment\b', r'\bset\s*india\b', r'\bstar\s*bharat\b',
    r'\b&tv\b', r'\bdangal\b', r'\bshemaroo\b', r'\bbig\s*magic\b', r'\bishara\b',
    # Movies (Hindi, South Dubbed, Regional)
    r'\bstar\s*gold\b', r'\bsony\s*max\b', r'\bzee\s*cinema\b', r'\bcolors\s*cineplex\b',
    r'\bsony\s*pix\b', r'\bzee\s*bollywood\b', r'\b&pictures\b', r'\bgoldmines\b',
    r'\bb4u\s*movies\b', r'\bbhojpuri\s*cinema\b', r'\bfilamchi\b', r'\bmanoranjan\b',
    r'\bdhinchaak\b', r'\bcinema\s*tv\b', r'\bbflix\b', r'\bmovie\s*plus\b', r'\bshubh\s*cinema\b'
]

# 6. ALL SPORTS
RE_ALL_SPORTS = [
    r'\bstar\s*sports\b', r'\bsony\s*sports\b', r'\bsony\s*ten\b', r'\bten\s*[1235]\b',
    r'\bsony\s*six\b', r'\bwillow\b', r'\ba\s*sports\b', r'\bptv\s*sports\b', r'\bastro\s*cricket\b',
    r'\bbein\s*sports?\b', r'\bsky\s*sports?\b', r'\btnt\s*sports?\b', r'\bsupersport\b',
    r'\beurosport\b', r'\bfox\s*sports?\b', r'\bespn\b', r'\bdazn\b', r'\bdd\s*sports\b',
    r'\bdsports\b', r'\bcricket\b', r'\bfootball\b', r'\b2tv\s*sport\b', r'\bbahrain\s*sports\b',
    r'\bjordan\s*sports\b', r'\bmax\s*sport\b', r'\bpremier\s*sports\b', r'\bpremier\s*league\b'
]

# 7. DOCUMENTARY & WILDLIFE
RE_DOCS = [
    r'\bdiscovery\b', r'\banimal\s*planet\b', r'\bnational\s*geographic\b', r'\bnat\s*geo\b',
    r'\bhistory\s*tv18\b', r'\bhistory\b', r'\btlc\b', r'\binvestigation\s*discovery\b',
    r'\bdiscovery\s*science\b', r'\bdiscovery\s*turbo\b', r'\bsony\s*bbc\s*earth\b',
    r'\breal\s*wild\b', r'\bwild\s*earth\b', r'\bwild\s*planet\b', r'\bwild\s*nature\b',
    r'\bautentic\s*history\b', r'\blove\s*nature\b', r'\binwild\b'
]

# 8. MUSIC & KIDS
RE_KIDS_AND_MUSIC = [
    # Kids
    r'\bduronto\b', r'\bcartoon\s*network\b', r'\bnickelodeon\b', r'\bnick\b', r'\bpogo\b',
    r'\bdisney\b', r'\bsony\s*yay\b', r'\bhungama\b', r'\bsonic\b',
    # Music
    r'\bgaan\s*bangla\b', r'\b9xm\b', r'\bmtv\b', r'\bb4u\s*music\b', r'\bmastiii\b',
    r'\bzing\b', r'\btrace\s*urban\b', r'\bdeluxe\s*music\b', r'\bclub\s*mtv\b',
    r'\bmtunes\b', r'\bsangeet\s*bangla\b'
]

# 9. ISLAMIC & DEVOTIONAL
RE_ISLAMIC = [
    r'\bpeace\s*tv\b', r'\bmakkah\b', r'\bmadinah\b', r'\bquran\b', r'\bsunnah\b', r'\bislamic\b'
]

print("Regex rules initialized.")
