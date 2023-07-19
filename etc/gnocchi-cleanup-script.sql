/* This script should be run in the openstack database containing the gnocchi database and tables
Functionality:
    - Display current counts
    - Mark stale metrics with 'delete' so gnocchi garbage collector properly deletes metrics
    - Delete dangling resources
    - Display new counts
*/

use gnocchi;
-- Total metric count
select count(id) from gnocchi.metric;

-- Total resource count
select count(id) from gnocchi.resource;

--#############################
--# Instance related cleanups #
--#############################
-- Delete metric history of items deleted in openstack
update gnocchi.metric as upm
set upm.status='delete'
where upm.id in
(select m.id
from nova.instances i, gnocchi.resource r, (select * from gnocchi.metric) m
where i.deleted <> 0
  and r.original_resource_id like concat('%', i.uuid,'%')
  and m.resource_id = r.id);

-- Delete dangling instance resources
delete from resource where id in (select r.id
from nova.instances i, (select * from gnocchi.resource) r
where i.deleted <> 0
  and r.original_resource_id like concat('%', i.uuid,'%'));

--####################
--# Volumes cleanups #
--####################
-- Delete metric history of items deleted in openstack
update gnocchi.metric
set gnocchi.metric.status='delete'
where gnocchi.metric.id in (
select id from (select id,resource_id from metric) as pruned_metric where resource_id in (
    select id from resource where type='volume' and original_resource_id in (
        select id from cinder.volumes where deleted <> 0 union select id from cinder.snapshots where deleted <> 0)));

-- Delete dangling volume resources
delete from resource where original_resource_id in (
  select id from cinder.volumes where deleted <> 0
  union select id from cinder.snapshots where deleted <> 0);

--###################
--# Images cleanups #
--###################
-- Delete metric history of items deleted in openstack
update gnocchi.metric
set gnocchi.metric.status='delete'
where gnocchi.metric.id in (
select id from (select id,resource_id from metric) as pruned_metric where resource_id in (
    select id from resource where type='image' and original_resource_id in (
        select id from glance.images where deleted <> 0)));

-- Delete dangling image resources
delete from resource where original_resource_id in (select id from glance.images where deleted <> 0);

-- Total metric count
select count(id) from gnocchi.metric;

-- Total resource count
select count(id) from gnocchi.resource;