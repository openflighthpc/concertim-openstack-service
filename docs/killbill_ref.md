# KillBill with Concertim-Openstack Service

For the KillBill -> Concertim-Openstack Service interaction, accounts in KillBill correspond to projects in Openstack where there is a subscription in KillBill for each cluster in Concertim.

When using KillBill as the prefered method of billing for the Openstack Billing API there is a minimum setup that must be completed to use the AIP.

- [a running KillBill build](https://docs.killbill.io/latest/getting_started.html), including [Kaui](https://docs.killbill.io/latest/userguide_kaui.html) and the backend database, that can be reached by ping/curl
- a user/tenant with a valid API key
- the `/etc/concertim-openstack-service/config.yaml` to be filled out for the user environment

After the above is met, there are pieces that we will edit to make the Openstack Billing API fit into the KillBill environment.

- Create a [catalog](https://docs.killbill.io/latest/catalog-examples.html) for the [subscriptions](https://docs.killbill.io/latest/userguide_subscription.html#components-catalog) to use
- Create the custom fields for the account
- have an account subscribe to a configured subscription

You are then ready to generate invoices for the configured accounts.

A basic Killbill setup can be found [here](/docs/killbill_basic.md)

## KillBill `config.yaml` Configuration

The Concertim-Openstack package communicates with Killbill via the [Killbill API Client](https://github.com/alces-flight/killbill_fork) and requires configuration in the `/etc/concertim-openstack-service/config.yaml` to work.

- `api_host` : The host url to reach the Killbill API
- `username` : The **admin** username
- `password` : The admin password
- `apikey` : The API Key for the tenant that it controlled by concertim
- `apisecret` : The secret corresponding to the API Key
- `plan_name` : "openstack-standard-monthly" - the default plan to use from the `catalog.xml` file

## KillBill Configuration

In order for the KillBill environment to work with the Concertim-Openstack Service you need to [create the catalog](https://docs.killbill.io/latest/catalog-examples.html) for the clusters built in Concertim to be track by. In our [example catalog](/con_opstk/billing/killbill/catalog.xml) we setup a basic configuration for a billing model with 2 metrics being track for their individual contributuons to the invoice: `openstack-billed-instance` and `openstack-billed-vcpus`.

- `openstack-billed-instance` - the amount to be billed for instance uptime
- `openstack-billed-vcpus` - the amount to be billed for the amount of vcpus the instance is occupying

An account would subscribe to a subscrition that uses this catalog for the billing plan.

