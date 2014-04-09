import bork


def full_name(namespace, env, group):
    prefix = 'aws-%s.%s' % (namespace, env)
    if group != 'base':
        prefix += '-%s' % group
    return prefix


def parse_security_group(namespace, env, description):
    bits = description.split(',')
    bits += [None]*(4-len(bits))
    protocol, start, end, src = bits
    kw = {
        'ip_protocol': protocol,
        'from_port': start,
        'to_port': end,}
    if src:
        kw['src_security_group_name'] = full_name(namespace, env, src)
    else:
        kw['cidr_ip'] = '0.0.0.0/0'
    return kw


def create_group(conn, namespace, env, group):
    if group == 'base':
        content = ['tcp,22,22']
    else:
        content = bork.buuks.groups[group]
    if content == None:
        raise Exception("please define group for: %s" % group)

    security_groups = [parse_security_group(namespace, env, x) for x in content]

    name = full_name(namespace, env, group)
    print "\tcreating security group %s..." % name
    conn.create_security_group(name, group)
    for security_group in security_groups:
        conn.authorize_security_group(name, **security_group)


def ensure_groups(conn, namespace, env, groups):
    existing = [x.name for x in conn.get_all_security_groups()]
    for group in groups:
        if full_name(namespace, env, group) not in existing:
            create_group(conn, namespace, env, group)
