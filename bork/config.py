import urllib2
import sys
import os

import boto.ec2


def get_metadata(name):
    base = 'http://169.254.169.254/latest/meta-data/'
    return urllib2.urlopen(base+name, timeout=.3).read().strip()


class memoized_property(object):
    def __init__(self, method):
        self.method = method
        self.value = None

    def __get__(self, obj, type):
        if self.value == None:
            self.value = self.method(obj)
        return self.value


class AWS(object):
    @memoized_property
    def region(self):
        return 'us-west-2'
        try:
            return get_metadata('placement/availability-zone')[:-1]
        except urllib2.URLError:
            return 'us-east-1'

    @memoized_property
    def ip_address(self):
        return get_metadata('local-ipv4')

    @memoized_property
    def public_ip_address(self):
        return get_metadata('public-ipv4')

    @memoized_property
    def instance_id(self):
        return get_metadata('instance-id')[2:]

    @memoized_property
    def env(self):
        groups = get_metadata('security-groups')
        env = groups.split()[0].strip().split('-')[1]
        if '.' in env:
            env = env.split('.')[-1]
        return env

    @memoized_property
    def namespace(self):
        groups = get_metadata('security-groups')
        env = groups.split()[0].strip().split('-')[1]
        if '.' in env:
            env = env.split('.')[0]
        return env

    def connect(self, region=None):
        return boto.ec2.connect_to_region(region or self.region)


# start config

aws = AWS()
user = os.environ['USER']

paths = []
for path in sys.path:
    full = "%s/buuks" % (path,)
    if os.path.exists(full):
        paths.append(full)
paths.reverse()
