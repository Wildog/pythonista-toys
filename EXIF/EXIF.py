import appex
from PIL import Image
from PIL.ExifTags import TAGS
from console import hud_alert
from datetime import datetime
from geopy.geocoders import Nominatim
import photos
import ui
import io
import os

def get_exif(img):
	ret = {}
	try:
		info = img._getexif()
	except:
		pass
	else:
		for tag, value in info.items():
			decoded = TAGS.get(tag, tag)
			ret[decoded] = value
	return ret
	
def get_histogram(img):
	if not img.mode.startswith('RGB'):
		img = img.convert('RGB')
	hist = img.histogram()
	max_h = float(max(hist))
	height = 180
	with ui.ImageContext(430, height) as ctx:
		a = 1
		rgb = [(1, 0, 0, a), (0, 1, 0, a), (0, 0, 1, a)]
		for i, color in enumerate(rgb):
			ui.set_color(color)
			for j, count in enumerate(hist[i*256:i*256+256]):
				bar_height = count / max_h * (height - 5)
				ui.fill_rect(2*j, height-bar_height, 2, bar_height)
		return ctx.get_image()
		
def pil2ui(imgIn):
	b = io.BytesIO()
	imgIn.save(b, 'JPEG')
	imgOut = ui.Image.from_data(b.getvalue())
	b.close()
	return imgOut
	
def size_fmt(num, suffix='B'):
	for unit in ['','Ki','Mi']:
		if abs(num) < 1024.0:
			return '{num:.2f} {unit}{suffix}'.format(num=num, unit=unit, suffix=suffix)
		num /= 1024.0
	return '{num:.1f} {unit}{suffix}'.format(num=num, unit='Gi', suffix=suffix)
	
