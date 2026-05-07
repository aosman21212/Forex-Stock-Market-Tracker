from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    forex_alpha_vantage_api_key = fields.Char(
        string='Alpha Vantage API Key',
        config_parameter='forex_market_tracker.alpha_vantage_api_key',
        help=(
            'Optional free API key from https://www.alphavantage.co/support/#api-key  '
            'When set, provides higher-quality intraday stock data.'
        ),
    )
