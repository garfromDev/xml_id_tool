# -*- coding: utf8 -*-
#
# Copyright (C) 2014 NDP Systèmes (<http://www.ndp-systemes.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

{
    'name': 'Logistique SIRAIL',
    'version': '0.1',
    'author': 'NDP Systèmes',
    'maintainer': 'NDP Systèmes',
    'category': 'Technical Settings',
    'depends': ['sirail_materialized_sql_views', 'sirail_qualite'],
    'description': """
Logistique SIRAIL
-----------------
Ce module comprend les modifications réalisées pour l'ERP SIRAIL dans le domaine de la logistique.
""",
    'website': 'http://www.ndp-systemes.fr',
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'report/rapport_sirail_logistique.xml',
        'data/data.xml',
        'data/mail_templates.xml',
        'data/automation.xml',
        'data/scripts.xml',
        'views/sirail_logistique.xml',
        'views/sirail_evo_stock.xml',
        'views/sirail_dead_inventory.xml',
        'views/stock.xml',
        'views/procurement.xml',
        'views/procurement_backlog.xml',
        'views/procurement_backlog_wizard.xml',
        'views/inventaire.xml',
        'views/product.xml',
        'views/coherence_regles_reassort.xml',
        'views/demande_transfert.xml',
        'views/res_config.xml',
        'views/sirail_imports.xml',
        'views/sirail_import_supplierinfo.xml',
        'wizard/stock_inventory_views.xml',
        'wizard/stock_move_scrap_views.xml',
        'wizard/stock_transfer_details_views.xml',
        'wizard/stock_mvt_prod_rebut.xml',
        'wizard/stock_moving_wizard.xml',
    ],
    'demo': [
        'tests/sirail_logistique_demo.xml',
        'tests/import_article_test.xml'
    ],
    'installable': True,
    'auto_install': False,
    'license': 'AGPL-3',
    'application': False,
}
