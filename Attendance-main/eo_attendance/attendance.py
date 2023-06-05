from osv import fields, osv, expression # type:ignore
from openerp.tools.translate import _ # type:ignore
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT # type:ignore
import time
import datetime
from datetime import timedelta
from datetime import datetime as dt
from openerp.osv import fields, osv # type:ignore
import openerp # type:ignore
import openerp.exceptions # type:ignore
import logging

_logger = logging.getLogger(__name__)

class attendance_logs(osv.osv):
    _name = "attendance.logs"
    _description = 'Atttendance Logs'

    _columns = {
        'persons_id' :fields.many2one('configurations.persons', string='Person' , required=True ),
        'date' :fields.datetime('Date / Time' , required=True ),
        'date_type' :fields.selection([('Check - IN','Check - IN'),('Check - OUT','Check - OUT')],string='Type' , required=True ),
        'image' : fields.binary('Attendance Image'),
        'loc_id' : fields.many2one('configurations.locations',string='Location' , required=True),
        'category' : fields.selection([('GPS','GPS'),('Manual','Manual'),('Wifi','Wifi'),('Other','Other')],string='Category' , required=True ),
        'status' : fields.selection([('Check - IN','Checked - IN'),('Check - OUT','Checked - OUT')],string='Status'),
        'create_date': fields.datetime('Create Date',readonly=True),
    }

    _order = "create_date desc"

    # Set default value persons
    def _get_persons_id(self, cr, uid, ids, context=None):
        cr.execute("select id from configurations_persons where user_id = ('%s');"%(uid,))
        result = cr.fetchall()
        if not result:
            return ''
        return result[0][0]

    # Get default value location
    def get_loc_id(self, cr, uid, ids, context=None):
        cr.execute("select location_id from configurations_persons where user_id = ('%s');"%(uid,))
        result = cr.fetchall()
        if not result:
            return ''
        return result[0][0]

    # Get todays date_type,date,status 
    def _get_date_type_today(self, cr, uid, ids, context=None):
        day = time.strftime('%Y-%m-%d')
        pers_id = self._get_persons_id(cr, uid, ids, context)
        if not pers_id:
            return ''
        cr.execute("select date_type,date,status from attendance_logs where to_char(date, 'yyyy-MM-dd') = ('%s') and persons_id = ('%s') order by date ;"%(day,pers_id,))
        result = cr.fetchall()
        if not result:
            return ''
        return result

    # Get default value date_type
    def is_check_in(self, cr, uid, ids, context=None):
        result = self._get_date_type_today(cr, uid, ids, context)
        if not result:
            return 'Check - OUT'
        return result[-1][2]

    # Checkin checkout default checker 
    def _is_check_in_out(self, cr, uid, ids, context=None):
        result = self._get_date_type_today(cr, uid, ids, context)
        if not result:
            return 'Check - IN'
        elif result[-1][0] == 'Check - OUT':
            return 'Check - IN'
        else :
            return 'Check - OUT'
        
    # Calculate total hours spent for message 
    def get_total_hours_spent(self, cr, uid, ids, context=None):
        result = self._get_date_type_today(cr, uid, ids, context)
        total_time_spent_timedl = []
        for i in range(len(result)-1):
            if result[i][0] == 'Check - IN' and result[i+1][0] == 'Check - OUT':
                day_in = dt.strptime(result[i][1],'%Y-%m-%d %H:%M:%S')
                day_out = dt.strptime(result[i+1][1],'%Y-%m-%d %H:%M:%S')
                timedelta_obj = day_out - day_in
                total_time_spent_timedl.append(timedelta_obj.total_seconds())
        seconds = 0
        for i in total_time_spent_timedl:
            seconds += i
        if not result:
            return ''
        return seconds , result[-1][0] , result[0][1] , result[len(result) - 1][1]

    # Check-IN button function
    def check_in(self, cr, uid, ids, context=None):
        product_obj = self.pool.get('attendance.logs')

        # If called from web page :
        if context != None and len(context) == 2 and type(context) is dict:
            if context["from_rpc"] == 1:
                product_obj.create(cr, uid,{
                    'date_type' : 'Check - IN',
                    'status' : 'Check - IN',
                })
                return True


        product_obj.write(cr, uid, ids, {
                'date_type' : 'Check - IN',
                'status' : 'Check - IN',
            })

        result = self._get_date_type_today(cr, uid, ids, context)
        if not result: # First checkin of the day with saved instance
            product_obj.create(cr, uid,{
                    'date_type' : 'Check - IN',
                    'status' : 'Check - IN',
                })
            return {
              'type': 'ir.actions.client',
              'tag': 'reload',
            }
        if result[-1][0] in 'Check - OUT':
            product_obj.create(cr, uid,{
                    'date_type' : 'Check - IN',
                    'status' : 'Check - IN',
                })

        return {
          'type': 'ir.actions.client',
          'tag': 'reload',
        }

    # Check-OUT button function
    def check_out(self, cr, uid, ids, context=None):
        product_obj = self.pool.get('attendance.logs')

        # If called from web page :
        if context != None and len(context) == 2 and type(context) is dict:
            if context["from_rpc"] == 1:
                product_obj.create(cr, uid,{
                    'date_type' : 'Check - OUT',
                    'status' : 'Check - OUT',
                })
                return True
        

        product_obj.write(cr, uid, ids, {
                'status' : 'Check - OUT',
            })

        result = self._get_date_type_today(cr, uid, ids, context)
        if len(result) >= 2 and result[len(result)-2][0] in 'Check - IN' and result[len(result)-1][0] in 'Check - IN': 
            product_obj.write(cr, uid, ids, {
                'date_type' : 'Check - OUT',
                'status' : 'Check - OUT',
            })
        elif result[-1][0] in 'Check - IN':
            product_obj.create(cr, uid,{
                    'date_type' : 'Check - OUT',
                    'status' : 'Check - OUT',
                })
        return {
          'type': 'ir.actions.client',
          'tag': 'reload',
        }

    # Warns you if you try to create between an existing checkin checkout
    def onchange_date(self, cr, uid, ids, changed_date, context=None):
        pers_id = self._get_persons_id(cr, uid, ids, context)
        if not pers_id:
            return ''
        cr.execute("select date_type,date,status from attendance_logs where persons_id = ('%s') order by date ;"%(pers_id,))
        result = cr.fetchall()
        if not result:
            return 
        current_date = dt.strptime(changed_date,'%Y-%m-%d %H:%M:%S')
        counter = 1
        res = {}
        for date in result:
            day_in = dt.strptime(date[1],'%Y-%m-%d %H:%M:%S')
            day_out = dt.strptime(result[counter][1],'%Y-%m-%d %H:%M:%S')
            if date[0] == 'Check - IN' and result[counter][0] == 'Check - OUT' and day_in < current_date and day_out > current_date :
                res = {'warning': {
                    'title': _('Warning Create Date'),
                    'message': _('You are trying to create between an existing checkin checkout ! Either modify them or delete them and then create new ones .')
                }}
                return res
            counter += 1
            if counter >= len(result):
                break
        return True

    _defaults = {
        'loc_id' : get_loc_id,
        'date_type' : _is_check_in_out,
        'persons_id' : _get_persons_id,
        'date' : lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'category' : 'Manual',
        'status' : is_check_in,
    }
