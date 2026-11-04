import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parent.parent / 'skills/vibehoster-publish/scripts/upload_static.py'
spec = importlib.util.spec_from_file_location('upload_static', SCRIPT)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class UploadHelperTests(unittest.TestCase):
    def test_ticket_is_sent_in_header_and_not_printed(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return json.dumps({'url': 'http://site.example.test/'}).encode()
        def open_request(request, timeout):
            self.assertEqual(request.full_url, 'http://localhost:18404/upload')
            self.assertEqual(request.get_header('Authorization'), 'Bearer vh_upload_test')
            self.assertEqual(request.data.read(), b'zip-bytes')
            return Response()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'site.zip'
            path.write_bytes(b'zip-bytes')
            output = io.StringIO()
            with patch.object(helper.sys, 'argv', ['upload_static.py', str(path)]), \
                    patch.object(helper.sys, 'stdin', io.StringIO('vh_upload_test\n')), \
                    patch.object(helper.urllib.request, 'urlopen', side_effect=open_request), redirect_stdout(output):
                self.assertEqual(helper.main(), 0)
            self.assertNotIn('vh_upload_test', output.getvalue())
            self.assertIn('http://site.example.test/', output.getvalue())


if __name__ == '__main__':
    unittest.main()
