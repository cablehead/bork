Getting Started
===============

Configuration
=============

Security Groups
---------------

Every environment gets a default base security group: *aws-&lt;envname&gt;*. At
the moment this security group allows access to port 22 from everywhere. All
instances in an environment will be assigned to this base security group.

You can define new security groups by creating a file in
*~/git/borkbork/cuukbuuks/group*. e.g. *~/git/borkbork/cuukbuuks/group/web*
will create a security group *aws-&lt;envname&gt;*-web. Each line in this file
describes a rule for ports to open:

        <protocol>,<start_port>,<end_port>[,source]

        # e.g.

        # open http access to port 80
        # by default, if source is not supplied, all ips will be able to access
        # this port. be careful which services you expose!!
        http,80,80

        # open tcp access to ports 7051 through 7061
        # the base source is the environment's base security group, which means
        # all instances from this environment will be able to access these
        # ports
        tcp,7051,7061,base

        # open tcp access to ports 7090 and 7091
        # the source is specified as web, so only instances which have been
        # assigned this environment's web security group will be able to access
        # these ports
        tcp,7090,7091,web

Security groups are assigned to instance types. Any time an instance of a given
type is started, if any of it's security groups don't exist yet, they'll be
created, and the then the new instance will be assigned it's security groups on
startup.

Which security groups an instance receives is controlled by
*~/git/borkbork/cuukbuuks/packages/&lt;name&gt;/groups*

