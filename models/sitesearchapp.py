from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval
from datetime import datetime
from collections import OrderedDict
import requests

default_model_matrix = {
    'product': {'model': 'product.template', 'name_field': 'name', 'url_field': 'website_url'},
    'category': {'model': 'product.public.category', 'name_field': 'display_name',
                 'url_regex': '/shop/category/%s'},
    'blog': {'model': 'blog.post', 'name_field': 'name', 'url_field': 'website_url'}}


def split_seq(seq, size):
    newseq = []
    splitsize = 1.0 / size * len(seq)
    for i in range(size):
        newseq.append(seq[int(round(i * splitsize)):int(round((i + 1) * splitsize))])
    return newseq


class SiteSearchAppModel(models.Model):
    _name = 'searchapp.search'
    _description = "SiteSearchApp"
    _inherit = "website.multi.mixin"
    _order = 'sequence'

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Index Name')
    identifier = fields.Char('Identifier')
    sequence = fields.Integer('Position')
    attribute_ids = fields.Many2many('searchapp.search.attrib', string='Attributes')
    indexed_ids = fields.Text(string='Indexed IDs')
    index_date = fields.Datetime('Last Indexed Date')
    domain = fields.Char('Domain')
    model_id = fields.Many2one('ir.model', string='Model')
    model = fields.Char(related='model_id.model', string='Code', readonly=True)
    default_name = fields.Boolean('Use default Name', default=True)
    default_slug = fields.Boolean('Use default URL site key', default=True)
    name_field = fields.Many2one('ir.model.fields', string='Name field', domain="[('model_id','=',model_id)]",
                                 help='The primary name field of the record that will be indexed.')
    url_prefix = fields.Char('URL Prefix')
    url_field = fields.Many2one('ir.model.fields', string='URL field', domain="[('model_id','=',model_id)]",
                                help='The url field of the record. Can either be relative or absolute.')
    is_product = fields.Boolean('Product')
    pricelist_id = fields.Many2one('product.pricelist', string='Login Pricelist', help='Pricelist for logged-in users')
    public_pricelist_id = fields.Many2one('product.pricelist', string='Public Pricelist',
                                          help='Pricelist for public users')
    image_size = fields.Char('Image size', default='68x68')
    image_field = fields.Many2one('ir.model.fields', string='Image field', domain="[('model_id','=',model_id)]",
                                  help='The primary product image field.')
    variant_img = fields.Boolean('Use Product Variant Image',
                                 help='Use the product variant image as the primary image.')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    price_field = fields.Many2one('ir.model.fields', string='Price field', domain="[('model_id','=',model_id)]",
                                  help='The actual price field of the product.')
    slash_field = fields.Many2one('ir.model.fields', string='Price Slash field', domain="[('model_id','=',model_id)]",
                                  help='The slash price field of the product.')
    promo_field = fields.Many2one('ir.model.fields', string='Promo Identifier field',
                                  domain="[('model_id','=',model_id)]",
                                  help='A boolean field that identifies promo products. These products will appear on top of the search results.')
    hide_price = fields.Float('Hide Price Limit',
                              help='Hide the price from the search results if the price is less than or equal to the value set here.')
    avg_review = fields.Many2one('ir.model.fields', string='Average Review field', domain="[('model_id','=',model_id)]",
                                 help='A float field that contains the review average rating where zero (0) is the lowest and five (5) is the highest.')
    total_review = fields.Many2one('ir.model.fields', string='Total Review field', domain="[('model_id','=',model_id)]",
                                   help='A float or integer field that contains the total number of reviews on a product.')

    @api.onchange('default_name')
    def default_name_onchange(self):
        if self.default_name:
            self.name_field = None

    @api.onchange('default_slug')
    def default_slug_onchange(self):
        if self.default_slug:
            self.url_field = None

    @api.model
    def create(self, vals):
        identifier = vals.get('identifier')
        res = super(SiteSearchAppModel, self).create(vals)
        website = res.website_id
        if identifier in default_model_matrix.keys():
            model_defaults = default_model_matrix.get(identifier)
            if model_defaults:
                model = model_defaults.get('model')
                model_id = self.env['ir.model'].sudo().search([('model', '=', model)], limit=1)
                if model_id:
                    res.model_id = model_id.id
            if identifier in ['product', 'blog']:
                res.domain = "[[u'website_published', u'=', True],[u'website_id', u'=', u'%s']]" % website.name
                if identifier == 'product':
                    res.is_product = True
            else:
                res.domain = "[[u'website_id', u'=', u'%s']]" % website.name
        return res

    @api.model
    def get_api_response(self, host, data=None, website=None):
        IrParamSudo = self.env['ir.config_parameter'].sudo()
        web_base_url = IrParamSudo.get_param('web.base.url')
        web_base_url = website.domain or web_base_url
        if not website.ssa_enable:
            raise UserError("Please Enable SiteSearchApp!")

        headers = {'Content-type': 'application/json',
                   'x-api-key': website.ssa_api_key,
                   }
        if not data:
            data = {"username": website.ssa_user,
                    "password": website.ssa_password,
                    "website": web_base_url}
        try:
            request = requests.post(url=host, json=data, headers=headers)
            resp = request.json(object_pairs_hook=OrderedDict)
        except Exception as e:
            raise UserError("Error! Please check your settings. %s" % e)
        return resp

    @api.model
    def get_attribute_ids(self, attributes):
        attrib_model = self.env['searchapp.search.attrib']
        attrib_ids = []
        if attributes:
            for attrib in attributes:

                attrib_record = attrib_model.search([('name', '=', attrib)], limit=1)
                if attrib_record:
                    attrib_ids.append(attrib_record.id)
                else:
                    new_attrib_record = attrib_model.create({"name": attrib})
                    attrib_ids.append(new_attrib_record.id)
        return attrib_ids

    @api.model
    def get_index_record(self, identifier):
        return self.search([('identifier', '=', identifier)], limit=1)

    def delete_index(self, rec_ids=None):
        data_limit = 1000
        if not isinstance(rec_ids, list):
            rec_ids = None
        for rec in self:
            current_website = rec.website_id
            host = current_website.ssa_delete_api
            if not host:
                raise Exception("Delete Index API is not set.")
            if not rec.model_id:
                raise Exception("Model ID is not defined: %s" % rec.name)
            else:
                body_data = []
                if rec_ids:
                    body_data = rec_ids
                else:
                    model_id = self.env[rec.model_id.model]
                    try:
                        domain = []
                        if rec.domain:
                            domain = safe_eval(rec.domain)
                        model_records = model_id.search(domain or [])
                    except Exception as e:
                        raise e
                    for record in model_records:
                        body_data.append(record.id)

                data = []
                size = int(len(body_data) / data_limit)
                if size > 1:
                    data = split_seq(body_data, size)
                else:
                    data.append(body_data)
                for dta in data:
                    index_data = {"index": rec.identifier, "ids": dta}
                    try:
                        indexing_resp = self.get_api_response(host=host, data=index_data, website=current_website)
                        if indexing_resp.get('message') and not indexing_resp.get('status'):
                            raise indexing_resp.get('message')
                        rec.write({"index_date": datetime.now()})
                    except Exception as e:
                        raise e
        return True

    @api.model
    def get_indices(self, website=None):
        current_website = website or self.env['website'].get_current_website()
        host = current_website.ssa_indices_api
        if not host:
            raise Exception("Indices API endpoint not set.")
        try:
            res = self.get_api_response(host=host, website=current_website)
            if res and res.get('status'):
                items = res.get('result')
                for key, val in items.items():
                    item_title = val.get('title')
                    item_position = val.get('position')
                    item_identifier = val.get('identifier')
                    item_attributes = val.get('attributes', [])
                    item_attrib_ids = self.get_attribute_ids(item_attributes)
                    item_record = self.search([('name', '=', item_title), ('website_id', '=', current_website.id)],
                                              limit=1)
                    if item_record:
                        item_record.write({"sequence": item_position.isdigit() and int(item_position),
                                           "identifier": item_identifier,
                                           "attribute_ids": [(6, 0, item_attrib_ids)]})
                    else:
                        domain = {"active": True,
                                  "name": item_title,
                                  "website_id": current_website.id,
                                  "identifier": item_identifier,
                                  "sequence": item_position.isdigit() and int(item_position) or 0,
                                  "attribute_ids": [(6, 0, item_attrib_ids)]
                                  }
                        self.create(domain)
        except Exception as e:
            return e
        return True

    def index_record(self):
        self.ensure_one()
        self.index_site()

    def index_site(self):
        data_limit = 1000
        IrParamSudo = self.env['ir.config_parameter'].sudo()
        Website = self.env['website']

        for rec in self:
            current_website = rec.website_id
            host = current_website.ssa_index_api
            web_base_url = current_website.domain or IrParamSudo.get_param('web.base.url')

            if not host:
                raise Exception("Indexing API endpoint not set.")

            body_data = []
            if not rec.model_id:
                raise Exception("Model ID not defined: %s" % rec.name)
            else:
                model_id = self.env[rec.model_id.model]
                try:
                    domain = []
                    if rec.domain:
                        domain = safe_eval(rec.domain)
                    model_records = model_id.search(domain or [])
                except Exception as e:
                    raise e
                for record in model_records:
                    rec_id = record.id
                    rec_doc_terms = record.name.replace(" ", "")

                    rec_data = {"_id": rec_id,
                                "doc_id": rec_id,
                                "doc_terms": rec_doc_terms}

                    if not rec.default_name and rec.name_field:
                        rec_data.update({'name': getattr(record, rec.name_field.name)})

                    final_url = ''

                    if not rec.default_slug and rec.url_field:
                        url = str(getattr(record, rec.url_field.name))
                        final_url = '%s/%s' % (rec.url_prefix or '', url.lstrip('/'))
                    else:
                        identifier = default_model_matrix.get(rec.identifier)
                        url_regex = identifier and identifier.get('url_regex')
                        url_field = identifier and identifier.get('url_field')
                        if url_regex:
                            final_url = url_regex % rec_id
                        if url_field:
                            final_url = getattr(record, url_field)

                    if final_url:
                        if final_url.startswith('/') or final_url.startswith('http'):
                            rec_data.update({'url': final_url})
                        else:
                            rec_data.update({'url': '/%s' % final_url})

                    if rec.is_product:
                        img_url, price, login_price, price_slash = '', '', '', ''
                        rating, rating_count = 0.0, 0
                        currency_symbol = '$'
                        hide_price, promo = 'no', 'no'
                        img_size = rec.image_size or '68x68'
                        rec_img = rec.image_field and rec.image_field.name or 'image_1920'
                        rec_rating = rec.avg_review
                        variant_img = rec.variant_img
                        rec_slash_field = rec.slash_field
                        price_field_field = rec.price_field and rec.price_field.name or 'list_price'
                        hide_price_limit = rec.hide_price
                        pricelist_id = rec.pricelist_id
                        public_pricelist_id = rec.public_pricelist_id
                        rec_rating_count = rec.total_review
                        rec_currency = rec.currency_id
                        rec_promo = rec.promo_field

                        if rec_currency:
                            currency_symbol = rec_currency.symbol
                        if price_field_field:
                            price_res = getattr(record, price_field_field)
                            if price_res:
                                price = '{:,.2f}'.format(price_res)
                                if hide_price_limit and price_res <= hide_price_limit:
                                    price = ''
                        if public_pricelist_id:
                            public_price_res = record._get_combination_info(only_template=True,
                                                                            pricelist=public_pricelist_id)
                            if public_price_res:
                                price = '{:,.2f}'.format(public_price_res['price'])
                        if pricelist_id:
                            login_price_res = record._get_combination_info(only_template=True, pricelist=pricelist_id)
                            if login_price_res:
                                login_price = '{:,.2f}'.format(login_price_res['price'])
                        if rec_slash_field:
                            slash_res = getattr(record, rec_slash_field.name)
                            if slash_res:
                                price_slash = '{:,.2f}'.format(slash_res)
                        if rec_img and img_size:
                            image_url = Website.image_url(record=record, field=rec_img, size=img_size)
                            if variant_img and hasattr(record, 'product_variant_ids'):
                                v_ids = record.product_variant_ids
                                if v_ids:
                                    image_url = Website.image_url(record=v_ids[0], field=rec_img, size=img_size)
                            img_url = '%s%s' % (web_base_url.rstrip('/'), image_url)
                        if rec_promo:
                            is_promo = getattr(record, rec_promo.name)
                            promo = is_promo and 'yes' or 'no'
                        if rec_rating:
                            rating = getattr(record, rec_rating.name)
                        if rec_rating_count:
                            rating_count = getattr(record, rec_rating_count.name)

                        rec_data.update({'image_url': img_url,
                                         'currency': currency_symbol,
                                         'price': price,
                                         'login_price': login_price,
                                         'price_slash': price_slash,
                                         'promo': promo and 'yes' or 'no',
                                         'hide_price': hide_price,
                                         'rating': rating,
                                         'rating_count': rating_count})

                    for attrib in rec.attribute_ids:
                        attr = attrib.name
                        if attr not in rec_data.keys() and hasattr(record, attr):
                            rec_data[attr] = getattr(record, attr)
                    body_data.append(rec_data)

                data = []
                size = int(len(body_data) / data_limit)
                if size > 1:
                    data = split_seq(body_data, size)
                else:
                    data.append(body_data)

                indexed_ids = []
                for dta in data:
                    index_data = {"type": rec.identifier, "body": dta}
                    try:
                        indexing_resp = self.get_api_response(host=host, data=index_data, website=current_website)
                        if indexing_resp.get('message') and not indexing_resp.get('status'):
                            raise Exception("Indexing Failed: %s" % indexing_resp.get('message'))
                        indx_ids = [x.get('_id') for x in dta]
                        indexed_ids += indx_ids
                        rec.write({"index_date": datetime.now()})
                    except Exception as e:
                        raise e

                if indexed_ids:
                    try:
                        old_indexed_ids = rec.indexed_ids and eval(rec.indexed_ids)
                        obsolete_ids = old_indexed_ids and set(old_indexed_ids) - set(indexed_ids)
                        if obsolete_ids:
                            rec.delete_index(rec_ids=list(obsolete_ids))
                        rec.write({'indexed_ids': str(indexed_ids)})
                    except Exception as e:
                        raise e

        return True

    @api.model
    def searchapp_scheduler(self):
        for rec in self.search([]):
            rec.index_site()
        return True


class SiteSearchAppAttrib(models.Model):
    _name = 'searchapp.search.attrib'
    _description = "SiteSearchApp Attributes"

    name = fields.Char('Attribute Name')
