import logging

import bork

from bork import boot
from bork import config
from bork import env
from bork import instance


def start(
        namespace,
        env,
        package,
        instance_type='t1.micro',
        zone='a',
        ami='ubuntu.12.04',
        num=1,
        region=None,
        branch='master',
        spot_price=None,):

    conn = config.aws.connect(region)
    boot.boot(conn, namespace, env, package, instance_type, zone=zone,
        ami=ami, num=num, branch=branch, spot_price=spot_price)
    print "\tBooting..."


def install(package, dependencies='', announce=False, notify=None):
    logging.basicConfig(level=logging.DEBUG)
    b = bork.buuks.package(package)
    b.install(dependencies=dependencies)
    if announce:
        message = '@%s new %s.%s.%s, id: %s, ip: %s' % (
                notify or config.user, config.aws.namespace, config.aws.env,
                package, config.aws.instance_id, config.aws.public_ip_address,)
    logging.info("%s done.\n" % package)


def terminate(instance_id, region=None):
    conn = config.aws.connect(region)
    i = instance.Instance(conn, instance_id)
    i.terminate()


def set_name(instance_id, name, region=None):
    conn = config.aws.connect(region)
    i = instance.Instance(conn, instance_id)
    i.set_name(name)


def set_tag(instance_id, name, value, region=None):
    conn = config.aws.connect(region)
    i = instance.Instance(conn, instance_id)
    i.set_tag(name, value)


def status(region=None):
    conn = config.aws.connect(region)
    envs = env.get_instances_by_env(conn)

    extra = [x.name for x in conn.get_all_security_groups()
        if x.name.startswith('aws') and
            len(x.name.split('-')) == 2 and
            x.name.split('-')[1] not in envs]

    print 'Untracked:', envs.get(None)
    print

    total_cost = 0
    keys = envs.keys()
    keys.sort()
    for name in keys:
        if name:
            print "Environment:", name
            prices = {
                't1.micro': 14,

                'm1.small': 43,
                'm1.medium': 86,
                'm1.large': 173,
                'm1.xlarge': 346,

                'c1.medium': 104,
                'c1.xlarge': 418,

                'c3.large': 108,
                'c3.xlarge': 216,

                'm2.xlarge': 295,
                'm2.2xlarge': 590,
                'm2.4xlarge': 1181,

                'm3.2xlarge': 720,

                'cc2.8xlarge': 1728,
                'cr1.8xlarge': 2520,
            }
            instances = envs[name]
            instances.sort(
                lambda x,y: cmp(x.tags.get('name', ''), y.tags.get('name', '')))
            last_tag = None
            for instance in instances:
                prefix = '  '
                if last_tag != None:
                    if last_tag[:2] != instance.tags.get('name', '')[:2]:
                        prefix = '| '
                last_tag = instance.tags.get('name', '')
                cost = prices.get(instance.instance_type, 0)
                total_cost += cost
                print '  %s%-5s%-9s%s %-16s%-16s%-18s%-12s%-5s%-8s%s' % (
                    prefix,
                    instance.tags.get('name', ''),
                    instance.id[2:],
                    instance.placement[-1],
                    instance.ip_address,
                    instance.private_ip_address,
                    instance.tags.get('role', 'unknown'),
                    instance.instance_type,
                    cost,
                    instance.tags.get('owner', '')[:7],
                    instance.state+'.'+instance.tags.get('active', ''),
                    )
            print
    print '    %-5s%-9s%s %-16s%-16s%-18s%-12s%-5s%-8s%s' % (
        '', '', '', '', '', '', 'total cost:', total_cost, '', '',)

    for key in extra:
        handle = key[len('aws-'):]
        print "Environment:" , handle, '-- no instances'
