1. Create a Secret for your Private Key
   Argo CD needs your private key (AGE or GPG) to decrypt files.

```

# Example using an AGE key
kubectl create secret generic sops-age-key \
 --namespace argocd \
 --from-file=keys.txt=age-key.txt

```
