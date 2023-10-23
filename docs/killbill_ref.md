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

## KillBill Configuration

The first step in configuring the KillBill environment to work with the Openstack Billing API is to [create the catalog](https://docs.killbill.io/latest/catalog-examples.html). In our [example catalog](/openstack_billing/billingplatforms/killbill/catalog.xml) we setup a basic configuration for a billing model with 2 metrics being track for their individual contributuons to the invoice: `openstack-billed-instance` and `openstack-billed-vcpus`.

- `openstack-billed-instance` - the amount to be billed for instance uptime
- `openstack-billed-vcpus` - the amount to be billed for the amount of vcpus the instance is occupying

An account would subscribe to a subscrition that uses this catalog for the billing plan.

The next steps are to create the [custom fields](https://docs.killbill.io/latest/userguide_kaui.html#custom_fields) that will be specific to the account.

![KillBill Custom Fields](/docs/images/killbill_custom_fields.PNG?raw=true "KillBill Custom Fields Example")

- `openstack_metering_enabled` - the flag to tell whether this account should have metering enabled
- `openstack_project_id` - the corresponding openstack project ID
- `openstack_cloudkitty_metrics` - the comma separated list of openstack resources/netrics to track

The fields will be used by the Openstack Billing API to determine whtat to send to each subscription.
