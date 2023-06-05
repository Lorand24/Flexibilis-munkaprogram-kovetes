<html>
    <head>
        <style type="text/css">
            ${css}
        </style>
    </head>
    <body>
        <% setLang(user.lang) %>
        <% rec_lines = get_lines(cr, uid, data)['result'] %>
        <% f = helper.get_filters(data, user.lang) %>       
        
        <div class="report-holder">
            <h1 class="report-title"><span>${_('Attendance Logs')}</span></h1>
            <table class="filters">
                <tr>
                    <td><span>${f['date_from']['label']}: </span>${formatLang(f['date_from']['value'] or '', date=True)}</td>
                    <td><span>${f['date_to']['label']}: </span>${formatLang(f['date_to']['value'] or '', date=True)}</td>

                    <td><span>${f['persons_id']['label']}: </span>${f['persons_id']['value']}</td>
                    <td><span>${f['loc_id']['label']}: </span>${f['loc_id']['value']}</td>
                </tr>
            </table>
           
            <table class="main-table">       
                <thead> 
                    <tr>
                        <th width="25%">${_('Person')}</th>
                        <th width="20%">${_('Date / Time')}</th>                        
                        <th width="15%">${_('Type')}</th>
                        <th width="25%">${_('Location')}</th>
                        <th width="15%">${_('Category')}</th>
                    </tr>    
                    <tbody>
                        %for line in _p.get_lines():
                            <tr >
                                <td class="center">${ nrcrt() }</td>
                                <td>${ line['person_id'] }</td>
                                <td>${ line['date'] }</td>
                                <td>${ line['date_type']}</td>
                                <td>${ line['loc_id']}</td>                                
                                <td>${ line['category']}</td>
                            </tr>
                        %endfor
                    </tbody>            
                </thead>                
            </table>

        </div>
    </body>
</html>