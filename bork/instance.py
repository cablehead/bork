import time

import bork

try:
    from bork import cli53
except:
    cli53 = None


# used for creating arguments to pass to cli53
class C(object):
    pass


class Instance(object):
    def __init__(self, conn, _id):
        self._id = 'i-'+_id
        self.instance = conn.get_all_instances(
            instance_ids=[self._id])[0].instances[0]

    def state(self):
        self.instance.update()
        return self.instance.state

    def env(self):
        return self.instance.tags.get('env')

    def add_dns_cname(self, zone, cname):
        args = C()
        args.zone = cli53.Zone(zone)
        args.replace = True
        args.wait=False
        args.ttl = 300
        args.type = 'CNAME'
        args.rr = cname
        args.values=[self.instance.public_dns_name]
        cli53.cmd_rrcreate(args)

    def set_tag(self, name, value):
        self.instance.add_tag(name, value)

    def set_name(self, name):
        namespace, env = self.env().split('.')
        cname = '%s.%s.%s' % (name, env, namespace)
        print '\tsetting name, %s.%s' % (cname, bork.buuks.domain)
        self.instance.add_tag('name', name)
        rname = cname.split('.')
        rname.reverse()
        rname = '.'.join(rname)
        self.instance.add_tag('Name', rname)
        self.add_dns_cname(bork.buuks.domain, cname)
        # TODO: add ability to hook additional functionality to setup scout etc

    def terminate(self):
        print "\tterminating %s ..." % self._id
        self.instance.terminate()
        while True:
            state = self.state()
            if state == 'terminated':
                break
            print '\t' + state
            time.sleep(5)
