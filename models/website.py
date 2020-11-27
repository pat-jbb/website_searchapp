from odoo import models, api, fields


class SiteSearchAppWebsite(models.Model):
    _inherit = 'website'

    ssa_enable = fields.Boolean('SiteSearchApp Enable', default=True)
    ssa_host = fields.Char('SiteSearchApp Host')
    ssa_user = fields.Char('SiteSearchApp User')
    ssa_api_key = fields.Char('SiteSearchApp API Key')
    ssa_password = fields.Char('SiteSearchApp Password')
    ssa_log_api = fields.Char("SiteSearchApp Log API", compute='_update_ssa_endpoints')
    ssa_test_api = fields.Char("SiteSearchApp Test API", compute='_update_ssa_endpoints')
    ssa_index_api = fields.Char("SiteSearchApp Index API", compute='_update_ssa_endpoints')
    ssa_delete_api = fields.Char("SiteSearchApp Delete API", compute='_update_ssa_endpoints')
    ssa_search_api = fields.Char("SiteSearchApp Search API", compute='_update_ssa_endpoints')
    ssa_indices_api = fields.Char("SiteSearchApp Indices API", compute='_update_ssa_endpoints')
    ssa_documents_api = fields.Char("SiteSearchApp Documents API", compute='_update_ssa_endpoints')
    ssa_alignment = fields.Selection([('left', 'Left'), ('center', 'Center'), ('right', 'Right')],
                                     'SiteSearchApp Alignment', default='right')
    ssa_ip_whitelist = fields.Char('Whitelist IP',
                                   help="Comma-separated list of IP Addresses excluded from search logs.")
    ssa_text_color = fields.Char('SiteSearchApp Text Color', default='#333333')
    ssa_title_color = fields.Char('SiteSearchApp Title Color', default='#333333')
    ssa_price_color = fields.Char('SiteSearchApp Price Color', default='#333333')
    ssa_border_color = fields.Char('SiteSearchApp Border Color', default='transparent')
    ssa_loader_color = fields.Char('SiteSearchApp Loader Color', default='#B6BD34')
    ssa_slash_color = fields.Char('SiteSearchApp Price Slash Color', default='#333333')
    ssa_highlight_color = fields.Char('SiteSearchApp Highlight Color', default='#000000')
    ssa_hover_color = fields.Char('SiteSearchApp Hover Background Color', default='#EEEEEE')
    ssa_bg_color = fields.Char('SiteSearchApp Container Background Color', default='#FFFFFF')
    ssa_title_bg_color = fields.Char('SiteSearchApp Title Background Color', default='#CECECE')
    ssa_custom_css = fields.Text('SiteSearchApp Custom CSS', help="Create custom css styles. Paste your code here.")

    @api.depends('ssa_host')
    def _update_ssa_endpoints(self):
        for website in self:
            website.ssa_log_api = ''
            website.ssa_test_api = ''
            website.ssa_index_api = ''
            website.ssa_delete_api = ''
            website.ssa_search_api = ''
            website.ssa_indices_api = ''
            website.ssa_documents_api = ''
            if website.ssa_host:
                ssa_host = website.ssa_host.rstrip('/')
                website.ssa_log_api = "%s/%s" % (ssa_host, 'api/querylog')
                website.ssa_test_api = "%s/%s" % (ssa_host, 'api/check')
                website.ssa_index_api = "%s/%s" % (ssa_host, 'api/index')
                website.ssa_delete_api = "%s/%s" % (ssa_host, 'api/delete')
                website.ssa_search_api = "%s/%s" % (ssa_host, 'api/search')
                website.ssa_indices_api = "%s/%s" % (ssa_host, 'api/indices')
                website.ssa_documents_api = "%s/%s" % (ssa_host, 'api/index-ids')

    @api.model
    def get_searchapp_styles(self):
        current_website = self.get_current_website()
        style_alignment = ''
        custom_css = current_website.ssa_custom_css or ''

        if current_website.ssa_alignment == 'center':
            style_alignment = '''#search_autocomplete .search-autocomplete {
                                             left: 50% !important;
                                            -moz-transform: translate(-50%, 0) !important;
                                            -ms-transform: translate(-50%, 0) !important;
                                            -webkit-transform: translate(-50%, 0) !important;
                                            transform: translate(-50%, 0) !important;
                                            }'''

        if current_website.ssa_alignment == 'left':
            style_alignment = '''#search_autocomplete .search-autocomplete {
                                            left: 0 !important;
                                            }'''

        style = '''
                    #search_autocomplete .search-autocomplete{
                        border: 1px solid %s !important;
                        background-color: %s !important;
                    }
                    #search_autocomplete .search-title{
                        background-color: %s !important;
                    }
                    #search_autocomplete .search-results-list li:not(.no-results):hover{
                        background-color: %s !important;
                    }
                    #search_autocomplete #search-loader .lds-ellipsis div{
                        background: %s !important;
                    }
                    #search_autocomplete .search-title{
                        color: %s !important;
                    }
                    #search_autocomplete .search-results-list .price-container .price{
                        color: %s !important;
                    }
                    #search_autocomplete .search-results-list .product-placeholder .p-desc{
                        color: %s !important;
                    }
                    #search_autocomplete .search-results-list .price-container .price-slash{
                        color: %s !important;
                    }
                    #search_autocomplete .search-results-list .highlight{
                        color: %s !important;
                    }
                    %s
                    %s
                    ''' % (current_website.ssa_border_color, current_website.ssa_bg_color,
                           current_website.ssa_title_bg_color, current_website.ssa_hover_color,
                           current_website.ssa_loader_color, current_website.ssa_title_color,
                           current_website.ssa_price_color, current_website.ssa_text_color,
                           current_website.ssa_slash_color, current_website.ssa_highlight_color,
                           custom_css, style_alignment)
        return style
