import time

from boto.ec2.blockdevicemapping import BlockDeviceType, BlockDeviceMapping

try:
    import jinja2
except:
    jinja2 = None

import bork
import bork.groups
from bork import config


ephemeral0 = BlockDeviceType(ephemeral_name='ephemeral0')
ephemeral1 = BlockDeviceType(ephemeral_name='ephemeral1')
ephemeral2 = BlockDeviceType(ephemeral_name='ephemeral2')
ephemeral3 = BlockDeviceType(ephemeral_name='ephemeral3')

block_device_map = BlockDeviceMapping()
block_device_map['/dev/sdb'] = ephemeral0
block_device_map['/dev/sdc'] = ephemeral1
block_device_map['/dev/sdd'] = ephemeral2
block_device_map['/dev/sde'] = ephemeral3


def boot(conn, namespace, env, package, instance_type,
        zone='a', ami='ubuntu.12.04', num=1, branch='master',
        spot_price=None):

    is_cluster = (
        instance_type.startswith('cc2') or instance_type.startswith('cr1'))
    if is_cluster:
        ami += ':cluster'

    image = bork.buuks.amis['%s:%s' % (ami, conn.region.name)]

    p = bork.buuks.package(package)

    # booting from scratch
    bootstrap = bork.buuks.boot['boot.sh']

    bork.groups.ensure_groups(conn, namespace, env, p.groups())
    security_groups = [
        bork.groups.full_name(namespace, env, x) for x in p.groups()]

    kw = {}
    role = p.role
    if role:
        # TODO: update to take namespace
        if bork.roles.ensure_role(namespace, env, role):
            # give the role time to be created
            time.sleep(10)
        kw['instance_profile_name'] = 'aws-%s-%s-%s-instance-profile' % (
            namespace, env, role)

    user_data = jinja2.Template(bootstrap).render({
        'user': config.user,
        'package': package,
        'authorized_keys': bork.buuks.authorized_keys,
        'private_key': bork.buuks.private_key,
        'repos': p.repos(),
        })

    if not spot_price:
        r = conn.run_instances(
            image,
            min_count=num,
            max_count=num,
            instance_type=instance_type,
            security_groups=security_groups,
            placement=conn.region.name+zone,
            user_data=user_data,
            block_device_map=block_device_map,
            **kw)

        # give aws a chance to create the instances before tagging them
        time.sleep(2)
        for instance in r.instances:
            instance.add_tag('namespace', namespace)
            instance.add_tag('role', package)
            instance.add_tag('env', "%s.%s" % (namespace, env))
            instance.add_tag('owner', config.user)

    else:
        r = conn.request_spot_instances(
            spot_price,
            image,
            instance_type=instance_type,
            security_groups=security_groups,
            placement=conn.region.name+zone,
            user_data=user_data,
            block_device_map=block_device_map,
            **kw)

    return r
