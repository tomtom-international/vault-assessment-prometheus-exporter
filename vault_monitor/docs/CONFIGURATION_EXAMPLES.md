# Configuration Examples

## Basic Configuration - Simple

At a bare minimum, Vault must be configured with an address and some authentication method

```yaml
vault:
  address: https://vault.exampledomainname.com
  authentication:
    token:
```

## Complete Simple Configuration using Token Authentication for Expiration Monitoring

An example of the absolute bare-minimun configuration to monitor a single secret.

```yaml
vault:
  address: https://vault.exampledomainname.com
  authentication:
    token:

expiration_monitoring:
    - name: simple_service
      secrets:
      - mount_point: secrets
        secret_path: expiring_secrets
```

## Complete Complex Configuration for Expiration Monitoring

Uses all non-exclusive settings for monitoring a secret.

```yaml
vault:
  address: https://vault.tomtomgroup.com
  namespace: thenamespace # optional, don't set for root/open source
  # If multiple options are set, goes approle, kubernetes, token
  authentication:
    # Configuration for approle
    approle:
      mount_point: someapproleauth # default approle
        role_id: ab462-0462ac
        secret_id_variable: VAULT_MONITOR_SECRET_ID # the associated environmental variable must be set


refresh_interval: 10 # default is 30 seconds
port: 8350 # default is 9935

expiration_monitoring:
    metadata_fieldnames:
      last_renewal_timestamp: "first_last_renewal_timestamp" # default is last_renewal_timestamp
      expiration_timestamp: "first_expiration_timestamp" # default is expiration_timestamp
    prometheus_labels: # Global configuration for prometheus labels
      team: tomtom
      environment: prod
      owner: Eugene Davis
    services:
    - name: complicated_service
      # Allow overriding the default labels - must *update* the existing defaults (optional)
      prometheus_labels:
        environment: dev # Cannot add a key that doesn't already exist in the global configuration
      secrets:
      - mount_point: secrets
        secret_path: expiration_secrets
        recursive: True # Require the list permission, but be able to monitor every sub-secret (optional, default False)

      metadata_fieldnames: # Allow overriding the defaults per-service (optional) - the earlier configured fieldnames will be ignored for this service
        last_renewal_timestamp: "some_last_renewal_timestamp"
        expiration_timestamp: "some_expiration_timestamp"
```
