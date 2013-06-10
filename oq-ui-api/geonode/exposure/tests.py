import mock
import unittest

from exposure import util
from exposure import views

from django.http import HttpResponse


class FakeUser(object):
    def __init__(self, authed):
        self.authed = authed

    def is_authenticated(self):
        return self.authed

class FakeHttpGetRequest(object):
    def __init__(self, get_dict):
        self.GET = get_dict
        self.META = dict()
        self.method = 'GET'
        self.user = FakeUser(True)

class FakeHttpPostRequest(object):
    def __init__(self, post_dict):
        self.POST = post_dict
        self.META = dict()
        self.method = 'POST'
        self.user = FakeUser(True)

class FakeHttpDeleteRequest(object):
    def __init__(self, del_dict):
        self.DELETE = del_dict
        self.META = dict()
        self.method = 'DELETE'
        self.user = FakeUser(True)


class ExportExposureTestCase(unittest.TestCase):
    """
    Tests for the `export_building` view.
    """
    def setUp(self):
        self.get_dict = dict(lat1=8, lng1=45,
                             lat2=9, lng2=46,
                             outputType='nrml')

    def test_export_building_invalid_output_type(self):
        self.get_dict['outputType'] = 'pdf'
        request = FakeHttpGetRequest(self.get_dict)

        with self.assertRaises(ValueError) as ar:
            views.export_building(request)

        expected_error = (
            "Unrecognized output type 'pdf', only 'nrml' and 'csv' are "
            "supported"
        )
        self.assertEqual(expected_error, ar.exception.message)

    def test_export_building_calls_csv(self):
        # Test that the `export_building` function calls the
        # `stream_response_generator` with the correct arguments.
        # Also test that the HttpResponse `Content-Disposition` is correct.
        self.get_dict['outputType'] = 'csv'
        request = FakeHttpGetRequest(self.get_dict)

        srg_path = 'exposure.views.stream_response_generator'
        with mock.patch(srg_path) as srg_mock:
            response = views.export_building(request)

            # Check that the `stream_response_generator` is getting called:
            self.assertEqual(1, srg_mock.call_count)
            # Check that the generator is being called with the correct output
            # type:
            self.assertEqual('csv', srg_mock.call_args[0][1])

            self.assertEqual(response['Content-Disposition'],
                             'attachment; filename="exposure_export.csv"')
            self.assertEqual(response['Content-Type'], 'text/csv')
        srg_mock.stop()

    def test_export_building_calls_nrml(self):
        request = FakeHttpGetRequest(self.get_dict)

        srg_path = 'exposure.views.stream_response_generator'
        with mock.patch(srg_path) as srg_mock:
            response = views.export_building(request)

            # Check that the `stream_response_generator` is getting called:
            self.assertEqual(1, srg_mock.call_count)
            # Check that the generator is being called with the correct output
            # type:
            self.assertEqual('nrml', srg_mock.call_args[0][1])

            self.assertEqual(response['Content-Disposition'],
                             'attachment; filename="exposure_export.xml"')
            self.assertEqual(response['Content-Type'], 'text/plain')
        srg_mock.stop()


class GetRegCodesPopRatiosTestCase(unittest.TestCase):
    """
    Tests for the `exposure.util._get_reg_codes_pop_ratios` function.
    """

    def setUp(self):
        self.region_codes = [1, 2, 3]
        self.occupancy = [0, 1]

    def test_tod_off(self):
        tod = 'off'

        with mock.patch('exposure.util.exec_query') as eq:
            util._get_reg_codes_pop_ratios(self.region_codes,
                                           tod,
                                           self.occupancy)
            self.assertEqual(1, eq.call_count)
            expected_query = """
        SELECT
            geographic_region_id AS region_code,
            1 AS pop_ratio,
            is_urban
        FROM ged2.pop_allocation
        WHERE geographic_region_id IN (1, 2, 3)
        AND occupancy_id IN (0, 1)""".strip()
            actual_query = eq.call_args[0][1]
            actual_query = actual_query.strip()
            self.assertEqual(expected_query, actual_query)

    def test_tod_all(self):
        tod = 'all'

        with mock.patch('exposure.util.exec_query') as eq:
            util._get_reg_codes_pop_ratios(self.region_codes,
                                           tod,
                                           self.occupancy)

            self.assertEqual(1, eq.call_count)

            expected_query = """
        SELECT
            geographic_region_id AS region_code,
            (day_pop_ratio + night_pop_ratio + transit_pop_ratio) AS pop_ratio,
            is_urban
        FROM ged2.pop_allocation
        WHERE geographic_region_id IN (1, 2, 3)
        AND occupancy_id IN (0, 1)""".strip()
            actual_query = eq.call_args[0][1]
            actual_query = actual_query.strip()
            self.assertEqual(expected_query, actual_query)

    def test_tod_day_night_transit(self):
        with mock.patch('exposure.util.exec_query') as eq:
            for i, tod in enumerate(('day', 'night', 'transit')):
                util._get_reg_codes_pop_ratios(self.region_codes,
                                               tod,
                                               self.occupancy)

                self.assertEqual(i + 1, eq.call_count)

                expected_query = """
        SELECT
            geographic_region_id AS region_code,
            %s_pop_ratio AS pop_ratio,
            is_urban
        FROM ged2.pop_allocation
        WHERE geographic_region_id IN (1, 2, 3)
        AND occupancy_id IN (0, 1)""".strip()

                expected_query %= tod
                actual_query = eq.call_args[0][1]
                actual_query = actual_query.strip()
                self.assertEqual(expected_query, actual_query)

    def test_invalid_tod(self):
        tod = 'tea_time'
        with self.assertRaises(ValueError) as ar:
            util._get_reg_codes_pop_ratios(self.region_codes,
                                            tod,
                                            self.occupancy)

        expected_error = ("Invalid time of day: 'tea_time'. "
                          "Expected 'day', 'night', 'transit', 'all', or "
                          "'off'")
        self.assertEqual(expected_error, ar.exception.message)


