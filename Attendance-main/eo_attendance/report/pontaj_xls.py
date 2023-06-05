import xlwt  # type:ignore
from openerp.addons.report_xls.report_xls import report_xls  # type:ignore
from openerp.addons.report_xls.utils import rowcol_to_cell  # type:ignore
from openerp.tools.translate import _  # type:ignore
from openerp import pooler  # type:ignore
from datetime import datetime
import datetime as dt
import logging
from styles import styles
from openerp.report import report_sxw  # type:ignore
import calendar

_logger = logging.getLogger(__name__)


class pontaj_parser(report_sxw.rml_parse):

    def __init__(self, cursor, uid, name, context):
        super(pontaj_parser, self).__init__(cursor, uid, name, context=context)
        self.localcontext.update({
        'cr': cursor,
        'uid': uid,
        'lines_get':self._lines_get,
        'return_day_of_week':self._return_day_of_week,
        'person_position':self._person_position,
        'return_month_position':self._return_month_position,
        'day_sum_seconds':self._day_sum_seconds,
        'get_context':self._get_context,
        'web_day_sum_seconds':self._web_day_sum_seconds,
        })
        self.context=context

    def _lines_get(self):
        moveline_obj = pooler.get_pool(self.cr.dbname).get('list.attendance.sheet.reporting')
        movelines = moveline_obj.browse(self.cr, self.uid, self.context.get('active_ids'))
        return movelines

    def _person_position(v, persons_pos, persons, name):
        counter = 0
        for pers in persons:
            if name == pers:
                return persons_pos[counter]
            counter += 1
        _logger.error("Error _person_position ! Name not found !")
        return 0

    def _return_month_position(v, date, months):
        counter = 0
        for i in months:
            if date.month == i[1] and date.year == i[2]:
                counter += date.day
                return counter
            else:
                counter += i[0]
        counter += date.day
        return counter

    def _return_day_of_week(v, year, month, day):
        offset = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
        week   = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        afterFeb = 1
        if month > 2: afterFeb = 0
        aux = year - 1700 - afterFeb
        # dayOfWeek for 1700/1/1 = Friday
        dayOfWeek  = 5
        # partial sum of days betweem current date and 1700/1/1
        dayOfWeek += (aux + afterFeb) * 365                  
        # leap year correction    
        dayOfWeek += aux / 4 - aux / 100 + (aux + 100) / 400     
        # sum monthly and day offsets
        dayOfWeek += offset[month - 1] + (day - 1)               
        dayOfWeek %= 7
        return week[dayOfWeek]

    def _day_sum_seconds(v, data, day, name):
        day_strtime = datetime.strptime(day,'%Y-%m-%d %H:%M:%S')
        elements = []
        for i in data:
            current_date = datetime.strptime(i['date'],'%Y-%m-%d %H:%M:%S')
            if current_date.year == day_strtime.year and name == i['persons_id'].name and current_date.month == day_strtime.month and current_date.day == day_strtime.day:
                elements.append(i)

        total_seconds = 0
        counter = 1
        for i in elements:
            if i['date_type'] == 'Check - IN' and elements[counter]['date_type'] == 'Check - OUT':
                day_in = datetime.strptime(i['date'],'%Y-%m-%d %H:%M:%S')
                day_out = datetime.strptime(elements[counter]['date'],'%Y-%m-%d %H:%M:%S')
                timedelta_obj = day_out - day_in
                total_seconds += timedelta_obj.total_seconds() / 3600
            counter += 1
            if counter >= len(elements):
                break
        return total_seconds

    def _web_day_sum_seconds(v, data, day, name):
        day_strtime = datetime.strptime(day,'%Y-%m-%d %H:%M:%S')
        elements = []
        for i in data[0]:
            current_date = datetime.strptime(i['date'],'%Y-%m-%d %H:%M:%S')
            for line in data[1]:
                if line[1] == name:
                    person = line[0]
            if current_date.year == day_strtime.year and person == i['persons_id'] and current_date.month == day_strtime.month and current_date.day == day_strtime.day:
                elements.append(i)

        total_seconds = 0
        counter = 1
        for i in elements:
            if i['date_type'] == 'Check - IN' and elements[counter]['date_type'] == 'Check - OUT':
                day_in = datetime.strptime(i['date'],'%Y-%m-%d %H:%M:%S')
                day_out = datetime.strptime(elements[counter]['date'],'%Y-%m-%d %H:%M:%S')
                timedelta_obj = day_out - day_in
                total_seconds += timedelta_obj.total_seconds() / 3600
            counter += 1
            if counter >= len(elements):
                break
        return total_seconds

    def _get_context(self):
        return self.context

