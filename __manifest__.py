{
    "name": "pos_inv_other_company",
    "summary": """
        POS inv other company
        """,
    "description": """
    """,
    "category": "Point of Sale",
    "version": "17.0.1.0",
    # any module necessary for this one to work correctly
    "depends": ["sale","account","point_of_sale","pos_order_to_sale_order"],
    # always loaded
    "data": [
        "views/res_config_settings_view.xml",
    ],
    'license': 'LGPL-3',
}
