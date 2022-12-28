# -*- coding: utf-8 -*-
{
    'name': "HR PAYROLL MXN",

    'summary': """
        Modulo para el timbradode Nomina mexicana para odoo12 enterprise""",

    'description': """
        Nomina MXN
    """,

    'author': "Xmarts",
    'collaborators': 'BIOFHE',
    'website': "xmarts.com",

    'category': 'Account',
    'version': '0.2',

    # any module necessary for this one to work correctly
    'depends': ['base', 'resource', 'hr_attendance', 'hr_payroll', 'hr_expense_extract', 'hr_work_entry_contract', 'account',
                'hr_expense'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/hr_contract.xml',
        'views/hr_employee.xml',
        'views/hr_imss_table.xml',
        'views/hr_salary_rule.xml',
        'views/hr_payroll.xml',
        'views/hr_payroll_structure.xml',
        'views/hr_payslip.xml',
        'views/hr_payslip_type.xml',
        'views/overtime_type.xml',
        'views/res_company_view.xml',
        'views/resource_calendar.xml',
        'views/salary_payment_type.xml',
        'views/hr_payslip_report.xml',
        'views/res_config_view.xml',
        'views/hr_salary_rule_web_view.xml',
        # vista de hr_payroll_account
        'views/hr_payroll_account_view.xml',
        'data/hr_contract_type_data.xml',
        'data/hr_factor_integration_data.xml',
        'data/hr_payroll_data.xml',
        'data/hr_payroll_imss_data.xml',
        'data/hr_payslip_type_data.xml',
        'data/hr_salary_rule_category.xml',
        'data/isr_table_type_data.xml',
        # 'data/l10n_mx_hr_ausent_data.xml',
        'data/l10n_mx_hr_incapacity_data.xml',
        'data/l10n_mx_hr_reset_work_data.xml',
        'data/overtime_type_data.xml',
        'data/regimen_employee_data.xml',
        'data/resource_calendar_type_data.xml',
        'data/resource_calendar_data.xml',
        'data/since_risk_data.xml',
        'data/salary_payment_type_data.xml',
        'data/planned_actions_rules_web.xml',
        # This must be at the end because use the data from previous files
        # 'data/catalogo_TipoPercepcion.xml',
        # 'data/catalogo_OtrosPagos.xml',
        # 'data/catalogo_TipoDeduccion.xml',
        # 'data/catalogo_TipoRetenciones.xml',
        # 'data/catalogo_Obligaciones.xml',
        # 'data/hr_payroll_structure_data.xml',
        'data/hr_payroll_isr_data.xml',
        'data/hr_payroll_isr_subcidio_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
        # 'demo/hr_payroll_account_demo.xml',
    ],
}
