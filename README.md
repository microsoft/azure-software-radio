# Welcome To Azure software radio Github!

Here we are sharing two assets we have developed todate click on either link to dive in further!


1. [GNURadio - Azure Out of Tree Module](./gr-azure-software-radio/docs/README.md)
2. [Azure software radio Developer Virtual Machine](./pages/devvm.md)

## Getting Started

To get started, first please follow the install guides below. 

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

What things you need to install the software and how to install them

```
GnuRadio 3.9.0 or Greater
python 3.8 or greater
```

### Installing Azure software radio OOT

    ```
    pip install -r python/requirements.txt

    mkdir build
    cd build
    cmake ..
    make
    sudo make install
    ```

### Running Test

Tests can be run with any of the following methods:
 - From the build directory
    ```
    make test
    ```

 - From the python directory
    ```
    python -m pytest qa_*
    ```
    
    or

    ```
    python3 -m unittest qa_*
    ```

## Support  

This project uses [GitHub Issues](https://github.com/microsoft/azure-software-radio/issues) to track bugs and feature requests. Please refer to our [Support Guide](SUPPORT.md#how-to-file-issues-and-get-help) for more details.  

Starting with [GNU Radio](https://github.com/gnuradio/gnuradio) maint-3.9, this project will support the same set of [maintenance branches](https://github.com/gnuradio/gnuradio/branches) tracked by GNU Radio.  

## Contributing

[Contributing Guide](./CONTRIBUTING.md)

## License

This project is licensed under the GNU General Public License v3.0 or later - see the [LICENSE](LICENSE.txt) file for details

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft trademarks or logos is subject to and must follow Microsoft's Trademark & Brand Guidelines. Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship. Any use of third-party trademarks or logos are subject to those third-party's policies.

