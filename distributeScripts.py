# распространение скриптов
'''
<parameters>
	<company>Timofei Serov</company>
	<title>Distribute Scripts</title>
	<version>1.0</version>
</parameters>
'''
is_write_logs_1 = False
is_write_logs_2 = False

connection_duration = 10

import datetime
import csv
import re

def write_log(text, is_write=True):
	if is_write:
		with open('___%s.log' % __name__, 'a') as log:
			log.write('%s\t%s\n' % (datetime.datetime.now(), str(text).replace('\n', '| ')))



def is_trassir_guid(text):
	return re.match(r'^[0-9A-Za-z]{8}$', text)
			


def is_cloud_id(text):
	return re.match(r'^[1-9A-Fa-f]{1}[0-9A-Fa-f]{7}$', text)



def delete_network_nodes(nodes=None, node=None):
	if is_write_logs_2: write_log('nodes %s, node %s' % (nodes, node))
	if nodes or node:
		node = node or (nodes.pop(0) if nodes else None)
		if node in [x.guid for x in settings('network').ls() if x.type == 'NetworkNode']:
			settings('network/network_node_add')['delete_node_id'] = node
			timeout(500, lambda: delete_network_nodes(nodes, node))
		else:
			timeout(500, lambda: delete_network_nodes(nodes))


	
def get_all_guides(path):
	path = path if type(path) == type(list()) else [path]
	try:
		leaves = [x.guid for x in settings('/' + '/'.join(path)).ls()]
	except:
		return set(['server'])
	subleaves = set(leaves)
	for leaf in leaves:
			subleaves.update(get_all_guides(path + [leaf]))
	return subleaves

	
	