def generate():
	if not appex.is_running_extension():
		img = photos.pick_image(show_albums=True)
		size_field.text = 'Open in Extension to view file size'
	else:
		img_path = appex.get_attachments()[0]
		size_field.text = size_fmt(os.path.getsize(img_path))
		img = appex.get_image()
	if img:
		exif = get_exif(img)
		
		orientations = {
			1: 0,
			2: 0,
			3: 180,
			4: 0,
			5: 0,
			6: 270,
			7: 0,
			8: 90
		}
		if exif.get('Orientation'):
			img = img.rotate(orientations.get(exif['Orientation'], 0))
		
		width, height = img.size
		if width > 5000 or height > 5000:
			img.thumbnail((1000, 1000))
		img_view.image = pil2ui(img)
		hist = get_histogram(img)
		hist_view.image = hist
		
		if exif.get('FocalLength'):
			focal_field.text = '%d' % (exif['FocalLength'][0] / exif['FocalLength'][1])
		else:
			focal_field.text = '--'
			
		if exif.get('FNumber'):
			f = exif['FNumber']
			aperture_field.text = '%.1f' % (float(f[0]) / f[1])
		else:
			aperture_field.text = '--'
			
		if exif.get('ExposureTime'):
			shutter_field.text = '%d/%d' % exif['ExposureTime']
		else:
			shutter_field.text = '----'
			
		iso_field.text = str(exif.get('ISOSpeedRatings', '--'))
		
		if exif.get('DateTimeOriginal'):
			date = datetime.strptime(exif['DateTimeOriginal'],  '%Y:%m:%d %H:%M:%S')
			date_field.text = date.strftime('%B %d, %Y at %H:%M')
		else:
			date_field.text = 'No date and time information'
			
		wh_field.text = '%d x %d (%.1fMP)' % (width, height, width * height / 1000000.0)
		
		camera_field.text = exif.get('Model', 'Unknown')
		
		lens = ''
		if exif.get('LensMake'):
			lens = exif['LensMake'] + '\n'
		lens += exif.get('LensModel', 'Unknown')
		lens_field.text = lens
		
		artist_field.text = exif.get('Artist', 'Unknown')
		
		programs = {
		0: 'Unknown',
		1: 'Manual',
		2: 'Program AE',
		3: 'Aperture-priority AE',
		4: 'Shutter-priority AE',
		5: 'Sleep speed',
		6: 'High speed',
		7: 'Portrait',
		8: 'Landscape',
		9: 'Bulb'}
		program_field.text = programs.get(exif.get('ExposureProgram', 0), 'Unknown')
		
		flashes = {
			0x0: 'No Flash',
			0x1: 'Fired',
			0x5: 'Fired, Return not detected',
			0x7: 'Fired, Return detected',
			0x8: 'On, Did not fire',
			0x9: 'On, Fired',
			0xd: 'On, Return not detected',
			0xf: 'On, Return detected',
			0x10: 'Off, Did not fire',
			0x14: 'Off, Did not fire, Return not detected',
			0x18: 'Auto, Did not fire',
			0x19: 'Auto, Fired',
			0x1d: 'Auto, Fired, Return not detected',
			0x1f: 'Auto, Fired, Return detected',
			0x20: 'No flash function',
			0x30: 'Off, No flash function',
			0x41: 'Fired, Red-eye reduction',
			0x45: 'Fired, Red-eye reduction, Return not detected',
			0x47: 'Fired, Red-eye reduction, Return detected',
			0x49: 'On, Red-eye reduction',
			0x4d: 'On, Red-eye reduction, Return not detected',
			0x4f: 'On, Red-eye reduction, Return detected',
			0x50: 'Off, Red-eye reduction',
			0x58: 'Auto, Did not fire, Red-eye reduction',
			0x59: 'Auto, Fired, Red-eye reduction',
			0x5d: 'Auto, Fired, Red-eye reduction, Return not detected',
			0x5f: 'Auto, Fired, Red-eye reduction, Return detected',
			0x60: 'Unknown'}
		flash_field.text = flashes.get(exif.get('Flash', 0x60))
		
		software_field.text = exif.get('Software', 'Unknown')
		
		meterings = {
			0: 'average.png',
			1: 'average.png',
			2: 'center-weighted.png',
			3: 'spot.png',
			4: 'spot.png',
			5: 'average.png',
			6: 'partial.png',
			255: 'average.png'
		}
		metering_view.image = ui.Image(meterings.get(exif.get('MeteringMode', 0), 'average.png'))
		
		if exif.get('WhiteBalance') == 1:
			balance_field.text = 'MWB'
		
		if exif.get('GPSInfo'):
			try:
				lat = [float(x)/float(y) for x, y in exif['GPSInfo'][2]]
				latref = exif['GPSInfo'][1]
				lon = [float(x)/float(y) for x, y in exif['GPSInfo'][4]]
				lonref = exif['GPSInfo'][3]
				lat = lat[0] + lat[1]/60 + lat[2]/3600
				lon = lon[0] + lon[1]/60 + lon[2]/3600
				if latref == 'S':
					lat = -lat
				if lonref == 'W':
					lon = -lon
				geolocator = Nominatim()
				loc_str = '%f, %f' % (lat, lon)
				location_field.text = loc_str + '\nDecoding location...'
				location = geolocator.reverse(loc_str)
				location_field.text = location.address
			except KeyError:
				location_field.text = 'No location data found'
		else:
			location_field.text = 'No location data found'
			
		return True
	else:
		hud_alert('No valid photo selected', icon='error')
		return False
		
if __name__ == '__main__':
	v = ui.load_view('exif')
	scroll_view = v['scrollview']
	
	img_view = scroll_view['imageview1']
	img_view.content_mode = ui.CONTENT_SCALE_ASPECT_FIT
	hist_view = scroll_view['imageview2']
	hist_view.content_mode = ui.CONTENT_SCALE_ASPECT_FIT
	
	container = scroll_view['container']
	highlights = container['view1']
	focal_field = highlights['focal']
	aperture_field = highlights['aperture']
	shutter_field = highlights['shutter']
	iso_field = highlights['iso']
	date_field = container['date']
	location_field = container['location']
	size_field = container['filesize']
	wh_field = container['wh']
	camera_field = container['camera']
	lens_field = container['lens']
	artist_field = container['artist']
	program_field = container['program']
	flash_field = container['flash']
	software_field = container['software']
	metering_view = scroll_view['metering']
	balance_field = scroll_view['balance']
	
	v.present('sheet')
	generate()
		
