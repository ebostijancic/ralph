#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A discovery plugin for ganeti virtual server hypervisors.

This plugin tries to connect through SSH to the server and execute Ganeti-
-specific commands to get information about its cluster master, and all
the virtual servers running on it. I also sets all the virtual servers that
were there but are not anymore to deleted.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from lck.django.common.models import MACAddressField
from django.db.models import Q
import paramiko

from ralph.util import network
from ralph.discovery.models import DeviceType
from ralph.scan.errors import NotConfiguredError, NoMatchError
from ralph.scan.plugins import get_base_result_template


SAVE_PRIORITY = 50


class Error(Exception):
    pass


def _connect_ssh(ip):
    if not settings.SSH_PASSWORD:
        raise Error('no password defined')
    return network.connect_ssh(
        ip,
        settings.SSH_USER or 'root',
        settings.SSH_PASSWORD,
    )


def get_device(hostname, default=None):
    qs = Device.objects.filter(
        Q(name=hostname) |
        Q(ipaddress__hostname=hostname)
    ).distinct()
    for device in qs[:1]:
        return device
    return default


def get_master_hostname(ssh):
    stdin, stdout, stderr = ssh.exec_command('/usr/sbin/gnt-cluster getmaster')
    master = stdout.read().strip()
    if not master:
        raise Error('not a ganeti node.')
    return master


def get_instances(ssh):
    stdin, stdout, stderr = ssh.exec_command(
        '/usr/sbin/gnt-instance list -o name,pnode,snodes,ip,mac --no-headers',
    )
    for line in stdout:
        line = line.strip()
        if not line:
            continue
        hostname, primary_node, secondary_nodes, ip, mac = line.split()
        if ip == '-':
            ip = None
        mac = MACAddressField.normalize(mac)
        yield hostname, primary_node, ip, mac


def run_ssh_ganeti(ip):
    ssh = _connect_ssh(ip)
    master_hostname = get_master_hostname(ssh)
    existing_macs = set()
    master_device = {
        'subdevices': [],
        'hostname': master_hostname,
    }
    for hostname, primary_node, address, mac in get_instances(ssh):
        subdev = {
            'type': str(DeviceType.virtual_server),
            'hostname': hostname,
            'mac_addresses': [':'.join(map(''.join, zip(*[iter(mac)] * 2)))],
        }
        if address:
            subdev['management_ip_addresses'] = [address]
        master_device['subdevices'].append(subdev)
    return master_device


def scan_address(ip_address, **kwargs):
    if 'nx-os' in kwargs.get('snmp_name', '').lower():
        raise NoMatchError("Incompatible nexus found")
    device = run_ssh_ganeti(ip_address)
    ret = {
        'status': 'success',
        'device': device,
    }
    tpl = get_base_result_template('ssh_ganeti')
    tpl.update(ret)
    return tpl
