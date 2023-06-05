from openerp.osv import fields, osv # type:ignore
from openerp.tools.translate import _ # type:ignore
import time
import datetime
from openerp import pooler # type:ignore
import logging

_logger = logging.getLogger(__name__)

class attendance_logs_wizard(osv.osv_memory):
    _name = "attendance.logs.wizard"
    _description = 'Atttendance Logs Wizard'

    _columns = {
        'persons_id' :fields.many2one('configurations.persons', 'Person' , required=True ),
        'date' :fields.datetime('Date / Time' , required=True ),
        'date_type' :fields.selection([('Check - IN','Check - IN'),('Check - OUT','Check - OUT')],string='Type' , required=True ),
        'loc_id' : fields.many2one('configurations.locations','Location' , required=True),
        'category' : fields.selection([('GPS','GPS'),('Manual','Manual'),('Wifi','Wifi'),('Other','Other')],string='Category' , required=True ),
        'logs_reporting_id' : fields.many2one('list.attendance.logs.reporting'),
    }

class list_attendance_logs_reporting(osv.osv_memory):
    
    _name="list.attendance.logs.reporting"

    _description = 'Attendance Logs Report'

    def _get_name(self, cr, uid, ids, fn, args, context=None):
        result = dict.fromkeys(ids, False)
        for tr in self.browse(cr, uid, ids, context=context):
            result[tr.id] = 'Attendance Logs Report'
        return result

    _columns = {
        'name': fields.function(_get_name, string='Name',type='char', size=128),    
        'date_from': fields.datetime('From', required=True),
        'date_to':fields.datetime('To', required=True),
        'filter_name_id':fields.many2one('configurations.persons','Person'),
        'filter_location_id':fields.many2one('configurations.locations','Location'),
        'attendance_logs_report_ids': fields.one2many('attendance.logs.wizard','logs_reporting_id',string='Attendance Logs Wizard'),
    }

    def show_summary_lines(self,cr,uid,ids,context=None):
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        tree_view = mod_obj.get_object_reference(cr, uid, 'eo_attendance', 'view_attendance_logs_row_sum_tree')
        result= {
                'name': _('Attendance Logs Wizard'),
                'view_mode': 'tree',
                'res_model': 'attendance.logs.wizard',
                'context':context,
                'limit':2000,
                'views': [(tree_view  and tree_view[1] or False, 'tree')],
                'type': 'ir.actions.act_window',
                'domain': [('logs_reporting_id', '=', ids[0])]
            }
        return result


    def reload_data(self, cr, uid, ids, data, context=None):        
        data = self.browse(cr, uid, ids, context=context)[0]        

        row_summary_obj=self.pool.get('attendance.logs.wizard') 
        old_ids=row_summary_obj.search(cr,uid,[('logs_reporting_id','=',data.id)])
        row_summary_obj.unlink(cr,uid,old_ids)

        query="""
        select al.persons_id, al.date, al.date_type, al.loc_id, al.category
        from attendance_logs al 
        order by al.date;
        """
        cr.execute(query)
        result = cr.fetchall()
        filter_result = []
        for i in result:
            if i[1] >= data.date_from and i[1] <= data.date_to :
                if data.filter_name_id and data.filter_location_id:
                    if data.filter_name_id.id == i[0] and data.filter_location_id.id == i[3]:
                        filter_result.append(i)
                    continue
                if data.filter_location_id:
                    if data.filter_location_id.id == i[3]:
                        filter_result.append(i)
                    continue
                if data.filter_name_id:
                    if data.filter_name_id.id == i[0]:
                        filter_result.append(i)
                    continue
                filter_result.append(i)

        cr.execute("DELETE FROM attendance_logs_wizard")
        for values in filter_result:
            cr.execute("insert into attendance_logs_wizard (persons_id,date,date_type,loc_id,category) values ('%s','%s','%s','%s','%s')"%(values[0],values[1],values[2],values[3],values[4],))
        
        lines = []
        counter = 0
        for record in self.browse(cr, uid, ids, context=context):
            if counter != 0 :
                break
            for i in filter_result:
                lines.append((0,0,{'persons_id':i[0],'date':i[1],'date_type':i[2],'loc_id':i[3],'category':i[4]}))
            record.write({'attendance_logs_report_ids': lines}, context=context)
            counter += 1

        return True

    def xls_export(self, cr, uid, ids, context=None):
        context = context or {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = self._name
        datas['w_id'] = ids[0]
        datas['form'] = self.read(cr, uid, ids, context=context)[0]    

        return {'type': 'ir.actions.report.xml',
                'report_name': 'eo_attendance_logs_report_xls',
                'datas': datas
                }