class pontaj_xls(report_xls, styles):

    _column_sizes = [
        ('persons_id', 20),
    ] 

    def generate_xls_report(self, _p, _xs, data, objects, wb):
        _report_name = _('Attendance Sheet')        
        ws = wb.add_sheet('Sheet1')
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0 # Landscape
        ws.fit_width_to_pages = 1
        ws.row(0).height_mismatch = True
        ws.row(0).height = 256 * 2
        row_pos = 0      

        # Title    
        c_specs = [('report_name', 32, 0, 'text', _report_name)]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=self.cell_title)


        # write empty row to define column sizes
        c_sizes = [x[1] for x in self._column_sizes]
        c_specs = [('empty%s'%i, 1, c_sizes[i], 'text', None) for i in range(0,len(c_sizes))]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(ws, row_pos, row_data, set_column_size=True)         

        c_specs = []
        row_pos += 1
        ws.write_merge(row_pos+2, row_pos+2, 0, 0, _('Persons'), self.cell_header_center_horz_cent)
        ws.write_merge(row_pos, row_pos, 1, 1, _('Date / Time'), self.cell_header_center_horz_cent)
        date_posx = row_pos+3
        sr_cell_left = self.cell_total
        style_red = xlwt.easyxf('pattern: pattern solid, fore_colour red;')
        style_green = xlwt.easyxf('pattern: pattern solid, fore_colour bright_green;')
        style_orange = xlwt.easyxf('pattern: pattern solid, fore_colour light_orange;')


        # Write years , months , days 
        db = _p.lines_get()
        context = _p.get_context()

        date_day_start = []
        date_month_start = []
        date_year_start = []
        date_day_stop= []
        date_month_stop = []
        date_year_stop = []
        count_days_in_month = []
        counter = 1
        weekends = ['Saturday' , 'Sunday']

        # If called from web page :
        if context != None and len(context) == 8 and type(context) is dict and "from_rpc" in context:
            date_day_start = datetime.strptime(context['date_sart'],'%Y-%m-%d').day
            date_month_start = datetime.strptime(context['date_sart'],'%Y-%m-%d').month
            date_year_start = datetime.strptime(context['date_sart'],'%Y-%m-%d').year
            date_day_stop = datetime.strptime(context['date_stop'],'%Y-%m-%d').day
            date_month_stop = datetime.strptime(context['date_stop'],'%Y-%m-%d').month
            date_year_stop = datetime.strptime(context['date_stop'],'%Y-%m-%d').year
        else:
            for line in db:
                date_day_start = datetime.strptime(line['account_period_wizard_id'].date_start,'%Y-%m-%d').day
                date_month_start = datetime.strptime(line['account_period_wizard_id'].date_start,'%Y-%m-%d').month
                date_year_start = datetime.strptime(line['account_period_wizard_id'].date_start,'%Y-%m-%d').year
                date_day_stop = datetime.strptime(line['account_period_wizard_id'].date_stop,'%Y-%m-%d').day
                date_month_stop = datetime.strptime(line['account_period_wizard_id'].date_stop,'%Y-%m-%d').month
                date_year_stop = datetime.strptime(line['account_period_wizard_id'].date_stop,'%Y-%m-%d').year

        
        while date_year_start <= date_year_stop:
            ws.write(date_posx-2, counter, date_year_start, self.cell_header_center_horz_cent)
            if date_year_start == date_year_stop:
                while date_month_start <= date_month_stop:
                    ws.write(date_posx-1, counter, dt.date(1900,date_month_start,1).strftime('%B'), self.cell_header_center_horz_cent)
                    if date_month_start == date_month_stop:
                        while date_day_start <= date_day_stop:
                            ws.write(date_posx, counter, date_day_start, sr_cell_left)
                            if _p.return_day_of_week(date_year_start ,date_month_start , date_day_start ) in weekends:
                                ws.write(date_posx+1, counter, _p.return_day_of_week(date_year_start ,date_month_start , date_day_start ), style_orange)
                            else:
                                ws.write(date_posx+1, counter, _p.return_day_of_week(date_year_start ,date_month_start , date_day_start ), sr_cell_left)
                            counter += 1
                            date_day_start += 1
                        break
                    else:
                        count_days_in_month.append((calendar.monthrange(date_year_start,date_month_start)[1],date_month_start,date_year_stop))
                        while date_day_start <= calendar.monthrange(date_year_start,date_month_start)[1]:
                            ws.write(date_posx, counter, date_day_start, sr_cell_left)
                            if _p.return_day_of_week(date_year_start ,date_month_start , date_day_start ) in weekends:
                                ws.write_merge(date_posx+1, date_posx+1, counter, counter, _p.return_day_of_week(date_year_start ,date_month_start , date_day_start ), style_orange)
                            else:
                                ws.write(date_posx+1, counter, _p.return_day_of_week(date_year_start ,date_month_start , date_day_start ), sr_cell_left)
                            counter += 1
                            date_day_start += 1
                    date_month_start += 1
                    date_day_start = 1
            else:
                while date_month_start <= 12:
                    count_days_in_month.append((calendar.monthrange(date_year_start,date_month_start)[1],date_month_start,date_year_stop))
                    ws.write(date_posx-1, counter, dt.date(1900,date_month_start,1).strftime('%B'), self.cell_header_center_horz_cent)
                    while date_day_start <= calendar.monthrange(date_year_start,date_month_start)[1]:
                        ws.write(date_posx, counter, date_day_start, sr_cell_left)
                        if _p.return_day_of_week(date_year_start ,date_month_start , date_day_start ) in weekends:
                            ws.write(date_posx+1, counter, _p.return_day_of_week(date_year_start ,date_month_start , date_day_start ), style_orange)
                        else:
                            ws.write(date_posx+1, counter, _p.return_day_of_week(date_year_start ,date_month_start , date_day_start ), sr_cell_left)
                        counter += 1
                        date_day_start += 1
                    date_month_start += 1
                    date_day_start = 1
            date_year_start += 1
            date_month_start = 1
        row_pos += 5
        ws.set_horz_split_pos(row_pos)
        ws.set_vert_split_pos(1)


        # Write persons names
        persons = []
        persons_pos = []
        # If called from web page :
        if context != None and len(context) == 8 and type(context) is dict and "from_rpc" in context:
            for line in context['data'][0]:
                for pers in context['data'][1]:
                    if pers[1] not in persons and line['persons_id'] == pers[0]:
                        ws.write(row_pos, 0, pers[1], sr_cell_left)
                        persons.append(pers[1])
                        persons_pos.append(row_pos)
                        row_pos += 1
        else:
            for line in db:
                for lines in line['attendance_sheet_report_ids']:
                    if lines['persons_id'].name not in persons:
                        ws.write(row_pos, 0, lines['persons_id'].name, sr_cell_left)
                        persons.append(lines['persons_id'].name)
                        persons_pos.append(row_pos)
                        row_pos += 1
        

        # Write the persons spent amount of time
        date_at = []
        # If called from web page :
        if context != None and len(context) == 8 and type(context) is dict and "from_rpc" in context:
            for line in context['data'][0]:
                time = line['date'].split(' ')
                if time[0] not in date_at:
                    for pers in persons:
                        day_out = datetime.strptime(line['date'],'%Y-%m-%d %H:%M:%S')
                        total_hour = _p.web_day_sum_seconds(context['data'],line['date'],pers)
                        position = _p.return_month_position(day_out,count_days_in_month)
                        counter = _p.person_position(persons_pos,persons,pers)

                        if total_hour == 0:
                            continue
                        if total_hour <= 7.3:
                            ws.write(counter,position,round(total_hour,2),style_red)
                        else :
                            ws.write(counter,position,round(total_hour,2),style_green)
                date_at.append(time[0])
        else:
            for line in db[0]['attendance_sheet_report_ids']:
                time = line['date'].split(' ')
                if time[0] not in date_at:
                    for pers in persons:
                        day_out = datetime.strptime(line['date'],'%Y-%m-%d %H:%M:%S')
                        total_hour = _p.day_sum_seconds(db[0]['attendance_sheet_report_ids'],line['date'],pers)
                        position = _p.return_month_position(day_out,count_days_in_month)
                        counter = _p.person_position(persons_pos,persons,pers)

                        if total_hour == 0:
                            continue
                        if total_hour <= 7.3:
                            ws.write(counter,position,round(total_hour,2),style_red)
                        else :
                            ws.write(counter,position,round(total_hour,2),style_green)
                date_at.append(time[0])


pontaj_xls('report.pontaj_xls',
            'list.attendance.sheet.reporting',
            parser=pontaj_parser)