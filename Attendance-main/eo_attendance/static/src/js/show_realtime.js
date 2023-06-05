openerp.eo_attendance = function(instance)
{
	instance.web.form.widgets.add('clock_from', 'instance.eo_attendance.clock_from');
    instance.eo_attendance.clock_from = instance.web.form.FieldChar.extend(
        {
        template:"clock_from",
        init: function (view, code) {
            this._super(view, code);
        },

        start: function() {
            var name = this.name;
            var self = this;
            var model = new instance.web.Model('attendance.logs');
            model.call("get_total_hours_spent",[[this.view.datarecord.id]],{context: new instance.web.CompoundContext()}).then(function(result)
            {
                if (result.length === 0){
                    if(name === 'image'){
                        self.$el.text(' ');
                    }else{
                        self.$el.text('You are yet to check in today !');
                    }
                }else if (result[1] === 'Check - OUT'){
                    if (name === 'category'){
                        var date = new Date(null);
                        date.setSeconds(result[0]);
                        var timer = date.toISOString().substr(11, 8);
                        var firstCheckin = self.string_to_date(result[2]);
                        self.$el.text('Today you first checked in at ' + result[2].substr(0, 10) + ' ' + firstCheckin.toString().substr(16, 8) + ' , total amount of time spent today : [' + timer + '].');
                    }else{
                        self.$el.text('You are checked out .');
                    }
                }else{
                    if (name === 'image'){
                        var time = self.time(0,result[3]);
                        var firstCheckin = self.string_to_date(result[3]);
                        self.$el.text('You are checked in starting from : ' + result[3].substr(0, 10) + ' ' + firstCheckin.toString().substr(16, 8) + ' , total amount of time spent from current checkin : [' + time + '].');
                        setInterval(function(){
                        time = self.time(0,result[3]);
                        self.$el.text('You are checked in starting from : ' + result[3].substr(0, 10) + ' ' + firstCheckin.toString().substr(16, 8) + ' , total amount of time spent from current checkin : [' + time + '].');},1000);
                    }
                    else{
                        var timer = self.time(result[0],result[3]);
                        var firstCheckin = self.string_to_date(result[2]);
                        self.$el.text('Today you first checked in at ' + result[2].substr(0, 10) + ' ' + firstCheckin.toString().substr(16, 8) + ' , total amount of time spent today : [' + timer + '].');
                        setInterval(function(){
                        timer = self.time(result[0],result[3]);
                        self.$el.text('Today you first checked in at ' + result[2].substr(0, 10) + ' ' + firstCheckin.toString().substr(16, 8) + ' , total amount of time spent today : [' + timer + '].');},1000);
                    }
                }
            });
        },

        time: function(totalSeconds,startTime) {
            var plusDifference = this.get_seconds(startTime);
            var date = new Date(null);
            date.setSeconds(totalSeconds + plusDifference);
            var result = date.toISOString().substr(11, 8);
            return result;
        },

        get_seconds: function(startTime) {
            const currentTime = new Date();
            const startDate = this.string_to_date(startTime);
            const plusDifference = Math.round(Math.abs(((currentTime - startDate) / 1000)));
            return plusDifference;
        },

        string_to_date: function(strDate) {
            const [dateValues, timeValues] = strDate.split(' ');
            const [year, month, day] = dateValues.split('-');
            const [hours, minutes, seconds] = timeValues.split(':');
            const date = new Date(year, month-1, day, hours, minutes, seconds);
            date.setHours(date.getHours() + 2);
            return date;
        }

    });
}