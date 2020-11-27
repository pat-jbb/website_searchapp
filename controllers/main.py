from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale.controllers.main import TableCompute
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.http_routing.models.ir_http import slug
from ..models.sitesearchapp import default_model_matrix

PPG = 18
PPR = 4


def _uniquify_list(seq):
    seen = set()
    return [x for x in seq if x not in seen and not seen.add(x)]


class SiteSearchAppController(http.Controller):

    @http.route('/searchapp/index/', type='json', auth='public', methods=['POST'], website=True, csrf=False)
    def searchapp_index(self, q):
        current_website = request.website
        host = current_website.ssa_search_api
        searchapp_search = request.env['searchapp.search'].sudo()
        try:
            res = searchapp_search.get_api_response(host=host, data={'query': q}, website=current_website)
        except Exception as e:
            return e
        return res

    @http.route('/searchapp/index/query', type='json', auth='public', methods=['POST'], website=True, csrf=False)
    def searchapp_querylog(self, q, idx_count):
        current_website = request.website
        host = current_website.ssa_log_api
        ip_whitelist = current_website.ssa_ip_whitelist or []
        searchapp_search = request.env['searchapp.search'].sudo()

        try:
            email = ''
            user_name = ''
            session_id = request.session.sid
            current_user = request.env.user
            http_env = request.httprequest.environ
            ip = http_env.get('HTTP_X_REAL_IP', http_env.get('HTTP_X_FORWARDED_FOR', http_env['REMOTE_ADDR']))
            whitelisted_ips = ip_whitelist and ip_whitelist.replace(' ', '').split(',')
            if ip not in whitelisted_ips:
                if current_user:
                    partner_id = current_user.partner_id
                    if partner_id:
                        user_name = partner_id.name or ''
                        email = partner_id.email or ''

                latest_order = request.session.sale_order_id or request.session.sale_last_order_id
                if latest_order:
                    order_id = request.env['sale.order'].sudo().browse(latest_order)
                    if order_id:
                        user_name = order_id.partner_id.name or ''
                        email = order_id.partner_id.email or ''

                data = {'query': q,
                        'ip': ip,
                        'session_id': session_id,
                        'user': user_name != 'Public user' and user_name or '',
                        'email': email,
                        'results': idx_count}

                searchapp_search.get_api_response(host=host, data=data, website=current_website)
        except Exception:
            return False
        return True

    @http.route([
        '''/search''',
        '''/search/page/<int:page>'''
    ], type='http', auth="public", website=True)
    def searchapp_page(self, page=0, q='', index='', search='', ppg=False, **post):
        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG

        domain = WebsiteSale()._get_search_domain(search, category=None, attrib_values=None)
        product_model = 'product.template'
        res_ids = []
        model = None
        indices = None
        searchapp_model = request.env['searchapp.search'].sudo()

        def _get_active_index(indcs):
            active_list = []
            for k, val in indcs.items():
                if val.get('hits', {}).get('total'):
                    active_list.append(k)
            return active_list

        if q:
            search = q
            searchapp_search = request.env['searchapp.search'].sudo()
            current_website = request.website
            host = current_website.ssa_documents_api
            indices_host = current_website.ssa_search_api

            try:
                indices = searchapp_model.get_api_response(host=indices_host, data={'query': search},
                                                           website=current_website)
                active_indices = _get_active_index(indices.get('results'))
                if not index:
                    if 'product' in active_indices:
                        index = 'product'
                    else:
                        if len(active_indices) >= 1:
                            index = active_indices[0]

                data = {'index': index,
                        'from': 0,
                        'limit': 2000,
                        'query': q}
                res = searchapp_search.get_api_response(host=host, data=data, website=current_website)
                if res:
                    results = res.get('results')
                    for key, res in results.items():
                        searchapp_id = searchapp_model.get_index_record(key)
                        is_product = searchapp_id and searchapp_id.is_product
                        hits = res.get('hits')
                        results = hits and hits.get('hits')
                        if results:
                            res_ids = [int(res['_id']) for res in results]
                            domain = [('id', 'in', res_ids)]
                            model = searchapp_id.model_id.model
                            if is_product:
                                product_model = model

            except Exception:
                pass

        keep = QueryURL('/search', q=q, index=index, order=post.get('order'))
        pricelist_context, pricelist = WebsiteSale()._get_pricelist_context()
        request.context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)

        url = "/search"
        if q:
            post["q"] = q

        values = {'pager': {'page_count': 0}}

        if index == 'product':
            Product = request.env[product_model].with_context(bin_size=True)
            product_count = Product.search_count(domain)
            pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
            array = None
            if not post.get('order'):
                array = res_ids
            products = Product.ordered_search(domain, limit=ppg, offset=pager['offset'], array=array,
                                              order=WebsiteSale()._get_search_order(post))

            values.update({
                'pager': pager,
                'pricelist': pricelist,
                'products': products,
                'search_count': product_count,
                'bins': TableCompute().process(products, ppg),
            })

        if index and index != 'product':
            data_model = request.env[model]
            data_count = data_model.search_count(domain)
            pager = request.website.pager(url=url, total=data_count, page=page, step=ppg, scope=7, url_args=post)
            array = None
            if not post.get('order'):
                array = res_ids
            search_data = data_model.ordered_search(domain, limit=ppg, array=array, offset=pager['offset'])

            if index == 'blog':
                values['slug'] = slug

            searchapp_id = searchapp_model.get_index_record(index)
            identifier = default_model_matrix.get(index)
            url_regex, url_field, name_field = '', '', ''
            if searchapp_id:
                if searchapp_id.default_name:
                    name_field = identifier and identifier.get('name_field')
                else:
                    name_field = searchapp_id.name_field.name

                if searchapp_id.default_slug:
                    url_field = identifier and identifier.get('url_field')
                    url_regex = identifier and identifier.get('url_regex')
                else:
                    url_field = searchapp_id.url_field.name

            values.update({
                'name_field': name_field,
                'url_regex': url_regex,
                'url_field': url_field,
                'pager': pager,
                'search_data': search_data,
                'search_count': data_count,
                'bins': [[]],
            })

        layout_mode = request.session.get('website_sale_shop_layout_mode')
        if not layout_mode:
            if request.website.viewref('website_sale.products_list_view').active:
                layout_mode = 'list'
            else:
                layout_mode = 'grid'

        values.update({
            'active_index': index,
            'search_indices': indices,
            'search': search,
            'rows': PPR,
            'keep': keep,
            'noindex_nofollow': True,
            'layout_mode': layout_mode,
            'additional_title': "Search Results for %s" % search,
        })

        return request.render("website_sale.products", values)
