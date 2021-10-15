# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#

from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential


def pull_keys(vault_name, keys):
    """
    Pulls given keys from a Azure keyvault given the vault name. This method returns a dictionary
    of the keys and values.

    Args:
        vault_name: The keyvault name
        keys: A list of strings or tuples (inclusive). If a list element is a string, that string is the key 
              that will be pulled and the key in the returned dictionary. If a list element is a tuple, the first
              item of the tuple is the key that will pulled and the second element is 
              the key that will be used in the returned dictionary
    Returns:
        A dictionary of the keys or the given varible name wanted for that key passed in 
        as tuple to the value of that key orvariable.   
    """
    client = SecretClient(
        vault_url=f"https://{vault_name}.vault.azure.net", credential=DefaultAzureCredential())
    return {key if not isinstance(key, tuple) else key[-1]:
            (client.get_secret(key).value if not isinstance(
                key, tuple) else client.get_secret(key[0]).value) for key in keys}
