#!/usr/bin/python3

# Copyright 2016 TransCirrus Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import os
import subprocess


def display(msg):
    print(msg)


def run_command(cmd):
    os_env = get_environment(os.environ.copy())
    p = subprocess.Popen(cmd, env=os_env, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode != 0:
        raise RuntimeError(
            "{} failed, status code {} stdout {} stderr {}".format(
                cmd, p.returncode, out, err))
    return out, err


def get_environment(env):
    with open("/root/novarc", "r") as ins:
        for line in ins:
            k, v = line.replace('export', '').replace(" ", "").split('=')
            env[k] = v.strip()
    return env


def get_server_id(server_name):
    servers = get_servers()
    if servers.get(server_name):
        return servers[server_name]['id']


def display_server_id(server_name):
    server_id = get_server_id(server_name)
    if server_id:
        display(server_id)


def get_domain_id(domain_name):
    domains = get_domains()
    if domains.get(domain_name):
        return domains[domain_name]['id']


def display_domain_id(domain_name):
    domain_id = get_domain_id(domain_name)
    if domain_id:
        display(domain_id)


def create_server(server_name):
    server_id = get_server_id(server_name)
    if server_id:
        return server_id
    cmd = [
        'designate', 'server-create',
        '--name', server_name,
        '-f', 'value',
    ]
    out, err = run_command(cmd)
    display(get_server_id(server_name))

"""
def create_domain(domain_name, domain_email):
    domain_id = get_domain_id(domain_name)
    if domain_id:
        return domain_id
    cmd = [
        'designate', 'domain-create',
        '--name', domain_name,
        '--email', domain_email,
        '-f', 'value',
    ]
    out, err = run_command(cmd)
    display(get_domain_id(domain_name))


def delete_domain(domain_name):
    domain_id = get_domain_id(domain_name)
    if domain_id:
        cmd = ['domain-delete', domain_id]
        run_command(cmd)


def get_domains():
    domains = {}
    cmd = ['designate', 'domain-list', '-f', 'value']
    out, err = run_command(cmd)
    for line in out.decode('utf8').split('\n'):
        values = line.split()
        if values:
            domains[values[1]] = {
                'id': values[0],
                'serial': values[2],
            }
    return domains
"""

def get_servers():
    servers = {}
    cmd = ['designate', 'server-list', '-f', 'value']
    out, err = run_command(cmd)
    for line in out.decode('utf8').split('\n'):
        values = line.split()
        if values:
            servers[values[1]] = {
                'id': values[0],
            }
    return servers


def display_domains():
    for domain in get_domains():
        display(domain)


def display_servers():
    for server in get_servers():
        display(server)

def trove_create(**cmd_args):
    for k,v in cmd_args.iteritems():
        print "%s = %s" % (k, v)
    # TODO
    pass

def trove_db_create(**cmd_args):
    # TODO
    pass

def trove_db_delete(**cmd_args):
    # TODO
    pass

def trove_db_list(**cmd_args):
    # TODO
    pass

def trove_delete(**cmd_args):
    # TODO
    pass

def trove_list(**cmd_args):
    # TODO
    pass

def trove_show(**cmd_args):
    # TODO
    pass

if __name__ == '__main__':
    commands = {
    #    'domain-create': create_domain,
    #    'server-create': create_server,
    #    'domain-get': display_domain_id,
    #    'server-get': display_server_id,
    #    'domain-delete': delete_domain,
    #    'domain-list': display_domains,
    #    'server-list': display_servers,
        'trove-create': trove_create,
        'trove-database-create': trove_db_create,
        'trove-database-delete': trove_db_delete,
        'trove-database-list': trove_db_list,
        'trove-delete': trove_delete,
        'trove-list': trove_list,
        'trove-show': trove_show,
    }
    parser = argparse.ArgumentParser(description='trove cli reference')
    parser.add_argument('command',
                        help='One of: {}'.format(', '.join(commands.keys())))
    #parser.add_argument('--domain-name', help='Domain Name')
    #parser.add_argument('--server-name', help='Server Name')
    #parser.add_argument('--email', help='Email Address')

    # must arguments for trove create
    parser.add_argument('--name', help='Name of the instance(trove-create) or database (trove-database-create)')
    parser.add_argument('--flavor', help='A flavor name or ID')
    # must arguments for trove db create
    parser.add_argument('--instance', help='ID or name of the instance')
    # must arg for trove db delete
    parser.add_argument('--database', help='Name of the database.')

    # optional args for trove db create
    parser.add_argument('--character-set', action='store_true', help='Optional character set for database.')
    parser.add_argument('--collate', action='store_true', help='Optional collation type for database.')

    # optional arguments for trove create
    parser.add_argument('--size', default=0, action='store_true', help='Size of the instance disk volume in GB. Required when volume support is enabled.')
    parser.add_argument('--volume_type', action='store_true', help='Volume type. Optional when volume support is enabled.')
    parser.add_argument('--databases', action='store_true', help='Optional list of databases..')
    parser.add_argument('--users', action='store_true', help='Optional list of users: <user:password> [<user:password> ...]')
    parser.add_argument('--backup', action='store_true', help='A backup name or ID.')
    parser.add_argument('--availability_zone', action='store_true', help='The Zone hint to give to Nova: --availability_zone <availability_zone>')
    parser.add_argument('--datastore', action='store_true', help='The datastore name or ID: --datastore <datastore>')
    parser.add_argument('--datastore_version', action='store_true', help='The datastore version name or ID: --datastore_version <datastore_version>')
    parser.add_argument('--configuration', action='store_true', help='ID of the configuration group to attach to the instance.')
    parser.add_argument('--replica_of', action='store_true', help='ID or name of an existing instance to replicate from.')
    parser.add_argument('--replica_count', default=1, action='store_true', help='Number of replicas to create (defaults to 1 if replica_of specified).')
    parser.add_argument('--module', action='store_true', help='ID or name of the module to apply. Specify multiple times to apply multiple modules.')
    parser.add_argument('--locality', action='store_true', help='Locality policy to use when creating replicas. Choose one of affinity, anti-affinity.')

    # optional args for trove list
    parser.add_argument('--limit', action='store_true', help='Limit the number of results displayed')
    parser.add_argument('--marker', action='store_true', help='Begin displaying the results for IDs greater than the specified marker. When used with --limit, set this to last ID displayed in the previous run')

    args = parser.parse_args()
    # extract essential args if they exist into a dictionary
    # to pass to the command -- this enforces that the right thing is passed to
    # a function that is expecting an argument.
    cmd_args = {v: a
                for v, a in zip(
                        ('name', 'flavor', 'instance', 'database'),
                        (args.name, args.flavor, args.instance, args.database))
                if a}
    # check for command specific required args
    if args.command == 'trove-create':
        if (args.name == None or args.flavor == None):
            raise RuntimeError("Error: {} required args --name --flavor".format(args.command))

    if args.command == 'trove-database-create':
        if args.instance == None or args.name == None:
            raise RuntimeError("Error: {} required args --instance --name".format(args.command))
            exit(-1)

    if args.command == 'trove-database-delete':
        if args.instance == None or args.database == None:
            raise RuntimeError("Error: {} required args --instance --database".format(args.command))
            exit(-1)

    if args.command == 'trove-database-list':
        if args.instance == None:
            raise RuntimeError("Error: {} required args --instance".format(args.command))
            exit(-1)

    if args.command == 'trove-delete':
        if args.instance == None:
            raise RuntimeError("Error: {} required args --instance".format(args.command))
            exit(-1)

    if args.command == 'trove-show':
        if args.instance == None:
            raise RuntimeError("Error: {} required args --instance".format(args.command))
            exit(-1)

    commands[args.command](**cmd_args)
