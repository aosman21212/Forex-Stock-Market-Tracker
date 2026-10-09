# -*- coding: utf-8 -*-
# =============================================================================
#  Forex & Stock Market Tracker
# -----------------------------------------------------------------------------
#  Location  : King Abdulaziz Branch Road, Riyadh, Saudi Arabia
#  Email     : sales@leapai.ai
#  Phone     : +966 53 553 3627
#  Website   : https://leapai.ai
#  Developer : Abdulkaraim Osman — Tech Manager | Backend Engineer | DevOps Engineer
#              at Bab International Corp For Specialized Services
#  LinkedIn  : https://www.linkedin.com/in/abdulkaraim-o-385b7a110/
# =============================================================================
{
    'name': 'Forex & Stock Market Tracker',
    'version': '19.0.1.0.0',
    'category': 'Finance/Market Data',
    'summary': 'Live Forex, Stock & Crypto prices using free public APIs',
    'description': """
Forex & Stock Market Tracker
==============================
Track real-time market prices using 100% free APIs — no subscription needed:

- **Forex** (EUR/USD, GBP/USD, USD/JPY …) via Frankfurter (European Central Bank data)
- **Stocks** (AAPL, TSLA, MSFT …) via Yahoo Finance
- **Crypto** (BTC, ETH, SOL …) via CoinGecko

Features:
- Kanban dashboard with live price cards (green ▲ / red ▼)
- Auto-refresh every 30 minutes via scheduled cron
- Manual "Refresh Prices" button (single or bulk)
- Price history log with graph view
- Optional Alpha Vantage API key for premium stock data
    """,
  'author': 'Abdulkrim Osman (+966562984106, +966553368212)',
  'maintainer': 'Abdulkaraim Osman',
  'support': 'sales@leapai.ai',
    'website': 'https://apps.odoo.com',
    'depends': ['base', 'base_setup'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'views/market_symbol_views.xml',
        'views/market_rate_history_views.xml',
        'views/res_config_settings_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
    'price': 0.0,
    'currency': 'EUR',
    'images': ['static/description/banner.svg', 'static/description/icon.png'],
}
