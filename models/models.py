from odoo import api, models


class BaseModelExtend(models.AbstractModel):
    _name = 'basemodel.extend'
    _description = 'Base Model Extension'

    def _register_hook(self):

        @api.model
        def _ordered_search(self, args, offset=0, limit=None, array=None, order=None, count=False,
                            access_rights_uid=None):
            self.with_user(access_rights_uid or self._uid).check_access_rights('read')

            if expression.is_false(self, args):
                # optimization: no need to query, as no record satisfies the domain
                return 0 if count else []

            query = self._where_calc(args)
            self._apply_ir_rules(query, 'read')
            if array:
                order_by = 'ORDER BY array_position(ARRAY%s, "%s"."id")' % (array, self._table)
            else:
                order_by = self._generate_order_by(order, query)
            from_clause, where_clause, where_clause_params = query.get_sql()
            where_str = where_clause and (" WHERE %s" % where_clause) or ''

            if count:
                # Ignore order, limit and offset when just counting, they don't make sense and could
                # hurt performance
                query_str = 'SELECT count(1) FROM ' + from_clause + where_str
                self._cr.execute(query_str, where_clause_params)
                res = self._cr.fetchone()
                return res[0]

            limit_str = limit and ' limit %d' % limit or ''
            offset_str = offset and ' offset %d' % offset or ''
            query_str = 'SELECT "%s".id FROM ' % self._table + from_clause + where_str + order_by + limit_str + offset_str
            self._cr.execute(query_str, where_clause_params)
            res = self._cr.fetchall()

            # TDE note: with auto_join, we could have several lines about the same result
            # i.e. a lead with several unread messages; we uniquify the result using
            # a fast way to do it while preserving order (http://www.peterbe.com/plog/uniqifiers-benchmark)
            def _uniquify_list(seq):
                seen = set()
                return [x for x in seq if x not in seen and not seen.add(x)]

            return _uniquify_list([x[0] for x in res])

        @api.model
        @api.returns('self',
                     upgrade=lambda self, value, args, offset=0, limit=None, order=None,
                                    count=False: value if count else self.browse(value),
                     downgrade=lambda self, value, args, offset=0, limit=None, order=None,
                                      count=False: value if count else value.ids)
        def ordered_search(self, args, offset=0, limit=None, array=None, order=None, count=False):
            """Ordered Search: Keeping Ids sorted in preformat manner:
                https://gist.github.com/cpjolicoeur/3590737#gistcomment-2222109
            """
            res = self._ordered_search(args, offset=offset, limit=limit, array=array, order=order, count=count)
            return res if count else self.browse(res)

        models.AbstractModel._ordered_search = _ordered_search
        models.AbstractModel.ordered_search = ordered_search
        return super(BaseModelExtend, self)._register_hook()


from odoo.osv import expression