class StreamResponseGeneratorTestCase(unittest.TestCase):
    """
    Tests for `stream_response_generator`.
    """

    def setUp(self):
        req_params = {
            'outputType': 'csv',
            'residential': 'res',
            'timeOfDay': 'day',
            'adminLevel': 'admin0',
            'lng1': '8.1',
            'lat1': '45.2',
            'lng2': '9.1',
            'lat2': '46.2',
        }
        self.request = FakeHttpGetRequest(req_params)

        self.adm_lvl_reg_patch = mock.patch(
            'exposure.util._get_admin_level_ids_region_ids'
        )
        self.adm_lvl_reg_mock = self.adm_lvl_reg_patch.start()
        self.adm_lvl_reg_mock.return_value = ['fake_admin_lvl_ids',
                                              'fake_region_ids']

        self.pop_patch = mock.patch('exposure.util._get_pop_table')
        self.pop_mock = self.pop_patch.start()

        self.grcpr_patch = mock.patch('exposure.util.'
                                      '_get_reg_codes_pop_ratios')
        self.grcpr_mock = self.grcpr_patch.start()

        self.df_patch = mock.patch('exposure.util._get_dwelling_fractions')
        self.df_mock = self.df_patch.start()

        self.ag_patch = mock.patch('exposure.views._asset_generator')
        self.ag_mock = self.ag_patch.start()
        self.ag_mock.return_value = []

        self.patches = [self.adm_lvl_reg_patch, self.pop_patch,
                        self.grcpr_patch, self.df_patch, self.ag_patch]
        self.mocks = [self.adm_lvl_reg_mock, self.pop_mock, self.grcpr_mock,
                      self.df_mock, self.ag_mock]

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def test_invalid_output_type(self):
        with self.assertRaises(ValueError) as ar:
            list(views.stream_response_generator(None, 'pdf'))

        expected_error = ("Unrecognized output type 'pdf', only 'nrml' and "
                          "'csv' are supported")
        self.assertEqual(expected_error, ar.exception.message)

    def test_invalid_admin_level(self):
        self.request.GET['adminLevel'] = 'admin4'

        with self.assertRaises(ValueError) as ar:
            list(views.stream_response_generator(self.request, 'csv'))

        expected_error = (
            "Invalid 'adminLevel' selection: 'admin4'."
            " Expected 'admin0', 'admin1', 'admin2', or 'admin3'."
        )
        self.assertEqual(expected_error, ar.exception.message)

    def test_query_func_calls_residential(self):
        # Test that the proper arguments are passed to the various DB query
        # helper functions.
        # 'Residential' selection is 'res'
        self.request.GET['adminLevel'] = 'admin0'

        # The list cast is done here to exhause the generator
        # (since all function calls happen in the context of a generator,
        # which is lazy)
        list(views.stream_response_generator(self.request, 'csv'))
        for m in self.mocks:
            self.assertEqual(1, m.call_count)

        self.assertEqual(('8.1', '45.2', '9.1', '46.2', 'gadm_country_id'),
                         self.adm_lvl_reg_mock.call_args[0])
        self.assertEqual(('8.1', '45.2', '9.1', '46.2', 'gadm_country_id'),
                         self.pop_mock.call_args[0])
        self.assertEqual(('fake_region_ids', 'day', [0]),
                         self.grcpr_mock.call_args[0])
        self.assertEqual(('fake_admin_lvl_ids', [0], 'gadm_country_id'),
                         self.df_mock.call_args[0])

    def test_query_func_calls_non_residential(self):
        # Test that the proper arguments are passed to the various DB query
        # helper functions.
        # 'Residential' selection is 'non-res'
        self.request.GET['adminLevel'] = 'admin1'
        self.request.GET['residential'] = 'non-res'

        list(views.stream_response_generator(self.request, 'csv'))
        for m in self.mocks:
            self.assertEqual(1, m.call_count)

        self.assertEqual(('8.1', '45.2', '9.1', '46.2', 'gadm_admin_1_id'),
                         self.adm_lvl_reg_mock.call_args[0])
        self.assertEqual(('8.1', '45.2', '9.1', '46.2', 'gadm_admin_1_id'),
                         self.pop_mock.call_args[0])
        self.assertEqual(('fake_region_ids', 'day', [1]),
                         self.grcpr_mock.call_args[0])
        self.assertEqual(('fake_admin_lvl_ids', [1], 'gadm_admin_1_id'),
                         self.df_mock.call_args[0])

    def test_query_func_calls_both(self):
        # Test that the proper arguments are passed to the various DB query
        # helper functions.
        # 'Residential' selection is 'both'
        self.request.GET['adminLevel'] = 'admin3'
        self.request.GET['residential'] = 'both'

        list(views.stream_response_generator(self.request, 'nrml'))
        for m in self.mocks:
            self.assertEqual(1, m.call_count)

        self.assertEqual(('8.1', '45.2', '9.1', '46.2', 'gadm_admin_3_id'),
                         self.adm_lvl_reg_mock.call_args[0])
        self.assertEqual(('8.1', '45.2', '9.1', '46.2', 'gadm_admin_3_id'),
                         self.pop_mock.call_args[0])
        self.assertEqual(('fake_region_ids', 'day', [0, 1]),
                         self.grcpr_mock.call_args[0])
        self.assertEqual(('fake_admin_lvl_ids', [0, 1], 'gadm_admin_3_id'),
                         self.df_mock.call_args[0])

    def test_invalid_residential(self):
        self.request.GET['residential'] = 'invalid'

        with self.assertRaises(ValueError) as ar:
            list(views.stream_response_generator(self.request, 'nrml'))

        self.assertEqual("Invalid 'residential' selection: 'invalid'. "
                         "Expected 'res', 'non-res', or 'both'.",
                         ar.exception.message)


