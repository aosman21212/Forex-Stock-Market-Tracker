from odoo import fields, models


class MarketRateHistory(models.Model):
    _name        = 'market.rate.history'
    _description = 'Market Rate History'
    _order       = 'date desc'
    _rec_name    = 'symbol_id'

    symbol_id = fields.Many2one(
        'market.symbol',
        string='Symbol',
        required=True,
        ondelete='cascade',
        index=True,
    )
    date = fields.Datetime(
        string='Timestamp',
        required=True,
        default=fields.Datetime.now,
        index=True,
    )
    price = fields.Float(
        string='Price',
        digits=(16, 6),
        required=True,
    )
    symbol_type = fields.Selection(
        related='symbol_id.symbol_type',
        string='Type',
        store=True,
    )
