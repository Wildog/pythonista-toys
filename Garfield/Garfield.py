import dialogs
import urllib2
import ui
import re
import sys
import thread
from PIL import Image
from console import hud_alert
if sys.version_info[0] >= 3:
	from urllib.request import urlretrieve
else:
	from urllib import urlretrieve

prev = ''
next = ''
default_url = 'http://www.gocomics.com/garfield/'
headers = {
          'User-Agent': 'Chrome/35.0',
          }

def get_page(url):
	global prev, next
	req = urllib2.Request(url, headers=headers)
	page = urllib2.urlopen(req).read()
	prev_result = re.search('(?<=href=").*(?=" class="prev">Prev)', page)
	next_result = re.search('(?<=href=").*(?=" class="next">Next)', page)
	if prev_result:
		prev = 'http://www.gocomics.com' + prev_result.group()
	else:
		prev = url
	if next_result:
		next = 'http://www.gocomics.com' + next_result.group()
	else:
		next = url
	return page
	
def get_pic(page):
	pic_url = re.search('(?<=<img alt="Garfield" class="strip" src=").*?(?=")', page)
	return pic_url.group()
	
def get_date(page):
	date = re.search('(?<=content="Garfield by Jim Davis, ).*?(?= Via)', page)
	return date.group()
	
def get_comments(page):
	comments = []
	paragraphs = re.findall('(?<=<div class="comment-faux">).*?(?=</div>)', page, re.S)
	for para in paragraphs:
		try:
			para = para.replace('\n', '').replace('    ', '').replace('  ', '')
			user = re.search('(?<=\d">).*?(?=</a>)', para).group()
			comment_raw = re.search('(?<=<p>).*?(?=</p></p>)', para).group()
			comment = comment_raw.replace('<p>', '').replace('<br>', '\n')
			comment = re.sub('<a.*?>(.*)</a>', '\g<1> ', comment)
		except AttributeError:
			pass
		else:
			comments.append({'user': user, 'comment': comment})
	return comments

def retrieve(url):
	page = get_page(url)
	date_label.text = get_date(page)
	comments = get_comments(page)
	urlretrieve(get_pic(page), 'garfield.gif')
	indicator.stop()
	image_view.image = ui.Image.named('garfield.gif')
	data_src = CommentDataSource(comments)
	table_view.data_source = data_src
	table_view.reload()
	
def share_action(sender):
	dialogs.share_image(image_view.image)
	hud_alert('Image shared.')
	
def page_action(sender):
	indicator.start()
	thread.start_new_thread(retrieve, (eval(sender.name),))

class TableViewDelegate (object):
	def tableview_did_select(self, tableview, section, row):
		dialogs.text_dialog('Full Text', tableview.data_source.comments[section]['comment'])

	def tableview_did_deselect(self, tableview, section, row):
		pass

	def tableview_title_for_delete_button(self, tableview, section, row):
		return 'Delete'

class CommentDataSource(object):
	def __init__(self, comments):
		self.comments = comments
		
	def tableview_number_of_sections(self, tableview):
		return len(self.comments)

	def tableview_number_of_rows(self, tableview, section):
		return 1

	def tableview_cell_for_row(self, tableview, section, row):
		cell = ui.TableViewCell()
		cell.selectable = True
		cell.text_label.text = self.comments[section]['comment']
		return cell

	def tableview_title_for_header(self, tableview, section):
		return self.comments[section]['user']

	def tableview_can_delete(self, tableview, section, row):
		return False

	def tableview_can_move(self, tableview, section, row):
		return False

	def tableview_delete(self, tableview, section, row):
		pass

	def tableview_move_row(self, tableview, from_section, from_row, to_section, to_row):
		pass

v = ui.load_view('Garfield')
views = v['scrollview1'].subviews
image_view = views[0]
prev_button = views[1]
next_button = views[2]
share_button = views[3]
date_label = views[4]
table_view = views[5]

image_view.content_mode = ui.CONTENT_SCALE_ASPECT_FIT
table_view.delegate = TableViewDelegate()

indicator = ui.ActivityIndicator()
indicator.style = ui.ACTIVITY_INDICATOR_STYLE_WHITE_LARGE
indicator.background_color = (0.0, 0.0, 0.0, 0.5)
indicator.x = (ui.get_screen_size()[0] - 60) / 2
indicator.y = (image_view.height - 60) / 2
indicator.width = 60
indicator.height = 60
indicator.corner_radius = 10
v.add_subview(indicator)

v.present('sheet')
indicator.start()
retrieve(default_url)
