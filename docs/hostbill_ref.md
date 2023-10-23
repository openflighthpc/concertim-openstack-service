# HostBill with Concertim-Openstack Service

When using HostBill as the prefered billing application, there is a minimum setup that must be completed to use the billing AIP.

- An active HostBill license
- A running HostBill instance that can be reached with ping/curl
- the [HostBill/Openstack module](https://hostbillapp.com/products-services/openstack/) installed
- a valid HostBill API key/ID
- a working [app connection with OpenStack](https://hostbill.atlassian.net/wiki/spaces/DOCS/pages/1213366/OpenStack)
- an OpenStack product with [metered billing](https://hostbill.atlassian.net/wiki/spaces/DOCS/pages/6160386/Metered+Billing) as the payment type

## HostBill Product configuration

To configure a product to be used with the billing API you will need to have the payment type set to metered billing and configure the billing to use the metrics tracked by the user's Openstack deployment. When setting the payment type to metered billing you should see an area to add variables to the product - this is where you will add what metrics you want this specific product to be billed for.

![Hostbill Metered Billing](/docs/images/hostbill_metered_billing_vars.PNG?raw=true "Hostbill Metered Billing Variables")

- `Name` - the name of the variable that is displayed to the HostBill clients
- `Unit` - the unit of the metric being added
- `Variable` - the name of the variable that is used in the backend - this needs to correspond to the variable name output by `openstack rating summary get -a -g tenant_id,res_type`
- `Starting QTY` - this value should be 0
- `Ending QTY` - this field should remain empty
- `Unit Price` - this should be set to 1 (the value calculation is done by the cloudkitty service)
