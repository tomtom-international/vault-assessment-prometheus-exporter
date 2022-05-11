# Expiration Monitor Module

This module monitors custom metadata for Vault secrets to allow easy maintenance of secret expiration for non-dynamic secret types (i.e. KeyVault v2 secrets).

## Set Expiration Command

The `set_expiration` script can set the expiration data based on input provided (and can be imported/used as an example for automation).
It is capable of setting custom metadata fieldnames.
If you installed via poetry, you can execute `poetry run set_expiration -h` (or from a poetry shell just `set_expiration`) to see usage details.
If not install via poetry, use [vault_monitor/expiration_monitor/set_expiration.py](vault_monitor/expiration_monitor/set_expiration.py).

## Configuration

Configuration is set within the main configuration yaml file, under the key `expiration_monitoring`

### Metadata Fieldnames

Under the key `metadata_fieldnames` you can specify custom fieldnames to use in the custom metadata for a secret, rather than the defaults `last_renewal_timestamp` and `expiration_timestamp`.
It is recommended to use the defaults unless they will conflict with existing custom metadata.

### Prometheus Labels

Under the key `promethus_labels` you can configure additional prometheus labels to set on the metrics.
These values can be overridden per-service.

### Services

Under the `services` key is a list of services with secrets to monitor.
A service in this context is merely a logical grouping, and beyond the fact a `service` label will be added by this name to each metric, it has no effect.

Each service can contain the following:

* `name` - the name of the service, this will be included as a label on the associated metrics
* `prometheus_labels` (optional) - this key allows over ridding the "global" Prometheus labels. It cannot, however, add a new key.
* `secrets` - this key maps to a list of secrets, see below for details for secret configuration
* `metadata_fieldnames` (optional) - allows you to override the default/"global" values for the custom metadata fieldnames

#### Secret Configuration

* `mount_point` - secret engine mount point
* `secret_path` - path within the secret engine to the secret to monitor
* `recursive` (optional) - if this option is set, then any and all secrets within the `secret_path` will be monitored. Note that enabling this requires the list permission to be provided by Vault.
