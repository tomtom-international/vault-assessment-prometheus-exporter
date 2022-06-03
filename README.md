# VAPE - Vault Assesment Prometheus Exporter 

[![PR Checks](https://github.com/tomtom-internal/sp-devsup-vault-expiration-monitoring/actions/workflows/pr-checks.yml/badge.svg)](https://github.com/tomtom-internal/sp-devsup-vault-expiration-monitoring/actions/workflows/pr-checks.yml)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

Provides a prometheus exporter for monitoring aspects of a running HashiCorp Vault server.

## Deploy

### Direct Installation

At present, the easiest method to install and run is to use [poetry](https://python-poetry.org/).
To install and run, do the following:

1. `poetry install`
2. `poetry run start_exporter` (optionally use `--config_file` to specify a configuration file, otherwise it will look for the default at `config.yaml`)

## Basic Configuration

Basic configuration for the exporter configures access to HashiCorp Vault, as well as refresh rate and the port of the exporter.
The configuration is stored in `config.yaml` (or can be specified in another file with `--config_file`), and is validated for correctness after being loaded.

The schema for the configuration can be shown with `start_exporter --show_schema`.

### General Configuration

* `refresh_interval` - the interval at which the exporter should access Vault to check the expiration metadata for all secrets, by default this is 30 seconds
* `port` - the port on which the exporter should run, by default this is

### Configuring Vault Access

* `address` - the address for the HashiCorp Vault server, e.g. `https://localhost` when running a dev server
* `namespace` - the namespace to use for the Vault server, for root namespace or for open source instances, leave blank
* `authentication` - contains the authentication configuration for accessing Hashicorp Vault, see the "Configuring Authentication" section

#### Configuring Authentication

There are currently three supported authentication methods: `token`, `approle` and `kubernetes`.
All of these require that an appropriate policy is bound to the resulting `token`, the permissions for which are described in each of the module READMEs.

##### Token Authentication

Token authentication is not generally recommended for production deployments, but rather for testing and development.
The default configuration values correspond with the defaults used by the Vault client.

* `token_var_name` - the name of an environmental variable containing the token, by default this is `VAULT_TOKEN`
* `token_file` - the name of a file containing the token, by default this is `~/.vault-token`

##### Approle Authentication

AppRole configuration allows specifying the `role_id`, `secret_id` and `mount_point` for an Approle. `role_id` and `secret_id` can both either be provided directly in the configuration, or as pointers to a environmental variable or file.

* `role_id` options:
  * `role_id` - directly configure the id in the configuration yaml
  * `role_id_variable` - provide the name of an environmental variable to look up the `role_id` from
  * `role_id_file` - provide the path to a file with the `role_id`
* `secret_id` options:
  * `secret_id` -  directly configure the id in the configuration yaml
  * `secret_id_variable` - provide the name of an environmental variable to look up the `secret_id` from
  * `secret_id_file` - provide the path to a file with the `secret_id`
* `mount_point` - mount point in Vault for the approle authentication to use, `approle` by default

##### Kubernetes Authentication

Kubernetes configuration allows using the `jwt` token provided by a Kuberenetes container to authenticate with HashiCorp Vault.

* `token_file` - path to the token file, defaults to /var/run/secrets/kubernetes.io/serviceaccount/token
* `mount_point` - mount point in Vault for the kubernetes authentication to use, `kubernetes` by default

## Modules

* [Expiration Monitor](vault_monitor/expiration_monitor/README.md) - monitor secrets in KV2 engines for expiration
