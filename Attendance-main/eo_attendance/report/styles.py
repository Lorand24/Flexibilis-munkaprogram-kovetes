from openerp import pooler
from openerp.tools.translate import _
import xlwt
from openerp.addons.report_xls.report_xls import report_xls

class styles(object):

	_xs = report_xls.xls_styles
	cell_title = xlwt.easyxf(_xs['xls_title'] + 'alignment: vertical center')
	cell_header_left = xlwt.easyxf(_xs['left'] + _xs['bold'] + _xs['borders_all'] + _xs['fill'])     
	cell_header_blue_left = xlwt.easyxf(_xs['bold'] + _xs['fill_blue'] + _xs['borders_all'] + _xs['left'])
	cell_left_fill_yellow = xlwt.easyxf(_xs['bold'] + _xs['fill'] + _xs['borders_all'] + _xs['left'])          
	cell_fill_yellow = xlwt.easyxf(_xs['fill'])
	cell_left_top = xlwt.easyxf(_xs['left'] + 'alignment: vertical top')      
	cell_left = xlwt.easyxf(_xs['left'])
	cell_right = xlwt.easyxf(_xs['right'])
	cell_right_bold = xlwt.easyxf(_xs['right'] + _xs['bold'])
	cell_row_grey = xlwt.easyxf('pattern: pattern solid, fore_color 22;')
	cell_header_center_horz_cent = xlwt.easyxf(_xs['bold'] + _xs['fill'] + _xs['borders_all'] + _xs['center'] + 'alignment: vertical center')
	cell_style_date_center = xlwt.easyxf(_xs['borders_all'] + _xs['center'], num_format_str = report_xls.date_format)