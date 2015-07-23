# Переключение дисков
'''
<parameters>
	<company>Тимофей Серов / DSSL</company>
	<title>StoragesCheck</title>
	<version>2.0</version>
	<parameter>
		<type>string</type>
		<name>Локальные диски</name>
		<id>local_drives</id>
		<value></value>
	</parameter>
	<parameter>
		<type>string</type>
		<name>Удалённые диски</name>
		<id>remote_drives</id>
		<value></value>
	</parameter>
	<parameter>
		<type>integer</type>
		<name>Периодичность проверки, с</name>
		<id>check_period</id>
		<value>60</value>
	</parameter>
</parameters>
'''



import re, os, datetime

# --- START --- service functions ---
def log_text(text, show_messages=True):
	with open('__%s.log' % __name__, 'a') as f:
		f.write('%s\t%s\n' % (datetime.datetime.now(), str(text)))
	if show_messages:
		message(str(text))	
def list_sort_string(x):
	x = list(x); x.sort()
	return ''.join(x)
def set_settings(settings_name, settings_parameter, settings_value):
	try:
		if settings(settings_name)[settings_parameter] != settings_value:
			settings(settings_name)[settings_parameter] = settings_value
	except KeyError, err:
		#alert(err.message)
		pass
def set_drive_readonly(drive, readonly=True):
	set_settings('archive/'+drive, 'read_only', int(readonly))
def set_drive_enable(drive, enable=True):
	set_settings('archive/'+drive, 'enable', int(enable))
def set_drive_rw(drive):
	set_drive_enable(drive, True)
	set_drive_readonly(drive, False)
def set_drive_ro(drive):
	set_drive_enable(drive, True)
	set_drive_readonly(drive, True)
def set_drive_disabled(drive):
	set_drive_enable(drive, False)
	set_drive_readonly(drive, False)
	
def get_drive_info_1_for_windows(drive):
	command = 'wmic logicaldisk get caption,description,drivetype,providername,volumename'
	
	return {'type': , 'address'}

def test_drive_on_trassir_error(drive):
	return bool( settings('archive/'+drive+'/stats')['last_error_code'] )

def test_drive_on_archive_folders(drive):
	return os.access(drive+':\\TrassirArchive-3.1', os.F_OK) or os.access(drive+':\\TrassirArchive', os.F_OK)

def test_drive_on_ping(drive):
	return True
	
def test_drive_on_file_write(drive):
	return True
	
def test_drive_on_total_volume(drive):
	return True
	
def test_drive_on_free_volume(drive):
	return True
	
def test_drive(drive):
	return all([
			test_drive_on_archive_folders(drive), 
			test_drive_on_file_write(drive), 
			test_drive_on_ping(drive), 
			test_drive_on_free_volume(drive), 
			test_drive_on_total_volume(drive)
		])
# --- END --- service functions ---
	


locals, remotes = map(
		lambda x: set(list(re.sub('[^c-zC-Z]', '', x).lower())),
		(local_drives, remote_drives))
remotes = remotes - locals
		
		
def archive_check(counter=0, accs0=set(), inaccs0=set()):
	accs, inaccs = set(), set()
	others = set([x.guid for x in settings('archive').ls()]) - remotes - locals
	writelog('others = %s' % others)
	for drive in others:				set_drive_disabled(drive)
	for drive in remotes:			accs.add(drive) if is_accessible(drive) else inaccs.add(drive)
	if not (accs0 == accs and inaccs0 == inaccs and len(accs)+len(inaccs)):
		if len(accs):
			for drive in locals:		set_drive_ro(drive)
			for drive in accs:			set_drive_rw(drive)
			for drive in inaccs:		set_drive_disabled(drive)
		else:
			for drive in locals:		set_drive_rw(drive)
			for drive in inaccs:		set_drive_disabled(drive)
	counter = counter if counter < 10 else 0
	writelog('locals = %s, accs = %s, inaccs = %s' % (locals, accs, inaccs))
	timeout(check_period*1000, lambda: archive_check(counter+1, accs, inaccs))


timeout(0, archive_check)
