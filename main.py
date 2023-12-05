from webdav3.exceptions import RemoteResourceNotFound
from webdav3.client import Client as WebDAVClient
from urllib.parse import urlparse, unquote
from syncthing import Syncthing, SyncthingError
import os
import io
import dotenv
dotenv.load_dotenv()


class Syncer:
    LAST_ID_PATH = "originals/.syncthing_last_id"

    def __init__(self, mappings, syncthing, webdav):
        self.mappings = mappings
        self.syncthing = syncthing
        self.webdav = webdav

    def get_last_syncid(self):
        try:
            res = self.webdav.resource(self.__class__.LAST_ID_PATH)
            buf = io.BytesIO(b'')
            res.write_to(buf)
            return int(buf.getvalue().decode())
        except RemoteResourceNotFound:
            return 0

    def write_last_syncid(self, last_id):
        res = self.webdav.resource(self.__class__.LAST_ID_PATH)
        res.read_from(str(last_id))

    def handle_file_synced(self, folder, filename):
        if not folder in self.mappings:
            return
        print(f"Uploading {filename} from folder {folder}")

        fullpath = os.path.join(self.mappings[folder], filename)
        if not os.path.isfile(fullpath):
            print("You likely have a configuration issue, syncthing is reporting a sync -- but we dont see the file mapped")
            return False

        self.webdav.upload_sync(
            remote_path=f"import/{filename}", local_path=fullpath)
        return True

    def run(self):
        # get the last sync'd id from the WebDAV server
        last_id = self.get_last_syncid()
        print(f"Starting from the last syncthing event id {last_id}")

        # subscribe to syncthing's event stream
        event_stream = self.syncthing.events(
            filters=("ItemFinished",), last_seen_id=last_id)
        for event in event_stream:
            ed = event['data']
            if ed['type'] == 'file' and ed['action'] == 'update':
                if self.handle_file_synced(ed['folder'], ed['item']):
                    self.write_last_syncid(event['id'])


def _mappings():
    return dict(x.split(':') for x in os.getenv('MAPPINGS').split(','))


def _syncthing():
    KEY = os.getenv('SYNCTHING_API_KEY')
    url = urlparse(os.getenv('SYNCTHING_URL'))
    HOST, PORT, IS_HTTPS = url.hostname, url.port, url.scheme == 'https'
    SSL_CERT_FILE = os.getenv('SYNCTHING_CERT_FILE')
    return Syncthing(KEY, HOST, PORT, 100.0, IS_HTTPS, SSL_CERT_FILE)


def _webdav():
    url = os.getenv('PHOTOPRISM_URL')
    parsed = urlparse(url)
    port_part = "" if parsed.port is None else f":{parsed.port}"
    return WebDAVClient({
        'webdav_hostname': f"{parsed.scheme}://{parsed.hostname}{port_part}",
        'webdav_login': parsed.username,
        'webdav_password': unquote(parsed.password),
        'disable_check': True
    })


def main():
    m = _mappings()
    s = _syncthing()
    w = _webdav()

    syncer = Syncer(m, s, w)
    syncer.run()


if __name__ == "__main__":
    main()
