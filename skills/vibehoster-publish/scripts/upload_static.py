#!/usr/bin/env python3
"""Upload a prepared ZIP with a one-time ticket read from standard input."""
import json
import os
from pathlib import Path
import sys
import urllib.error
from urllib.parse import urlsplit
import urllib.request

URL = os.environ.get('VIBEHOSTER_UPLOAD_URL', 'https://mcp.vibehoster.ru/upload')
LIMIT = 100 * 1024 * 1024


def main():
    if len(sys.argv) != 2:
        print('Usage: upload_static.py /absolute/path/site.zip < ticket.txt', file=sys.stderr)
        return 2
    ticket = sys.stdin.readline(201).strip()
    try:
        address = urlsplit(URL)
        if (not ((address.scheme == 'https' and address.hostname == 'mcp.vibehoster.ru' and address.port in (None, 443))
                 or (address.scheme == 'http' and address.hostname in ('localhost', '127.0.0.1') and address.port))
                or address.username or address.password or address.path != '/upload'
                or address.query or address.fragment):
            raise ValueError
    except ValueError:
        print('Invalid upload URL', file=sys.stderr)
        return 1
    if not ticket.startswith('vh_upload_') or len(ticket) > 200:
        print('Invalid upload ticket', file=sys.stderr)
        return 1
    try:
        path = Path(sys.argv[1])
        size = path.stat().st_size
        if size > LIMIT:
            raise ValueError('Archive exceeds 100 MiB')
        # Send a file stream, not its base64 content in the model context.
        with path.open('rb') as archive:
            request = urllib.request.Request(URL, method='POST', data=archive, headers={
                'Authorization': 'Bearer ' + ticket, 'Content-Type': 'application/zip', 'Content-Length': str(size)})
            with urllib.request.urlopen(request, timeout=180) as response:
                result = json.loads(response.read())
        print(json.dumps(result, ensure_ascii=False))
    except (OSError, ValueError, urllib.error.HTTPError, urllib.error.URLError):
        print('Upload failed. Check the archive, connection, and ticket; request a new ticket if needed.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
