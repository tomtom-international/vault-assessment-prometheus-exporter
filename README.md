# Vault Assessment Prometheus Exporter

[![Release](../../actions/workflows/release.yml/badge.svg)](../../sp-devsup-vault-expiration-monitoring/actions/workflows/release.yml)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

Provides a prometheus exporter for monitoring aspects secrets stored on a running HashiCorp Vault server - in contrast to the built-in metrics which focus on the operation of the server itself.

At present, the only supported usecase is for monitoring the age and expiration date for a secret stored within a [KV2 secret engine](https://www.vaultproject.io/docs/secrets/kv/kv-v2), as they are static secrets and lack any alerting to assist in manual rotation.

Future support may include tracking the age of connection secrets inside dynamic secret engines (e.g. the root password for the [database engine](https://www.vaultproject.io/docs/secrets/databases) or the secret for the primary service principal in the [Azure secret engine](https://www.vaultproject.io/docs/secrets/azure)).

Additionally, a modular design has been used, to allow for integration of other monitoring targets, for instance a module could be contributed to support tracking all policies using the `sudo` capability.

## Deploying Vault Assessment Prometheus Exporter

### Vault Configuration

Configuration on the Vault-side will require configuring authentication access and associating an appropriate Vault policy.
Please [Supported Authentication Methods](#supported-authentication-methods) for configuring authentication and [Required Policy](#required-policy) for details and instructions and the policy needed to run the exporter.

**Enterprise Users:** If you are running an enterprise server with namespaces, you should run an exporter per namespace, utilizing the exporter with root namespace privileges is discouraged.

#### Supported Authentication Methods

The exporter supports three authentication methods for its connection to HashiCorp Vault:

* [token](https://www.vaultproject.io/docs/internals/token) (intended primarily for development)
* [approle](https://www.vaultproject.io/docs/auth/approle)
* [kubernetes](https://www.vaultproject.io/docs/auth/kubernetes)

Additional authentication methods should be relatively easy to add due to usage of the [hvac](https://hvac.readthedocs.io/en/stable/overview.html) module, please feel free to open an issue or a pull request with any you might need.

#### Required Policy

Please see the [module documentation](#modules)

### Docker Image

A Docker image can be found at [/pkgs/container/vault-assessment-prometheus-exporter](../../pkgs/container/vault-assessment-prometheus-exporter)
The location of the secret file can be set with the `CONFIG_FILE` environmental variable, any other environment variables that may be required (e.g. for approles) are based on configuration.

### Direct Installation

To install and run  locally, use [poetry](https://python-poetry.org/).
To install and run, do the following:

1. `poetry install`
2. `poetry run start_exporter` (optionally use `--config_file` to specify a configuration file, otherwise it will look for the default at `config.yaml`)

### Basic Configuration

Basic configuration for the exporter configures access to Vault, as well as refresh rate and the port of the exporter.
The configuration is stored in `config.yaml` (or can be specified in another file with `--config_file`), and is validated for correctness after being loaded.

The schema for the configuration can be shown with `start_exporter --show_schema`.

#### General Configuration

* `refresh_interval` - the interval at which the exporter should access Vault to check the expiration metadata for all secrets, by default this is 30 seconds
* `port` - the port on which the exporter should run, by default this is 9937.

#### Configuring Vault Access

* `address` - the address for the HashiCorp Vault server, e.g. `https://localhost` when running a dev server
* `namespace` - the namespace to use for the Vault server, for root namespace or for open source instances, leave blank
* `authentication` - contains the authentication configuration for accessing Hashicorp Vault, see the "Configuring Authentication" section

#### Using a Custom CA

For using a custom CA (or otherwise setting the trusted certificate authorities) please use the environmental variable `REQUESTS_CA_BUNDLE`.

See the [requests documentation](https://requests.readthedocs.io/en/latest/user/advanced/#ssl-cert-verification) for more details.

##### Configuring Authentication

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

Please see module documentation for how to configure specific functionality in the Vault Assessment Prometheus Exporter instance.

* [Expiration Monitor](vault_monitor/expiration_monitor/README.md) - monitor secrets in KV2 engines for expiration
