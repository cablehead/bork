def get_instances_by_env(conn):
    envs = {}
    reservations = conn.get_all_instances()
    for reservation in reservations:
        for instance in reservation.instances:
            if instance.state == 'terminated':
                continue
            env_name = instance.tags.get('env')
            envs.setdefault(env_name, []).append(instance)
    return envs
