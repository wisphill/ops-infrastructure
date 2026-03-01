TODO list

- Backup /etcd
- Add secrets using AGE key
- Add statefulset application
- Add role/role binding resource and testing
- Testing helm
- Add Grafana & datasources
- Add apps: Nginx, Ingress, Telemetry
- Istio testing with Istio Bookinfo
- Host Bitwarden for internal use with Tailscale
- Build gateway for game
- Host Minecraft servers for 2 players
- Enable Interoperability to access Window from WSL

DONE

1. Add infra app to manage infrastructure resources. (DONE)

## Commands

```
sops --encrypt --age age1fg2mcvwuztl4cgycxhdlfzu584uslnfznmgunqgw99znwmqhjq3quxdmw3 gitops/clusters/apse2/local/platform/monitoring/grafana/grafana-admin.yaml > gitops/clusters/apse2/local/platform/monitoring/grafana/secrets.enc.yaml
```
