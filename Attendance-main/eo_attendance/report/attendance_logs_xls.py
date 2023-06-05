import xlwt # type:ignore
from openerp.addons.report_xls.report_xls import report_xls # type:ignore
from openerp.addons.report_xls.utils import rowcol_to_cell  # type:ignore
from openerp.tools.translate import _  # type:ignore
from openerp import pooler # type:ignore
from datetime import datetime
import logging
from styles import styles
from openerp.report import report_sxw  # type:ignore

_logger = logging.getLogger(__name__)


class eo_attendance_logs_parser(report_sxw.rml_parse):

    def __init__(self, cursor, uid, name, context):
        super(eo_attendance_logs_parser, self).__init__(cursor, uid, name, context=context)
        self.localcontext.update({
        'cr': cursor,
        'uid': uid,
        'lines_get':self._lines_get
        })
        self.context=context

    def _lines_get(self):
        moveline_obj = pooler.get_pool(self.cr.dbname).get('list.attendance.logs.reporting')
        movelines = moveline_obj.browse(self.cr, self.uid, self.context.get('active_ids'))
        return movelines

class eo_attendance_logs_report_xls(report_xls, styles):

    _column_sizes = [
        ('persons_id', 30),
        ('date', 25),
        ('date_type', 20),
        ('loc_id', 40),
        ('category', 20),     
    ]
    
    def generate_xls_report(self, _p, _xs, data, objects, wb):
        cr = self.cr
        uid = self.uid
        _report_name = _('Attendance Logs')        
        ws = wb.add_sheet('Sheet1')
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0 # Landscape
        ws.fit_width_to_pages = 1
        ws.row(0).height_mismatch = True
        ws.row(0).height = 256 * 2
        row_pos = 0     

        # Title    
        c_specs = [('report_name', 11, 0, 'text', _report_name)]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.cell_title)


        # write empty row to define column sizes
        c_sizes = [x[1] for x in self._column_sizes]
        c_specs = [('empty%s'%i, 1, c_sizes[i], 'text', None) for i in range(0,len(c_sizes))]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(ws, row_pos, row_data, set_column_size=True)         

        cr = self.cr
        uid = self.uid
        c_specs = []
        row_pos += 1

        ws.write_merge(row_pos, row_pos+1, 0, 0, _('Persons'), self.cell_header_center_horz_cent)
        ws.write_merge(row_pos, row_pos+1, 1, 1, _('Date / Time'), self.cell_header_center_horz_cent)
        ws.write_merge(row_pos, row_pos+1, 2, 2, _('Date Type'), self.cell_header_center_horz_cent)
        ws.write_merge(row_pos, row_pos+1, 3, 3, _('Location'), self.cell_header_center_horz_cent)
        ws.write_merge(row_pos, row_pos+1, 4, 4, _('Category'), self.cell_header_center_horz_cent)

        row_pos += 2
        ws.set_horz_split_pos(row_pos)
        sr_cell_left = self.cell_total
        nr_style = self.cell_style_decimal

        for line in _p.lines_get():
            for lines in line['attendance_logs_report_ids']:
                ws.write_merge(row_pos, row_pos+1, 0, 0, _(lines['persons_id'].name), sr_cell_left)
                ws.write_merge(row_pos, row_pos+1, 1, 1, _(lines['date']), sr_cell_left)
                ws.write_merge(row_pos, row_pos+1, 2, 2, _(lines['date_type']), sr_cell_left)
                ws.write_merge(row_pos, row_pos+1, 3, 3, _(lines['loc_id'].name), sr_cell_left)
                ws.write_merge(row_pos, row_pos+1, 4, 4, _(lines['category']), sr_cell_left)

                row_pos += 1
                row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
                row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=nr_style)  


eo_attendance_logs_report_xls('report.eo_attendance_logs_report_xls',
                                'list.attendance.logs.reporting',
                                parser=eo_attendance_logs_parser)