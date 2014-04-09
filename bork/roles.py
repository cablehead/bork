import os

import boto

def create_role(env, role):
    c = boto.connect_iam()
    prefix = 'aws-%s-%s-' % (env, role)

    path = os.path.join(
        os.path.dirname(__file__), '..', 'cuukbuuks', 'roles',  role)
    policy = open(path).read() % {'env': env}

    print "\tcreating permission role", prefix+'role', '...'
    c.create_instance_profile(prefix+'instance-profile')
    c.create_role(prefix+'role')
    c.add_role_to_instance_profile(prefix+'instance-profile', prefix+'role')
    c.put_role_policy(prefix+'role', prefix+'policy', policy)


def ensure_role(env, role):
    c = boto.connect_iam()
    prefix = 'aws-%s-%s-' % (env, role)

    profiles = c.list_instance_profiles()
    profiles = profiles['list_instance_profiles_response']
    profiles = profiles['list_instance_profiles_result']
    profiles = profiles['instance_profiles']
    profiles = [x['instance_profile_name'] for x in profiles]

    if prefix+'instance-profile' not in profiles:
        create_role(env, role)
        return True


def delete_role(env, role):
    c = boto.connect_iam()
    prefix = 'aws-%s-%s-' % (env, role)

    c.delete_role_policy(prefix+'role', prefix+'policy')
    c.remove_role_from_instance_profile(prefix+'instance-profile', prefix+'role')
    c.delete_role(prefix+'role')
    c.delete_instance_profile(prefix+'instance-profile')


def delete_roles(env):
    c = boto.connect_iam()
    prefix = 'aws-%s-' % env

    profiles = c.list_instance_profiles()
    profiles = profiles['list_instance_profiles_response']
    profiles = profiles['list_instance_profiles_result']
    profiles = profiles['instance_profiles']
    profiles = [x['instance_profile_name'] for x in profiles]
    profiles = [x for x in profiles if x.startswith(prefix)]

    for profile in profiles:
        role = profile.split('-')[2]
        print "\tdeleting permission role", prefix+'role', '...'
        delete_role(env, role)
