# Billing Services / Handlers

The Billing modules of the Concertim-Openstack package manage the billing lifecycle of the various objects used in the Concertim workflow. This python utility package automates the process of various interactions between openstack and a selected billing application's API. The goal is to post metric data from the user's Openstack configuration to the configured billing API and Concertim using native Openstack python client libraries and REST API's.

The Billing modules consist of two separate components - the [service](/con_opstk/billing) modules and the [handler](/con_opstk/data_handler/billing_handler) modules. The `service` modules are a collection of functions and objects to manage communication with the chosen billing application. The `handler` modules are a collection of objects and functions to manage the automation workflow of the billing lifecycle. 

### Data Flow

![Data Flow Diagram](/docs/images/billing-api-data-flow.png?raw=true "Data Flow Diagram")

## Platform

The default Billing application that the package uses is KillBill, an opensource java-based billing application. The Concertim-Openstack service mainly uses the billing platform for invoice generation, customer tracking, and billing cycle management.

Currently supported billing applications:

- [KillBill](https://killbill.io/)
    - [KillBill reference](/docs/killbill_ref.md)
    - [KillBill Official Docs](https://docs.killbill.io/latest/)
- [HostBill](https://hostbillapp.com/)
    - [HostBill reference](/docs/hostbill_ref.md)
    - [Hostbill Official Docs](https://hostbill.atlassian.net/wiki/spaces/DOCS/overview)

## Installation

The Billing modules require the following to be installed and configured in the openstack environment:

- [Openstack Telemetry](https://docs.openstack.org/ceilometer/yoga/) (Ceilometer)
- [Openstack Rating](https://docs.openstack.org/cloudkitty/yoga/) (Cloudkitty)
- A time-seriese database for storing metrics (The default and **recommended** databse is [Gnocchi](https://gnocchi.osci.io/))

If **Killbill** is being used as the Billing App (default), the Concertim-Openstack service will require another package to be installed in order to function properly - [the Killbill API Client](https://github.com/alces-flight/killbill_fork). When building the Docker images, the `requirements.txt` will look into the `concertim-openstack-service/con_opstk/billing/killbill/` directory for this package.

Clone the Alces fork of the Killbill API Client into the Conceritm-Openstack billing directory
    ```
    cd concertim-openstack-service/con_opstk/billing/killbill/
    git clone https://<user>@github.com/alces-flight/killbill_fork.git
    ```

## Configuration

### `congif.yaml`

See the configured app's dedicated documentation

### Openstack

The billing automation makes use of various openstack objects for tracking Concertim-managed systems. To achieve this, the following need to be presesnt in Openstack:

- Openstack Role : `watcher` - Concertim Manager
- Openstack User : `concertim` - Concertim Manager
- Openstack Role : `rating` - Cloudkitty Role
- Openstack User : `cloudkitty` - Cloudkitty User

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.