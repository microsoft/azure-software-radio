# Frequently asked questions

## How can I file an issue?  
  See our guidelines on [How to file issues and get help](../../SUPPORT.md) or [Reporting Security Issues](../../SECURITY.md#reporting-security-issues).  

## How can I contribute to this project?  
  See our [Contributing](../../README.md#contributing) guide for more details.  

## Why is cmake failing to find azure components?  
  If you are having issues installing gr-azure-software-radio, the first troubleshooting step is to make sure the python requirements have been successfully installed. To install the requirements use ``` pip install -r python/requirements.txt ```  (or follow the [Installation Instructions](../../README.md/#installing-azure-software-radio-oot)).   
  Then, verify the installed package versions using ``` pip freeze -r python/requirements.txt ```.  

  ### Installing requirements errors with version conflicts, what should I do?  
  If there are version conflicts with the Azure packages, consider using a [virtual environment](https://docs.python.org/3/tutorial/venv.html) to manage package dependencies.  

  If the version conflicts are due to the Azure CLI installation using pip, refer to the [Azure CLI Installation](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) for the recommended installation options.  

## Failures importing azure_software_radio in the flowgraph  
  By default Azure software radio will be installed in the ``` /usr/local/ ``` directory. Use the ``` CMAKE_INSTALL_PREFIX ``` to install elsewhere.  

  Add the install prefix to your environment  
  ```
  export PYTHONPATH=<INSTALL_PREFIX>/lib/python3/dist-packages:<INSTALL_PREFIX>/lib/python3/site-packages:$PYTHONPATH
  export LD_LIBRARY_PATH=<INSTALL_PREFIX>/lib:$LD_LIBRARY_PATH
  ```

  