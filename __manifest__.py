{
    "name": "ml_import",
    "summary": """
        ML Import
        """,
    "description": """
    """,
    "category": "Sales",
    "version": "17.0.1.0",
    # any module necessary for this one to work correctly
    "depends": ["sale","product","l10n_ar","sale_management"],
    # always loaded
    "data": [
        "sale_view.xml",
        "security/ir.model.access.csv"
    ],
    'license': 'LGPL-3',
}
