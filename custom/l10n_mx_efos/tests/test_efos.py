from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestEFOS(TransactionCase):
    def setUp(self):
        super(TestEFOS, self).setUp()
        self.partner = self.env["l10n_mx.efos"].create(
            [
                {
                    "name": "Favorable 1",
                    "rfc": "FAV1",
                    "state": "favorable",
                },
                {
                    "name": "Distorted 1",
                    "rfc": "DIS1",
                    "state": "distorted",
                },
                {
                    "name": "Definitive 1",
                    "rfc": "DEF1",
                    "state": "definitive",
                },
                {
                    "name": "Presumed 1",
                    "rfc": "PRE1",
                    "state": "presumed",
                },
                {
                    "name": "Favorable 2",
                    "rfc": "FAV2",
                    "state": "favorable",
                },
                {
                    "name": "Distorted 2",
                    "rfc": "DIS2",
                    "state": "distorted",
                },
                {
                    "name": "Definitive 2",
                    "rfc": "DEF2",
                    "state": "definitive",
                },
                {
                    "name": "Presumed 2",
                    "rfc": "PRE2",
                    "state": "presumed",
                },
            ]
        )

    def test_partner_in_efos_favorable(self):
        """
        Test if the partner is in the efos favorable list
        """
        partner = self.env["res.partner"].create(
            {
                "name": "Test",
                "email": "test",
                "vat": "FAV1",
            }
        )
        self.assertEqual(partner.sat_efos_state, "favorable")

    def test_partner_in_efos_distorted(self):
        """
        Test if the partner is in the efos distorted list
        """
        partner = self.env["res.partner"].create(
            {
                "name": "Test",
                "email": "test",
                "vat": "DIS1",
            }
        )
        self.assertEqual(partner.sat_efos_state, "distorted")

    def test_partner_in_efos_definitive(self):
        """
        Test if the partner is in the efos definitive list
        """
        partner = self.env["res.partner"].create(
            {
                "name": "Test",
                "email": "test",
                "vat": "DEF1",
            }
        )
        self.assertEqual(partner.sat_efos_state, "definitive")

    def test_partner_in_efos_presumed(self):
        """
        Test if the partner is in the efos presumed list
        """
        partner = self.env["res.partner"].create(
            {
                "name": "Test",
                "email": "test",
                "vat": "PRE1",
            }
        )
        self.assertEqual(partner.sat_efos_state, "presumed")

    def test_partner_in_efos_danger(self):
        """
        Test if the partner is in the efos presumed list
        """
        partner = self.env["res.partner"].create(
            {
                "name": "Test",
                "email": "test",
                "vat": "DIS1",
            }
        )
        self.assertFalse(partner.sat_efos_danger)

    def test_partner_not_in_efos_danger(self):
        """
        Test if the partner is in the efos presumed list
        """
        partner = self.env["res.partner"].create(
            {
                "name": "Test",
                "email": "test",
                "vat": "PRE1",
            }
        )
        self.assertTrue(partner.sat_efos_danger)

    def test_partner_not_in_efos(self):
        """
        Test if the partner is in the efos presumed list
        """
        partner = self.env["res.partner"].create(
            {
                "name": "Test",
                "email": "test",
                "vat": "OTH1",
            }
        )
        self.assertEqual(partner.sat_efos_state, "unknown")

    @patch("odoo.addons.l10n_mx_efos.models.l10n_mx_efos.requests.get")
    def test_download_sat_file(self, mock_get):
        """
        Test if can download the SAT CSV file
        """
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b'Informaci\xf3n actualizada al 17 de septiembre de 2021,,,,,,,,,,,,,,,,,,,\r\nListado completo de contribuyentes (Art\xedculo 69-B del CFF),,,,,,,,,,,,,,,,,,,\r\nNo,RFC,Nombre del Contribuyente,Situaci\xf3n del contribuyente,N\xfamero y fecha de oficio global de presunci\xf3n SAT,Publicaci\xf3n p\xe1gina SAT presuntos,N\xfamero y fecha de oficio global de presunci\xf3n DOF,Publicaci\xf3n DOF presuntos,N\xfamero y fecha de oficio global de contribuyentes que desvirtuaron SAT,Publicaci\xf3n p\xe1gina SAT desvirtuados,N\xfamero y fecha de oficio global de contribuyentes que desvirtuaron DOF,Publicaci\xf3n DOF desvirtuados,N\xfamero y fecha de oficio global de definitivos SAT,Publicaci\xf3n p\xe1gina SAT definitivos,N\xfamero y fecha de oficio global de definitivos DOF,Publicaci\xf3n DOF definitivos,N\xfamero y fecha de oficio global de sentencia favorable SAT,Publicaci\xf3n p\xe1gina SAT sentencia favorable,N\xfamero y fecha de oficio global de sentencia favorable DOF,Publicaci\xf3n DOF sentencia favorable\r\n1,AAA080808HL8,"ASESORES EN AVAL\xdaOS Y ACTIVOS, S.A. DE C.V.",Sentencia Favorable,500-05-2018-16632 de fecha 01 de junio de 2018,01/06/2018,500-05-2018-16632 de fecha 01 de junio de 2018,25/06/2018,,,,,500-05-2018-27105 de fecha 27 de septiembre de 2018,28/09/2018,500-05-2018-27105 de fecha 27 de septiembre de 2018,23/10/2018,500-05-2019-7305 de fecha 5 de marzo de 2019,05/03/2019,500-05-2019-7305 de fecha 5 de marzo de 2019,16/04/2019\r\n2,AAA091014835,"AQUAERIS ACUACULTURA Y ARQUITECTURA SUSTENTABLE, S.C.",Desvirtuado,500-05-2016-38728 de fecha 16 de diciembre de 2016,01/01/2017,500-05-2016-38728 de fecha 16 de diciembre de 2016,19/01/2017,500-05-2017-38533 de fecha 13 de octubre de 2017,13/10/2017,500-05-2017-38533 de fecha 13 de octubre de 2017,02/11/2017,,,,,,,,\r\n3,AAA100303L51,"INGENIOS SANTOS, S.A. DE C.V.",Desvirtuado,500-05-2017-38736 de fecha 01 de diciembre de 2017,01/12/2017,500-05-2017-38736 de fecha 01 de diciembre de 2017,26/12/2017,500-05-2018-27096 de fecha 25 de septiembre de 2018,26/09/2018,500-05-2018-27096 de fecha 25 de septiembre de 2018,23/10/2018,,,,,,,,\r\n4,AAA120730823,"ASESORES Y ADMINISTRADORES AGRICOLAS, S. DE R.L. DE C.V.",Definitivo,500-05-2016-38728 de fecha 16 de diciembre de 2016,01/01/2017,500-05-2016-38728 de fecha 16 de diciembre de 2016,19/01/2017,,,,,500-05-2018-14172 de fecha 25 de mayo de 2018,25/05/2018,500-05-2018-14172 de fecha 25 de mayo de 2018,28/06/2018,,,,\r\n5,AAA121206EV5,"AM\xc9RICA ADMINISTRATIVA ARROLLO, S.A. DE CV.",Definitivo,500-05-2019-7349 de fecha 1 de abril de 2019,01/04/2019,500-05-2019-7349 de fecha 1 de abril de 2019,26/04/2019,,,,,500-05-2019-35911 de fecha 25 de octubre de 2019,25/10/2019,500-05-2019-35911 de fecha 25 de octubre de 2019,20/11/2019,,,,\r\n6,AAA140116926,"AVALOS & ASOCIADOS CONSULTORIA INTEGRAL, S.C.",Definitivo,500-05-2020-23758 de fecha 03 de noviembre de 2020,03/11/2020,500-05-2020-23758 de fecha 03 de noviembre de 2020,18/11/2020,,,,,500-05-2021-6937 de fecha 26 de abril de 2021,26/04/2021,500-05-2021-6937 de fecha 26 de abril de 2021,13/05/2021,,,,\r\n7,AAA1502061S0,"ACUESY ASESOR\xcdA ACUICOLA ESPECIALIZADA DE YUCAT\xc1N, S.A. DE C.V.",Sentencia Favorable,500-05-2017-32156 de fecha 18 de septiembre de 2017,18/09/2017,500-05-2017-32156 de fecha 18 de septiembre de 2017,20/10/2017,,,,,500-05-2018-8169 de fecha 16 de marzo de 2018,16/03/2018,500-05-2018-8169 de fecha 16 de marzo de 2018,16/04/2018,500-05-2021-17861 de fecha 9 de agosto de 2021,09/08/2021,500-05-2021-17861 de fecha 9 de agosto de 2021,31/08/2021\r\n8,AAA151209DYA,"AYC ADMINISTRACION Y ASESORIA COMERCIAL, S.A. DE C.V.",Definitivo,500-05-2020-13588 de fecha 15 de mayo de 2020,15/05/2020,500-05-2020-13588 de fecha 15 de mayo de 2020,29/06/2020,,,,,500-05-2020-28709 de fecha 25 de noviembre de 2020,25/11/2020,500-05-2021-5055 de fecha 9 de febrero de 2021,22/02/2021,,,,\r\n9,AAAA620217U54,AMADOR AQUINO JOS\xc9 AVENAMAR,Definitivo,500-05-2017-16140 de fecha 1 de junio de 2017,01/06/2017,500-05-2017-16140 de fecha 12 de junio de 2017,12/06/2017,,,,,500-05-2018-32751 de fecha 23 de noviembre de 2018,23/11/2018,500-05-2018-32751 de fecha 23 de noviembre de 2018,31/12/2018,,,,\r\n10,AAAE910314EJ7,ALVARADO ALMARAZ ESTEBAN JACOB,Definitivo,500-05-2020-13956 de fecha 01 de septiembre de 2020 ,01/09/2020,500-05-2020-13956 de fecha 01 de septiembre de 2020 ,18/09/2020,,,,,500-05-2021-5205 de fecha 3 de marzo de 2021,03/03/2021,500-05-2021-5205 de fecha 3 de marzo de 2021,22/03/2021,,,,\r\n'  # noqa: E501 pylint: disable=line-too-long
        data = self.env["l10n_mx.efos"]._download_sat_csv()  # pylint: disable=protected-access
        self.assertEqual(len(list(data)), 10)

    @patch("odoo.addons.l10n_mx_efos.models.l10n_mx_efos.requests.get")
    def test_download_sat_file_fail(self, mock_get):
        """
        Test if can download the SAT CSV file
        """
        mock_get.return_value.status_code = 400
        with self.assertRaises(UserError):
            self.env["l10n_mx.efos"]._download_sat_csv()  # pylint: disable=protected-access

    @patch("odoo.addons.l10n_mx_efos.models.l10n_mx_efos.EFOS._download_sat_csv")
    def test_parse_sat_file(self, mock_data):
        """
        Test if can parse the SAT CSV file
        """
        mock_data.return_value = [
            [
                "1",
                "AAA080808HL8",
                "ASESORES EN AVALÚOS Y ACTIVOS, S.A. DE C.V.",
                "Sentencia Favorable",
                "500-05-2018-16632 de fecha 01 de junio de 2018",
                "01/06/2018",
                "500-05-2018-16632 de fecha 01 de junio de 2018",
                "25/06/2018",
                "",
                ...,
            ],
            [
                "2",
                "AAA091014835",
                "AQUAERIS ACUACULTURA Y ARQUITECTURA SUSTENTABLE, S.C.",
                "Desvirtuado",
                "500-05-2016-38728 de fecha 16 de diciembre de 2016",
                "01/01/2017",
                "500-05-2016-38728 de fecha 16 de diciembre de 2016",
                "19/01/2017",
                "500-05-2017-38533 de fecha 13 de octubre de 2017",
                ...,
            ],
            [
                "3",
                "AAA100303L51",
                "INGENIOS SANTOS, S.A. DE C.V.",
                "Desvirtuado",
                "500-05-2017-38736 de fecha 01 de diciembre de 2017",
                "01/12/2017",
                "500-05-2017-38736 de fecha 01 de diciembre de 2017",
                "26/12/2017",
                "500-05-2018-27096 de fecha 25 de septiembre de 2018",
                ...,
            ],
            [
                "4",
                "AAA120730823",
                "ASESORES Y ADMINISTRADORES AGRICOLAS, S. DE R.L. DE C.V.",
                "Definitivo",
                "500-05-2016-38728 de fecha 16 de diciembre de 2016",
                "01/01/2017",
                "500-05-2016-38728 de fecha 16 de diciembre de 2016",
                "19/01/2017",
                "",
                ...,
            ],
            [
                "5",
                "AAA121206EV5",
                "AMÉRICA ADMINISTRATIVA ARROLLO, S.A. DE CV.",
                "Definitivo",
                "500-05-2019-7349 de fecha 1 de abril de 2019",
                "01/04/2019",
                "500-05-2019-7349 de fecha 1 de abril de 2019",
                "26/04/2019",
                "",
                ...,
            ],
            [
                "6",
                "AAA140116926",
                "AVALOS & ASOCIADOS CONSULTORIA INTEGRAL, S.C.",
                "Definitivo",
                "500-05-2020-23758 de fecha 03 de noviembre de 2020",
                "03/11/2020",
                "500-05-2020-23758 de fecha 03 de noviembre de 2020",
                "18/11/2020",
                "",
                ...,
            ],
            [
                "7",
                "AAA1502061S0",
                "ACUESY ASESORÍA ACUICOLA ESPECIALIZADA DE YUCATÁN, S.A. DE C.V.",
                "Sentencia Favorable",
                "500-05-2017-32156 de fecha 18 de septiembre de 2017",
                "18/09/2017",
                "500-05-2017-32156 de fecha 18 de septiembre de 2017",
                "20/10/2017",
                "",
                ...,
            ],
            [
                "8",
                "AAA151209DYA",
                "AYC ADMINISTRACION Y ASESORIA COMERCIAL, S.A. DE C.V.",
                "Definitivo",
                "500-05-2020-13588 de fecha 15 de mayo de 2020",
                "15/05/2020",
                "500-05-2020-13588 de fecha 15 de mayo de 2020",
                "29/06/2020",
                "",
                ...,
            ],
            [
                "9",
                "AAAA620217U54",
                "AMADOR AQUINO JOSÉ AVENAMAR",
                "Definitivo",
                "500-05-2017-16140 de fecha 1 de junio de 2017",
                "01/06/2017",
                "500-05-2017-16140 de fecha 12 de junio de 2017",
                "12/06/2017",
                "",
                ...,
            ],
            [
                "10",
                "AAAE910314EJ7",
                "ALVARADO ALMARAZ ESTEBAN JACOB",
                "Definitivo",
                "500-05-2020-13956 de fecha 01 de septiembre de 2020 ",
                "01/09/2020",
                "500-05-2020-13956 de fecha 01 de septiembre de 2020 ",
                "18/09/2020",
                "",
                ...,
            ],
        ]
        self.env["l10n_mx.efos"]._update_catalogs()  # pylint: disable=protected-access
        count = self.env["l10n_mx.efos"].search_count([])
        self.assertEqual(count, 10)

    @patch("odoo.addons.l10n_mx_efos.models.l10n_mx_efos.EFOS._download_sat_csv")
    def test_update_partner_status_if_list_change(self, mock_data):
        """
        Test if the status of the partners is re-computed when the list changes
        """
        self.env["l10n_mx.efos"].search([]).sudo().unlink()
        partner = self.env["res.partner"].create(
            {
                "name": "Test",
                "email": "test",
                "vat": "AAA080808HL8",
            }
        )
        self.assertEqual(partner.sat_efos_state, "unknown")
        mock_data.return_value = [
            [
                "1",
                "AAA080808HL8",
                "ASESORES EN AVALÚOS Y ACTIVOS, S.A. DE C.V.",
                "Sentencia Favorable",
                "500-05-2018-16632 de fecha 01 de junio de 2018",
                "01/06/2018",
                "500-05-2018-16632 de fecha 01 de junio de 2018",
                "25/06/2018",
                "",
                ...,
            ],
            [
                "2",
                "AAA091014835",
                "AQUAERIS ACUACULTURA Y ARQUITECTURA SUSTENTABLE, S.C.",
                "Desvirtuado",
                "500-05-2016-38728 de fecha 16 de diciembre de 2016",
                "01/01/2017",
                "500-05-2016-38728 de fecha 16 de diciembre de 2016",
                "19/01/2017",
                "500-05-2017-38533 de fecha 13 de octubre de 2017",
                ...,
            ],
        ]
        self.env["l10n_mx.efos"].update_catalog_and_partners()
        self.assertEqual(partner.sat_efos_state, "favorable")
