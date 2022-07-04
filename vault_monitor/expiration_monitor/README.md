# Expiration Monitor Module

This module monitors custom metadata for Vault secrets to allow easy maintenance of secret expiration for non-dynamic secret types (i.e. KeyVault v2 secrets).
Additionally metadata can be added to Vault entity to track their secrets rotation (e.g. for AppRoles and their secret-ids).

## Vault Policy Requirements

The exporter requires the `read` capability access to the metadata of the monitored secrets.
Additionally `read` is required on the entities that are being monitored.
Additionally, if you are using the recursive function to monitor multiple secrets in a path, you will need to provide the `list` capability.

A sample policy for a secret in the KV2 engine `secret` at path `some/example/secret` would need a policy like:

```hcl
path "secret/metadata/some/example/secret" {
  capabilities = [ "read" ]
}
```

To recursively monitor at the `example` level, it would look like:

```hcl
path "secret/metadata/some/example/**" {
  capabilities = [ "read", "list" ]
}
```

## Set Expiration

Expiration and last-renewal information is stored in the custom metadata for each secrets, or in the metadata for each entity.
It is recommended that you use automation (for a script that is also importable as a Python module see below), however you can also set the metadata manually via CLI or UI or in any other automation system.

Both timestamps are in UTC time in the [ISO 8601 format](https://www.w3.org/TR/NOTE-datetime-970915) with the timezone (`Z`) included at the end - this matches the format the the Vault server itself uses for timestamps.
The precision used goes to miliseconds, for example `2022-05-02T09:49:41.415869Z`
The exporter does not support other timezones, and will currently break if the are used.

The script can also recursively set metadata from a given secret path point.

## Field Info

* `last_renewal_timestamp` - this should be set when the secret is created or renewed, it indicates the age of the current version of the secret. This allows tracking the age of the secret, in addition to seeing when it is marked to expire.
* `expiration_timestamp` - this should be set the the target expiration date and time

Keep in mind, both fieldnames can be customized if needed or desired, see [Metadata Fieldnames](#metadata-fieldnames)

### Using the Provided Script

**Note**: The current script does not support setting entity ids.
This support will be added once they have been extended to support easier management of specific auth types, such as AppRole.

The `set_expiration` script can set the expiration data based on input provided (and can be imported/used as an example for automation).
It is capable of setting custom metadata fieldnames.
If you installed via poetry, you can execute `poetry run set_expiration -h` (or from a poetry shell just `set_expiration`) to see usage details.
If not install via poetry, use [vault_monitor/expiration_monitor/set_expiration.py](vault_monitor/expiration_monitor/set_expiration.py).

When using the `set_expiration` script you will need to provide the appropriate permissions to its bound token.
Due to the recent availability of the `patch` command ([Vault 1.10](https://www.vaultproject.io/docs/release-notes/1.10.0#kv-secrets-engine-v2-patch-operations)), this differs based on your Vault version.

* Vault 1.10 requires only the `patch` command on the secret
* Older versions require `read`, `write`, and `update` on the secret

### Importing the Script as Module

To use the `set_expiration` script as a module, import `vault_monitor/scripts/start_exporter.py` and call the function `set_expiration`.
The parameters are fairly straight-forward:

* `address`, and `namespace` - configures access to Vault
* `mount_point` and `secret_path` - point to the target secret
* `weeks`, `days`, `hours`, `minutes` and `seconds` - configure the timestamp
* `last_renewed_timestamp_fieldname` and `expiration_timestamp_fieldname` (optional) - allow you to configure the fieldnames used

Currently the Vault token is retrieved from the environment, in the near future it will be updated to require setting the token directly.

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
The goal of providing services is to allow the exporter to provide a label which clearly distinguishes between different services or aspects of a service - e.g. `backend` and `frontend` or `shop` and `mailing list`.

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

#### Entity Configuration

* `mount_point` - auth engine mount point
* `entity_id` - the entity id to monitor
* `entity_name` - a human readable name for the entity. This does not have to match the name used in Vault, as it is not used to look up the entity.