def main(stage=0, count=0, **params):
	
	# is threr server to connect, is there server to take server from them?
	if stage == 0:
		if params.get('connection'):
			timeout(10, lambda: main(stage+1, **params))
		elif params.get('connections'):
			params['connection'] = params['connections'].pop(0)
			write_log('>%s' % params['connection'][0])
			timeout(10, lambda: main(**params))
		else:
			write_log('---FINISH---')
	
	# initiating connection to server
	# TODO: ports (rpc, video)
	# TODO: cloud login in Trassit 3.3 / 4.0
	elif stage == 1 and params.get('connection') and len(params['connection']) >= 3:
		network_add = settings('network/network_node_add')
		params['guid'] = network_add['new_node_id']
		address, network_add['new_node_username'], network_add['new_node_password'] = params['connection'][:3]
		network_add['new_node_cloud_id' if is_cloud_id(address) else 'new_node_name'] = address
		if is_cloud_id(address):
			network_add['new_node_use_cloud_connect'] = 1
		network_add['create_now'] = 1
		timeout(500, lambda: main(stage+1, **params))
	
	# waiting connection or error message or timeout 140*500 = 50000 ms = 70 s
	elif stage == 2 and params.has_key('guid') and is_trassir_guid(params['guid']):
		guid = params['guid']
		node = settings('network/' + guid)
		connected, last_error = node.cd('stats')['connected'], node.cd('stats')['last_error']
		if is_write_logs_1 and not count: write_log(' counting, error "%s"' % last_error)
		if is_write_logs_2: write_log('  c %s, e "%s"' % (count, last_error))
		params['connected'] = connected
		if connected:
			timeout(connection_duration, lambda: main(stage+1, **params))
		elif not connected and last_error == 'certificate verify failed':
			node['accepted_fingerprint'] = node.cd('stats')['fingerprint']
			timeout(100, lambda: main(stage, **params))
		elif not connected and count <= 140 and not last_error:
			timeout(500, lambda: main(stage, count+1, **params))
		elif not connected and (count > 140 or last_error):
			write_log(' ERROR for %s: "%s"' % (params['connection'][0], last_error))
			timeout(10, lambda: main(stage+1, **params))
		else:
			timeout(10, lambda: main(100))
	
	# getting guid of connected server
	elif stage == 3 and params.has_key('connected'):
		if params['connected']:
			guid = params['guid']
			params['connected'] = settings('network/%s/stats' % guid)['connected']
			server_guids = dict([
					( x['connected_through'].split('/')[-1], x.guid ) 
					for x in settings('/').ls()
						if x.type == 'RemoteServer' 
				])
			if server_guids.has_key(guid):
				params['server_guid'] = server_guids[guid]
				write_log(' GUID for %s: %s' % (params['connection'][0], params['server_guid']))
				timeout(10, lambda: main(stage+1, **params))
			elif count < 140:
				timeout(500, lambda: main(stage, count+1, **params))
			else:
				timeout(10, lambda: main(stage+1, **params))
		else:
			timeout(10, lambda: main(stage+1, **params))
	
	# getting name of connected server
	elif stage == 4 and params.has_key('connected'):
		if params['connected'] and params.get('server_guid') and is_trassir_guid(params['server_guid']):
			server_guid = params['server_guid']
			leaves = get_all_guides(server_guid)
			if is_write_logs_1: write_log('  LEAVES = %s' % len(leaves))
			if not params.has_key('settingstree_leaves') or params['settingstree_leaves'] < len(leaves):
				params['settingstree_leaves'] = len(leaves)
				timeout(1000, lambda: main(stage, **params))
				return
			try:
				server_name = settings('/%s'%server_guid)['name']
			except KeyError as e:
				if is_write_logs_1 and not count: write_log('  NO ALL LEAVES = %s, counting' % len(leaves))
				if is_write_logs_2: write_log('   c %s, LEAVES = %s' % (count, len(leaves)))
				if count < 140:
					timeout(500, lambda: main(stage, count+1, **params))
				else:
					params['connected'] = 0
					timeout(10, lambda: main(stage+1, **params))
				return
			write_log('   NAME for %s: %s' % (params['connection'][0], server_name))
		timeout(10, lambda: main(stage+1, **params))
	
	# getting list os script names of the server
	# TODO: call payload function(s) to make something on connected server
	elif stage == 5 and params.has_key('connected'):
		if params['connected'] and params.get('server_guid') and is_trassir_guid(params['server_guid']):
			server_guid = params['server_guid']
			scripts = [x['name'] for x in settings('/%s/scripts' % server_guid).ls() if x.type == 'Script']
			if params.has_key('processes'):
				for process in params['processes']:
					try:
						process(params['server_guid'])
					except Exception as err:
						write_log('   PROCESSING ERROR in %s: %s' % (process.__name__, err.message))
			#write_log('   SCRIPTS for %s: %s' % (params['connection'][0], ', '.join(scripts)))
		timeout(10, lambda: main(stage+1, **params))
	
	# disconnection from server, remove it from connections in settings-tree
	elif stage == 6 and params.has_key('connected'):
		settings('network/network_node_add')['delete_node_id'] = params['guid']
		for key in 'connection guid connected server_guid settingstree_leaves'.split():
			if params.has_key(key):
				del(params[key])
		timeout(10, lambda: main(**params))
	
	# if something went wrong
	else:
		write_log('Stage %s not done' % stage)
		write_log('---FINISH---')
		
		
		
		
write_log('---START---')

# Deleting existing network nodes
network_nodes = [x.guid for x in settings('network').ls() if x.type == 'NetworkNode']
network_nodes_number = len(network_nodes)
delete_network_nodes(network_nodes)


# TODO: check if file exists
with open('distributeScripts.servers', 'r') as connections_file:
	connections = [
			tuple(x) 
				for x in csv.reader(
						connections_file, 
						doublequote=True, skipinitialspace=True
					)
				if x and len(x) >=3 
					and not x[0].startswith('-') # conneting: - before address or CloudID
		]


# functions to process connected server
def process1(guid):
	for disk in settings('/%s/archive' % guid).ls():
		write_log('      PROCESS: DISK {0[disk_id]}, {0[capacity_gb]} GB'.format(disk))
		write_log('      PROCESS: DISK %s, Error "%s"' % (disk['disk_id'], disk.cd('stats')['last_error_code']))
	for user in [x for x in settings('/%s/users' % guid).ls() if x.type != 'UserAdd']:
		#try:
		write_log('      PROCESS: USER {0[name]}, base rights {0[base_rights]}'.format(user))
		#except KeyError: pass
		#try:
		write_log('      PROCESS: USER %s, Last login from "%s"' % (user['name'], user['last_login_address']))
		#except KeyError: pass

# timeout neede for finalizing delete_network_nodes function
timeout(
		1000 + 1000 * network_nodes_number, 
		lambda: main(connections=connections, processes=[process1])
	)




