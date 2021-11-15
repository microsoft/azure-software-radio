# pylint: disable=invalid-name
# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#
#  pylint: disable=too-many-arguments

from azure.identity import DefaultAzureCredential


def get_DefaultAzureCredential(enable_cli_credential, enable_environment, enable_managed_identity,
                      enable_powershell, enable_visual_studio_code, enable_shared_token_cache,
                      enable_interactive_browser, cred_authority='login.microsoftonline.com'):
    """
    Returns DefaultAzureCredential
    Args:
        enable_cli_credential: enable CLI authentication
        enable_environment: enable environment variable authentication
        enable_managed_identity: enable managed identity authentication
        enable_powershell: enable powersehll authentication
        enable_visual_studio_code: enable visual studio code authentication
        enable_interactive_browser: enable interactive broswer authentication
        cred_authority : Authority to use, defaults to 'login.microsoftonline.com'
    Returns:
        A DefaultAzureCredential.
    """

    return DefaultAzureCredential(exclude_cli_credential=not enable_cli_credential,
                                  exclude_environment_credential=not enable_environment,
                                  exclude_managed_identity_credential=not enable_managed_identity,
                                  exclude_powershell_credential=not enable_powershell,
                                  exclude_visual_studio_code_credential=not enable_visual_studio_code,
                                  exclude_shared_token_cache_credential=not enable_shared_token_cache,
                                  exclude_interactive_browser_credential=not enable_interactive_browser,
                                  authority=cred_authority)
