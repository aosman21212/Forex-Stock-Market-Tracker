import logging
import requests

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

FRANKFURTER_URL = 'https://api.frankfurter.app/latest'
YAHOO_URL       = 'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}'
COINGECKO_URL   = 'https://api.coingecko.com/api/v3/simple/price'

# CoinGecko requires full coin IDs (not ticker symbols)
CRYPTO_ID_MAP = {
    'BTC':  'bitcoin',
    'ETH':  'ethereum',
    'BNB':  'binancecoin',
    'SOL':  'solana',
    'XRP':  'ripple',
    'USDT': 'tether',
    'ADA':  'cardano',
    'DOGE': 'dogecoin',
    'AVAX': 'avalanche-2',
    'DOT':  'polkadot',
    'MATIC':'matic-network',
    'LTC':  'litecoin',
}


class MarketSymbol(models.Model):
    _name        = 'market.symbol'
    _description = 'Market Symbol'
    _order       = 'symbol_type, symbol'

    # ── Identity ──────────────────────────────────────────────────────── #
    name = fields.Char(string='Name', required=True)
    symbol = fields.Char(
        string='Symbol / Ticker',
        required=True,
        index=True,
        help='Forex: EUR/USD  |  Stock: AAPL  |  Crypto: BTC',
    )
    symbol_type = fields.Selection(
        selection=[
            ('forex',  'Forex'),
            ('stock',  'Stock'),
            ('crypto', 'Crypto'),
        ],
        string='Type',
        required=True,
        default='forex',
        index=True,
    )
    currency_quote = fields.Char(
        string='Quote Currency',
        default='USD',
        help='Denomination currency (e.g. USD)',
    )
    active = fields.Boolean(default=True)

    # ── Live Price ─────────────────────────────────────────────────────── #
    price          = fields.Float('Price',          digits=(16, 6), readonly=True)
    price_previous = fields.Float('Previous Close', digits=(16, 6), readonly=True)
    change_pct     = fields.Float('Change %',       digits=(6, 4),  readonly=True)
    price_high     = fields.Float('High',           digits=(16, 6), readonly=True)
    price_low      = fields.Float('Low',            digits=(16, 6), readonly=True)
    last_update    = fields.Datetime('Last Updated', readonly=True)

    # ── Computed helpers ───────────────────────────────────────────────── #
    price_direction = fields.Selection(
        selection=[('up', 'Up'), ('down', 'Down'), ('flat', 'Flat')],
        compute='_compute_price_direction',
        string='Direction',
    )
    history_ids = fields.One2many('market.rate.history', 'symbol_id', string='History')
    history_count = fields.Integer(compute='_compute_history_count', string='Data Points')

    # ── Computes ───────────────────────────────────────────────────────── #
    @api.depends('change_pct')
    def _compute_price_direction(self):
        for rec in self:
            if rec.change_pct > 0:
                rec.price_direction = 'up'
            elif rec.change_pct < 0:
                rec.price_direction = 'down'
            else:
                rec.price_direction = 'flat'

    def _compute_history_count(self):
        for rec in self:
            rec.history_count = len(rec.history_ids)

    def name_get(self):
        return [(rec.id, f'{rec.symbol} — {rec.name}') for rec in self]

    # ── Smart button: history ──────────────────────────────────────────── #
    def action_view_history(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Price History — {self.symbol}',
            'res_model': 'market.rate.history',
            'view_mode': 'list,graph',
            'domain': [('symbol_id', '=', self.id)],
            'context': {'default_symbol_id': self.id},
        }

    # ── Manual refresh (button on list / form) ─────────────────────────── #
    def action_refresh_prices(self):
        targets = self if self else self.search([('active', '=', True)])
        self._fetch_and_update(targets)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title':   _('Prices Refreshed'),
                'message': _('%d symbol(s) updated.') % len(targets),
                'type':    'success',
                'sticky':  False,
            },
        }

    # ── Scheduled action entry-point ───────────────────────────────────── #
    @api.model
    def _cron_refresh_prices(self):
        self._fetch_and_update(self.search([('active', '=', True)]))

    # ── Orchestration ─────────────────────────────────────────────────── #
    @api.model
    def _fetch_and_update(self, symbols):
        forex  = symbols.filtered(lambda s: s.symbol_type == 'forex')
        stocks = symbols.filtered(lambda s: s.symbol_type == 'stock')
        crypto = symbols.filtered(lambda s: s.symbol_type == 'crypto')
        if forex:
            self._fetch_forex(forex)
        for sym in stocks:
            self._fetch_stock(sym)
        if crypto:
            self._fetch_crypto(crypto)

    # ── Frankfurter — Forex ────────────────────────────────────────────── #
    @api.model
    def _fetch_forex(self, symbols):
        try:
            resp = requests.get(
                FRANKFURTER_URL,
                params={'base': 'EUR'},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            _logger.warning('Frankfurter API error: %s', exc)
            return

        rates = data.get('rates', {})
        rates['EUR'] = 1.0  # base

        for sym in symbols:
            parts = sym.symbol.upper().replace('-', '/').split('/')
            if len(parts) != 2:
                _logger.warning('Forex symbol %s not in BASE/QUOTE format', sym.symbol)
                continue
            base, quote = parts
            if base not in rates or quote not in rates:
                _logger.warning('Currency %s or %s not in Frankfurter data', base, quote)
                continue
            # Cross-rate calculation
            new_price = rates[quote] / rates[base]
            self._write_price(sym, new_price)

    # ── Yahoo Finance — Stocks ─────────────────────────────────────────── #
    @api.model
    def _fetch_stock(self, sym):
        try:
            resp = requests.get(
                YAHOO_URL.format(symbol=sym.symbol),
                headers={'User-Agent': 'Mozilla/5.0'},
                params={'interval': '1d', 'range': '2d'},
                timeout=10,
            )
            resp.raise_for_status()
            result = resp.json()['chart']['result'][0]
            meta = result['meta']
            new_price  = float(meta.get('regularMarketPrice', 0))
            prev_close = float(meta.get('chartPreviousClose') or meta.get('previousClose', 0))
            high       = float(meta.get('regularMarketDayHigh', 0))
            low        = float(meta.get('regularMarketDayLow', 0))
            self._write_price(sym, new_price, prev_close, high, low)
        except Exception as exc:
            _logger.warning('Yahoo Finance error for %s: %s', sym.symbol, exc)

    # ── CoinGecko — Crypto ─────────────────────────────────────────────── #
    @api.model
    def _fetch_crypto(self, symbols):
        ids_map = {}
        for sym in symbols:
            cg_id = CRYPTO_ID_MAP.get(sym.symbol.upper())
            if cg_id:
                ids_map[cg_id] = sym
            else:
                _logger.warning('No CoinGecko mapping for %s', sym.symbol)

        if not ids_map:
            return

        try:
            resp = requests.get(
                COINGECKO_URL,
                params={
                    'ids':               ','.join(ids_map.keys()),
                    'vs_currencies':     'usd',
                    'include_24hr_change': 'true',
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            _logger.warning('CoinGecko API error: %s', exc)
            return

        for cg_id, sym in ids_map.items():
            coin = data.get(cg_id, {})
            new_price  = float(coin.get('usd', 0))
            change_24h = float(coin.get('usd_24h_change', 0))
            if new_price:
                prev = new_price / (1 + change_24h / 100) if change_24h else new_price
                self._write_price(sym, new_price, prev)

    # ── Write helper ───────────────────────────────────────────────────── #
    @api.model
    def _write_price(self, sym, new_price, prev_price=None, high=None, low=None):
        if not new_price:
            return
        prev   = prev_price if prev_price is not None else sym.price
        change = ((new_price - prev) / prev * 100) if prev else 0.0
        vals = {
            'price':          new_price,
            'price_previous': prev,
            'change_pct':     change,
            'last_update':    fields.Datetime.now(),
        }
        if high:
            vals['price_high'] = high
        if low:
            vals['price_low'] = low
        sym.write(vals)
        # Snapshot to history
        self.env['market.rate.history'].create({
            'symbol_id': sym.id,
            'date':      fields.Datetime.now(),
            'price':     new_price,
        })
