# распространение скриптов
'''
<parameters>
	<company>Timofei Serov</company>
	<title>Distribute Scripts</title>
	<version>1.0</version>
</parameters>
'''
is_write_logs_1 = True
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
	# waiting connection or error message or timeout 100*500 = 500000 ms
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
		elif not connected and count <= 100 and not last_error:
			timeout(500, lambda: main(stage, count+1, **params))
		elif not connected and (count > 100 or last_error):
			write_log(' ERROR for %s: "%s"' % (params['connection'][0], last_error))
			timeout(10, lambda: main(stage+1, **params))
		else:
			timeout(10, lambda: main(100))
	# getting guid of connected server
	# TODO: or [x.guid for x in settings('/').ls() if not x.type == 'RemoteServer']
	#      other possibilities: LocalServer, Client, NetworkNode
	#      interesting list: [x.guid for x in settings('/').ls() if not x.type]
	elif stage == 3 and params.has_key('connected'):
		if params['connected']:
			guid = params['guid']
			server_guid = sorted(
					[x for x in settings('network/%s'%guid)['reachable_via_this_node'].split(',')], 
					lambda y: long(y.split('-'))[-1]
				)[-1].split('-')[0]
			if server_guid:
				params['server_guid'] = server_guid
			write_log(' GUID for %s: %s' % (params['connection'][0], server_guid))
		timeout(10, lambda: main(stage+1, **params))
	# getting name of connected server
	# TODO: 	waiting of full settings-tree loading instead
	elif stage == 4 and params.has_key('connected'):
		if params['connected'] and params.get('server_guid') and is_trassir_guid(params['server_guid']):
			server_guid = params['server_guid']
			# TODO: write as recursion
			leaves = []
			for x1 in settings('/%s'%server_guid).ls():
				leaves.append(x1.guid)
				for x2 in settings('/%s/%s' % (server_guid, x1.guid)).ls():
					leaves.append(x2.guid)
					for x3 in settings('/%s/%s/%s' % (server_guid, x1.guid, x2.guid)).ls():
						leaves.append(x3.guid)
						for x4 in settings('/%s/%s/%s/%s' % (server_guid, x1.guid, x2.guid, x3.guid)).ls():
							leaves.append(x4.guid)
			write_log('  LEAVES = %s' % len(leaves))
			try:
				server_name = settings('/%s'%server_guid)['name']
			except KeyError as e:
				if is_write_logs_1 and not count: write_log('  NO ALL LEAVES = %s, counting' % len(leaves))
				if is_write_logs_2: write_log('   c %s, LEAVES = %s' % (count, len(leaves)))
				if count < 100:
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
			#write_log('   SCRIPTS for %s: %s' % (params['connection'][0], ', '.join(scripts)))
		timeout(10, lambda: main(stage+1, **params))
	# disconnection from server, remove it from connections in settings-tree
	elif stage == 6 and params.has_key('connected'):
		settings('network/network_node_add')['delete_node_id'] = params['guid']
		for key in 'connection guid connected server_guid'.split():
			if params.has_key(key):
				del(params[key])
		timeout(10, lambda: main(**params))
	
	else:
		write_log('Stage %s not done' % stage)
		write_log('---FINISH---')
		
		
		
		
		
		
		
		
		
		
		
		
		
write_log('---START---')
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
main(connections=connections)
