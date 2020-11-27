from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools import ustr


class SiteSearchAppConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    def _default_website(self):
        return self.env['website'].search([('company_id', '=', self.env.user.company_id.id)], limit=1)

    website_id = fields.Many2one('website', string="website",
                                 default=_default_website, ondelete='cascade')
    ssa_enable = fields.Boolean('Enable', related='website_id.ssa_enable', readonly=False)
    ssa_log_api = fields.Char('SiteSearchApp Log API', related='website_id.ssa_log_api', readonly=False)
    ssa_test_api = fields.Char('SiteSearchApp Test API', related='website_id.ssa_test_api', readonly=False)
    ssa_index_api = fields.Char('SiteSearchApp Index API', related='website_id.ssa_index_api', readonly=False)
    ssa_delete_api = fields.Char('SiteSearchApp Delete API', related='website_id.ssa_delete_api', readonly=False)
    ssa_search_api = fields.Char('SiteSearchApp Search API', related='website_id.ssa_search_api', readonly=False)
    ssa_indices_api = fields.Char('SiteSearchApp Indices API', related='website_id.ssa_indices_api', readonly=False)
    ssa_documents_api = fields.Char('SiteSearchApp Documents API', related='website_id.ssa_documents_api',
                                    readonly=False)
    ssa_host = fields.Char('Host', related='website_id.ssa_host', readonly=False)
    ssa_user = fields.Char('User', related='website_id.ssa_user', readonly=False)
    ssa_api_key = fields.Char('API Key', related='website_id.ssa_api_key', readonly=False)
    ssa_password = fields.Char('Password', related='website_id.ssa_password', readonly=False)
    ssa_alignment = fields.Selection([('left', 'Left'), ('center', 'Center'), ('right', 'Right')],
                                     'Search Suggestions Box Alignment', related='website_id.ssa_alignment',
                                     readonly=False)
    ssa_ip_whitelist = fields.Char('Whitelist IP', related='website_id.ssa_ip_whitelist', readonly=False)
    ssa_text_color = fields.Char('Text Color', related='website_id.ssa_text_color', readonly=False)
    ssa_title_color = fields.Char('Title Color', related='website_id.ssa_title_color', readonly=False)
    ssa_price_color = fields.Char('Price Color', related='website_id.ssa_price_color', readonly=False)
    ssa_border_color = fields.Char('Border Color', related='website_id.ssa_border_color', readonly=False)
    ssa_loader_color = fields.Char('Loader Color', related='website_id.ssa_loader_color', readonly=False)
    ssa_slash_color = fields.Char('Price Slash Color', related='website_id.ssa_slash_color', readonly=False)
    ssa_highlight_color = fields.Char('Highlight Color', related='website_id.ssa_highlight_color', readonly=False)
    ssa_hover_color = fields.Char('Hover Background Color', related='website_id.ssa_hover_color', readonly=False)
    ssa_bg_color = fields.Char('Container Background Color', related='website_id.ssa_bg_color', readonly=False)
    ssa_title_bg_color = fields.Char('Title Background Color', related='website_id.ssa_title_bg_color', readonly=False)
    ssa_custom_css = fields.Text('Custom CSS', related='website_id.ssa_custom_css', readonly=False)

    def get_indices(self):
        searchapp_model = self.env['searchapp.search']
        try:
            searchapp_model.get_indices(website=self.website_id)
        except Exception as e:
            raise UserError(e)
        return {
            'name': 'SiteSearchApp Indexer',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'searchapp.search',
            'type': 'ir.actions.act_window',
            'context': {'group_by': 'website_id'},
            'target': 'current',
        }

    def index_site(self):
        searchapp_model = self.env['searchapp.search']
        try:
            searchapp_model.get_indices(website=self.website_id)
            searchapp_model.search([('website_id', '=', self.website_id.id)]).index_site()
        except Exception as e:
            raise UserError("%s" % ustr(e))
        raise UserError("Successfully indexed site to SiteSearchApp!")

    def test_connection(self):
        self.ensure_one()
        host = self.ssa_test_api
        searchapp_model = self.env['searchapp.search']
        try:
            res = searchapp_model.get_api_response(host=host, website=self.website_id)
            if res and res.get('error'):
                raise UserError("%s" % res['error'])
            if res and not res.get('status'):
                raise UserError("%s" % res['message'])
        except UserError as e:
            raise UserError(e)

        raise UserError("SiteSearchApp Connection Test Succeeded!")