class DecoratorUtilTestcase(unittest.TestCase):

    def test_allowed_methods(self):
        @util.allowed_methods(('GET', 'POST'))
        def fake_view(request):
            return HttpResponse(status=200)

        req = FakeHttpGetRequest(None)
        resp = fake_view(req)
        self.assertEqual(200, resp.status_code)

        req = FakeHttpPostRequest(None)
        resp = fake_view(req)
        self.assertEqual(200, resp.status_code)

        req = FakeHttpDeleteRequest(None)
        resp = fake_view(req)
        self.assertEqual(405, resp.status_code)

    def test_sign_in_required(self):
        @util.sign_in_required
        def fake_view(request):
            return HttpResponse(status=200)

        req = FakeHttpGetRequest(None)
        req.user.authed = False

        resp = fake_view(req)
        self.assertEqual(401, resp.status_code)

        req.user.authed = True
        resp = fake_view(req)
        self.assertEqual(200, resp.status_code)


class ExportAreaValidTestCase(unittest.TestCase):

    def test_valid(self):
        lat1 = '8'
        lng1 = '45'
        lat2 = '10'
        lng2 = '47'

        valid, _ = views._export_area_valid(lat1, lng1, lat2, lng2)
        self.assertTrue(valid)

    def test_invalid(self):
        lat1 = '8'
        lng1 = '45'
        lat2 = '10'
        lng2 = '47.001'

        valid, _ = views._export_area_valid(lat1, lng1, lat2, lng2)
        self.assertFalse(valid)


class ValidateExportTestCase(unittest.TestCase):

    def setUp(self):
        req_params = {
            'outputType': 'csv',
            'residential': 'res',
            'timeOfDay': 'day',
            'adminLevel': 'admin0',
            'lng1': '8.0',
            'lat1': '45.0',
            'lng2': '10.0',
            'lat2': '47.0',
        }
        self.request = FakeHttpGetRequest(req_params)

    def test_valid(self):
        resp = views.validate_export(self.request)
        self.assertEqual(200, resp.status_code)

    def test_invalid(self):
        self.request.GET['lat2'] = '47.001'
        resp = views.validate_export(self.request)
        self.assertEqual(403, resp.status_code)