attendance_logs()

class configurations_persons(osv.osv):
    _name = "configurations.persons"
    _description = 'Users'

    _columns = {
        'name': fields.char('Name' , required=True),
        'username' : fields.char('UserName' , required=True),
        'password' : fields.char('Password' ,required=True, size=64),
        'image' : fields.binary('Image'),
        'user_id' : fields.many2one('res.users',string='User',required=True),
        'location_id' : fields.many2one('configurations.locations',string='Default Location',required=True),
    }

    _sql_constraints = [
        ('username_key', 'UNIQUE (username)',  'You can not have two users with the same username !')
    ]

    def _get_persons_username(self, cr, uid, ids, context=None):
        cr.execute("select login from res_users where id = ('%s');"%(uid,))
        return cr.fetchall()

    def _get_persons_password(self, cr, uid, ids, context=None):
        cr.execute("select password from res_users where id = ('%s');"%(uid,))
        return cr.fetchall()

    _defaults = {
        'user_id' : lambda self, cr, uid, ctx=None: uid,
        'password' : _get_persons_password,
        'username' : _get_persons_username,
    }
configurations_persons()

class configurations_locations(osv.osv):
    _name = "configurations.locations"
    _description = 'Locations'

    _columns = {
        'name' : fields.char('Name' , required=True),
        'locwifi_id' : fields.many2many('wifi.points','locations_wifi_points_rel','location_id','wifipoint_id','Location Wifi Points' , required=True),
        'description' : fields.char('Description'),
        'image' : fields.binary('Location Image'),
    }
configurations_locations()

class wifi_points(osv.osv):
    _name = "wifi.points"
    _description = 'Wifi Points'

    _columns = {
        'name' : fields.char('Name' , required=True),
        'wifi_password' : fields.char('Wifi Password'),
    }
wifi_points()
