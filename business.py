"""
Business facts used in the page copy, the contact block, the footer, and the
structured data. Keep name, phone, and city identical to the Google Business
Profile and every directory listing.

Empty values are skipped: a section with no data is not rendered, so nothing
here is ever shown as a placeholder.
"""

NAME = 'Estada'
FOUNDER = {'mk': 'Андреј Трендов', 'en': 'Andrej Trendov'}

# Public contact address. A domain address (e.g. andrej@estada.dev) is better
# for trust once a mailbox for it exists.
EMAIL = 'atrendov1@gmail.com'

# International format, e.g. '+389 70 123 456'. When set, the site shows tel:
# and Viber links and adds the number to the structured data.
PHONE = ''

CITY = {'mk': 'Струмица', 'en': 'Strumica'}
POSTAL_CODE = '2400'
COUNTRY_CODE = 'MK'

INSTAGRAM = 'https://www.instagram.com/estada.dev/'
FACEBOOK = 'https://www.facebook.com/profile.php?id=61585353975464'
LINKEDIN = ''  # company page URL
GITHUB = ''    # e.g. https://github.com/<user>

FOUNDER_URL = 'https://trendov.dev'

# Pricing section. Shown on the home page once at least one package is added.
# Example:
# {
#     'name': {'mk': 'Сајт за локал', 'en': 'Venue website'},
#     'price': {'mk': 'од 00.000 ден', 'en': 'from 00,000 MKD'},
#     'includes': {
#         'mk': ['Мени и работно време', 'Домен и хостирање прва година'],
#         'en': ['Menu and opening hours', 'Domain and hosting for the first year'],
#     },
# },
PACKAGES = []

# Monthly hosting and upkeep fee, shown under the packages.
# Example: {'mk': '000 ден месечно', 'en': '000 MKD per month'}
HOSTING_FEE = None

# Named client quotes, used with the client's permission. Example:
# {
#     'quote': {'mk': '...', 'en': '...'},
#     'name': 'Име Презиме',
#     'role': {'mk': 'сопственик, Generacija Cafe', 'en': 'owner, Generacija Cafe'},
# },
TESTIMONIALS = []

# FAQ answers only you can give (price, timeline, who owns the domain, what
# happens if a client leaves Estada). Appended after the standard questions.
# Example: {'mk': ('Колку чини веб-сајт?', 'Од ... ден, зависно од ...'),
#           'en': ('How much does a website cost?', 'From ... MKD, depending on ...')}
EXTRA_FAQ = []
