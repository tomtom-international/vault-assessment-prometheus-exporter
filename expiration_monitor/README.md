# Vault Expiration Monitor

## Format

* last_updated - used for the last "real" update to the secret rather than depending on the secret to not have been edited in some way (possibly without actually rotating the credential) in Vault which is shown by `updated_time`