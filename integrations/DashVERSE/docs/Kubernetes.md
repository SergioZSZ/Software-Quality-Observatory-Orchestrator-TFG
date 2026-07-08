# Kubernetes Operations

Common commands for managing the DashVERSE deployment.

## Check Status

```shell
# all resources in namespace
kubectl get all -n dashverse

# or use justfile
just status
```

## View Logs

```shell
# all services
just logs

# specific service
just logs-postgres
just logs-postgrest
just logs-superset
```

## Port Forwarding

```shell
just port-forward
```

Services become available at:
- Superset: http://localhost:8088
- PostgREST: http://localhost:3000
- PostgreSQL: localhost:5432

## Debugging

```shell
# check pod status
kubectl get pods -n dashverse

# describe a pod
kubectl describe pod <pod-name> -n dashverse

# check events
kubectl get events -n dashverse --sort-by='.lastTimestamp'

# exec into a pod
kubectl exec -it <pod-name> -n dashverse -- /bin/sh
```

## Secrets

Secrets are managed by OpenTofu and stored in Kubernetes. To view:

```shell
kubectl get secrets -n dashverse
```

Generate a JWT token for API access (register a user first at `http://localhost:8000/register`):

```shell
just jwt <username> <password>
```

## Restart Services

```shell
# restart a deployment
kubectl rollout restart deployment/<name> -n dashverse

# or redeploy everything
just destroy
just deploy
```
