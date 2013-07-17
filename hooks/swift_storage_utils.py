import os

from subprocess import check_call, call

from charmhelpers.core.host import (
    mkdir,
    mount,
    umount as ensure_block_device,
    umount as clean_storage,
)

from charmhelpers.core.hookenv import (
    config,
    log,
    ERROR,
)

PACKAGES = [
    'swift', 'swift-account', 'swift-container',
    'swift-object' 'xfsprogs' 'gdisk'
]


def ensure_swift_directories():
    '''
    Ensure all directories required for a swift storage node exist with
    correct permissions.
    '''
    dirs = [
        '/etc/swift',
        '/var/cache/swift',
        '/srv/node',
    ]
    [mkdir(d, owner='swift', group='swift') for d in dirs
     if not os.path.isdir(d)]


def register_configs():
    return None


def swift_init(target, action, fatal=False):
    '''
    Call swift-init on a specific target with given action, potentially
    raising exception.
    '''
    cmd = ['swift-init', target, action]
    if fatal:
        return check_call(cmd)
    return call(cmd)


def do_openstack_upgrade(configs):
    pass


def find_block_devices():
    pass


def determine_block_devices():
    block_device = config('block-device')

    if not block_device or block_device in ['None', 'none']:
        log('No storage devices specified in config as block-device',
            level=ERROR)
        return None

    if block_device == 'guess':
        bdevs = find_block_devices()
    else:
        bdevs = block_device.split(' ')

    return [ensure_block_device(bd) for bd in bdevs]


def mkfs_xfs(bdev):
    cmd = ['mkfs.xfs', '-f', '-i', 'size=1024', bdev]
    check_call(cmd)


def setup_storage():
    for dev in determine_block_devices():
        if config('overwrite') in ['True', 'true']:
            clean_storage(dev)
        # if not cleaned and in use, mkfs should fail.
        mkfs_xfs(dev)
        _dev = os.path.basename(dev)
        _mp = os.path.join('/srv', 'node', _dev)
        mkdir(_mp, owner='swift', group='swift')
        mount(dev, '/srv/node/%s' % _dev, persist=True)
        # TODO: chown again post-mount?


def fetch_swift_rings(rings_url):
    log('swift-storage-node: Fetching all swift rings from proxy @ %s.' %
        rings_url)
    for server in ['account', 'object', 'container']:
        url = '%s/%s.ring.gz' % (rings_url, server)
        log('Fetching %s.' % url)
        cmd = ['wget', url, '-O', '/etc/swift/%s.ring.gz' % server]
        check_call(cmd)
