import datetime

def write_log(text, is_write=True):
	if is_write:
		with open('___%s.log' % __name__, 'a') as log:
			log.write('%s\t%s\n' % (datetime.datetime.now(), str(text).replace('\n', '| ')))


			
# 1:			
#    delete network nodes
def delete_network_nodes(nodes=None, node=None):
	if nodes or node:
		node = node or (nodes.pop(0) if nodes else None)
		if node in [x.guid for x in settings('network').ls() if x.type == 'NetworkNode']:
			settings('network/network_node_add')['delete_node_id'] = node
			timeout(1000, lambda: delete_network_nodes(nodes, node))
		else:
			timeout(1000, lambda: delete_network_nodes(nodes))

delete_network_nodes(
		[x.guid for x in settings('network').ls() if x.type == 'NetworkNode']
	)
settings('scripts/'+__name__)['enable'] = 0

# 2:
#    ...




