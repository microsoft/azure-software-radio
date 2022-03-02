# Azure SDR Tutorials

In these tutorials we demonstrate the power behind GNU Radio workflows in Azure.  These tutorials were written such that no prior experience with Azure and/or GNU Radio is required to follow along.

In **[Exploring GNU Radio Companion](exploring_grc/README.md)** we show how to install GNU Radio and the Azure blocks manually, starting with a fresh Ubuntu 20 VM in Azure.  We then switch over to using our prebuild GNU Radio development VM that lets you skip having to install and configure everything yourself.  As an example GNU Radio application we view the spectrum of the FM radio band, using an RF recording stored in Azure blob storage.

**[Mapping Airplane Locations Using ADS-B and Power BI](adsb_powerbi/README.md)** involves demodulating and decoding [ADS-B](https://en.wikipedia.org/wiki/Automatic_Dependent_Surveillance%E2%80%93Broadcast) signals transmitted by commercial aircraft, and send the resulting information into Azure event hub.  We have an RF recording of aircraft in the DC area, but with ~$50 in hardware you can receive and decode signals yourself!