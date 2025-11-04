import unittest
import jinja2
import datetime

class TestUvSafeExposureMulti(unittest.TestCase):
    def setUp(self):
        # Load the Jinja template
        with open('exposure_st.jinja') as f:
            self.template_source = f.read()
        self.env = jinja2.Environment()
        self.env.globals.update({
            'now': lambda: datetime.datetime(2025, 9, 18, 12, 0, 0),
            'state_attr': self.mock_state_attr,
            'is_state': lambda eid, val: True,
            'as_datetime': self.mock_as_datetime,
            'as_local': lambda dt: dt,
            'tojson': lambda obj: obj,
        })
        self.template = self.env.from_string(self.template_source)

    def mock_state_attr(self, entity_id, attr):
        if attr == 'hourly':
            # Example hourly data
            return {
                'time': [
                    '2025-09-18T12:00:00',
                    '2025-09-18T13:00:00',
                    '2025-09-18T14:00:00',
                ],
                'uv_index': [2.0, 3.0, 0.0]
            }
        return None

    def mock_as_datetime(self, s, default=None):
        try:
            return datetime.datetime.fromisoformat(s)
        except Exception:
            return default

    def test_uv_safe_exposure_multi(self):
        # Call the macro with a mock entity_id
        result = self.template.module.uv_safe_exposure_multi('weather.test')
        self.assertIsInstance(result, dict)
        for k in ['st1','st2','st3','st4','st5','st6']:
            self.assertIn(k, result)
            self.assertIn('mins', result[k])
            self.assertIn('capped', result[k])

    def test_no_uv(self):
        # Patch mock_state_attr to return no UV
        self.env.globals['state_attr'] = lambda eid, attr: {'time': ['2025-09-18T12:00:00'], 'uv_index': [0.0]}
        template = self.env.from_string(self.template_source)
        result = template.module.uv_safe_exposure_multi('weather.test')
        for k in ['st1','st2','st3','st4','st5','st6']:
            self.assertEqual(result[k]['mins'], 0)
            self.assertFalse(result[k]['capped'])

if __name__ == '__main__':
    unittest.main()
