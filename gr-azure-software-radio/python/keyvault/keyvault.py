# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

def pull_key(vault_name, key, default_cred=None):
    """
    Pulls given key from a Azure keyvault given the vault name. This method returns a string corresponding to
    the key provided.

    Args:
        KeyVault Name: The keyvault name
        key: A key string which maps to a secret stored in the keyvault.
        default_cred: A DefaultAzureCredential object, other wise an empty string in which case one is generated locally.

    Example:
        KeyVault Name: myvault
        key: "SEED"

        The above would pull the SEED secret from myvault and set the blockname equal to value stored for SEED.
    """
    if not default_cred:
        default_cred = DefaultAzureCredential()
    client = SecretClient(
        vault_url=f"https://{vault_name}.vault.azure.net", credential=default_cred)
    return client.get_secret(key).value
