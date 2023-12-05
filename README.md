prismsyncer
===
A self-contained photo syncing service designed for syncthing and photoprism.

The primary use-case is to replace Google Photos on my Android, but it can be
used in many different ways.

## How it works

Syncthing maintains a synced folder between your phone and your NAS, but this is
not sufficient since you might delete photos from your phone. We need a way to
tell our photo library application to *import* new files when they appear in the
synced folder. This is where prismsyncer comes in...

prismsyncer listens to syncthing's event stream waiting for new files and then
immediately uploads them to Photoprism's WebDAV interface.

## Usage
```yaml
---
version: "2.1"
services:
    photoprism:
        ...
    syncthing:
        ....
    prismsyncer:
        image: <image>
        container_name: prismsyncer
        environment:
            - SYNCTHING_API_KEY=<your api key>
            - SYNCTHING_URL=http://syncthing:8384/
            - SYNCTHING_CERT_FILE=#optional
            - PHOTOPRISM_URL="http://admin:password@photoprism:2342/"
            - MAPPINGS=folderid:/mnt/vol1,folderid2:/mnt/vol2
        volumes:
            - "/mnt/vol1"
            - "/mnt/vol2"
```
