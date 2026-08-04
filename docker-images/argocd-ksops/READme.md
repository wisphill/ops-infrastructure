### Test

```bash
docker login ghcr.io
docker run --rm -it --platform=linux/amd64 --entrypoint=/bin/sh ghcr.io/wisphill/argocd-repo-server:latest
```
