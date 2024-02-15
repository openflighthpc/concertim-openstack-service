/* This script should be run in the openstack database containing the gnocchi database and tables
Functionality:
    - instert 2 new rows into the gnocchi.archive_policy table
    
OPENSTACK CLI COMMAND ex:
openstack metric archive-policy create -d '[{"timespan": 3600.0, "granularity": 5.0, "points": 720}, {"timespan": 43200.0, "granularity": 60.0, "points": 720}, {"timespan": 2592000.0, "granularity": 3600.0, "points": 720}]' -m '["rate:mean", "mean"]' concertim_rate_policy
openstack metric archive-policy create -d '[{"timespan": 3600.0, "granularity": 5.0, "points": 720}, {"timespan": 43200.0, "granularity": 60.0, "points": 720}, {"timespan": 2592000.0, "granularity": 3600.0, "points": 720}]' -m '["mean"]' concertim_policy

*/

use gnocchi;
INSERT INTO gnocchi.archive_policy
VALUES ('concertim_rate_policy', 0, '[{"timespan": 3600.0, "granularity": 5.0, "points": 720}, {"timespan": 43200.0, "granularity": 60.0, "points": 720}, {"timespan": 2592000.0, "granularity": 3600.0, "points": 720}]', '["rate:mean", "mean"]'),('concertim_policy', 0, '[{"timespan": 3600.0, "granularity": 5.0, "points": 720}, {"timespan": 43200.0, "granularity": 60.0, "points": 720}, {"timespan": 2592000.0, "granularity": 3600.0, "points": 720}]', '["mean"]');
