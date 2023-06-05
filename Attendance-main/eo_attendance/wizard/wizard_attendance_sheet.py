from openerp.osv import fields, osv # type:ignore
from openerp.tools.translate import _ # type:ignore
import datetime
from datetime import datetime as dt
import time
import openerp.addons.account.account  # type:ignore
import logging
import netsvc # type:ignore
import base64

_logger = logging.getLogger(__name__)

class attendance_sheet_wizard(osv.osv_memory):
    _name = "attendance.sheet.wizard"
    _description = 'Attendance Sheet Wizard'

    _columns = {
        'persons_id' :fields.many2one('configurations.persons', 'Person' , required=True ),
        'date' :fields.datetime('Date / Time' , required=True ),
        'date_type' :fields.selection([('Check - IN','Check - IN'),('Check - OUT','Check - OUT')],string='Type' , required=True ),
        'loc_id' : fields.many2one('configurations.locations','Location' , required=True),
        'category' : fields.selection([('GPS','GPS'),('Manual','Manual'),('Wifi','Wifi'),('Other','Other')],string='Category' , required=True ),
        'attendance_sheet_id' : fields.many2one('list.attendance.sheet.reporting'),
    }

class list_attendance_sheet_reporting(osv.osv_memory):
    _name="list.attendance.sheet.reporting"
    _description = 'Attendance Sheet Report'

    def _get_name(self, cr, uid, ids, fn, args, context=None):
        result = dict.fromkeys(ids, False)
        for tr in self.browse(cr, uid, ids, context=context):
            result[tr.id] = 'Attendance Sheet Report'
        return result

    _columns = {
        'name': fields.function(_get_name, string='Name',type='char', size=128),    
        'account_period_wizard_id' : fields.many2one('account.period',string='Period',required=True),
        'attendance_sheet_report_ids': fields.one2many('attendance.sheet.wizard','attendance_sheet_id',string='Attendance Sheet'),
    }

    def get_periods(self, cr, uid, ids, context=None):
        query = """select name,id,date_start,date_stop from account_period;"""
        cr.execute(query)
        result = cr.fetchall()
        return result

    def show_summary_lines(self,cr,uid,ids,context=None):
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        tree_view = mod_obj.get_object_reference(cr, uid, 'eo_attendance', 'view_attendance_sheet_row_sum_tree')
        result= {
                'name': _('Attendance Sheet'),
                'view_mode': 'tree',
                'res_model': 'attendance.sheet.wizard',
                'context':context,
                'limit':2000,
                'views': [(tree_view  and tree_view[1] or False, 'tree')],
                'type': 'ir.actions.act_window',
                'domain': [('attendance_sheet_id', '=', ids[0])]
            }
        return result

    def reload_data(self, cr, uid, ids, data, context=None):
        # If called from web page :
        if context != None and len(context) == 5 and type(context) is dict and "from_rpc" in context:
            data = self.browse(cr, uid, ids, context=context)
            conv_date_start = dt.strptime(context['date_sart'],'%Y-%m-%d')
            conv_date_stop = dt.strptime(context['date_stop'],'%Y-%m-%d')
        else:
            data = self.browse(cr, uid, ids, context=context)[0]   
            row_summary_obj=self.pool.get('attendance.sheet.wizard') 
            old_ids=row_summary_obj.search(cr,uid,[('attendance_sheet_id','=',data.id)])
            row_summary_obj.unlink(cr,uid,old_ids)
            conv_date_start = dt.strptime(data.account_period_wizard_id.date_start,'%Y-%m-%d')
            conv_date_stop = dt.strptime(data.account_period_wizard_id.date_stop,'%Y-%m-%d')


        query_attendance_logs="""
        select al.persons_id, al.date, al.date_type, al.loc_id, al.category
        from attendance_logs al 
        order by al.date;
        """
        cr.execute(query_attendance_logs)
        result_att_log = cr.fetchall()
        filter_result = []
        for values in result_att_log:
            date = dt.strptime(values[1],'%Y-%m-%d %H:%M:%S')
            if date.month >= conv_date_start.month and date.year >= conv_date_start.year and date.month <= conv_date_stop.month and date.year <= conv_date_stop.year:
                filter_result.append(values)

        cr.execute("DELETE FROM attendance_sheet_wizard")
        for values in filter_result:
            cr.execute("insert into attendance_sheet_wizard (persons_id,date,date_type,loc_id,category) values ('%s','%s','%s','%s','%s')"%(values[0],values[1],values[2],values[3],values[4],))
        
        # If called from web page :
        if context != None and len(context) == 5 and type(context) is dict and "from_rpc" in context:
            cr.execute("select id,name from configurations_persons;")
            persons = cr.fetchall()
            lines = [] 
            for i in filter_result:
                lines.append(({'persons_id':i[0],'date':i[1],'date_type':i[2],'loc_id':i[3],'category':i[4]}))
            return lines , persons
        
        lines = []
        counter = 0
        for record in self.browse(cr, uid, ids, context=context):
            if counter != 0 :
                break
            for i in filter_result:
                lines.append((0,0,{'persons_id':i[0],'date':i[1],'date_type':i[2],'loc_id':i[3],'category':i[4]}))
            record.write({'attendance_sheet_report_ids': lines}, context=context)
            counter += 1
        return True

    def xls_export(self, cr, uid, ids, context=None):
        context = context or {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = self._name
        datas['w_id'] = ids[0]
        datas['form'] = self.read(cr, uid, ids, context=context)[0] 

        return {'type': 'ir.actions.report.xml',
                'report_name': 'pontaj_xls',
                'datas': datas
                }

    def xls_export_web(self, cr, uid, ids, data, context=None):
        context.update(bin_raw=True)
        context.update({'uid': uid})
        context.update({'data':data})
        report_pool = self.pool.get('ir.actions.report.xml')
        report_id = report_pool.search(cr,uid,[('report_name','=','pontaj_xls')])
        report = report_pool.browse(cr, uid, report_id[0], context=context)
        report_service = 'report.' + report.report_name
        service = netsvc.LocalService(report_service)
        (result, format) = service.create(cr, uid, [10], {'model': 'list.attendance.sheet.reporting'}, context=context)
        result = base64.b64encode(result)
        return result