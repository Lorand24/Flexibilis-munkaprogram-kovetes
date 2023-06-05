<!DOCTYPE html>
<html>
	<head>
		<meta http-equiv="content-type" content="text/html; charset=utf-8" />
		<meta name="viewport" content="width=device-width, initial-scale=1">
		<title>Attendance</title>
		<style>
			#result{
				font-size: 0.8rem;
			}
		</style>
		<script type="text/javascript">
			function realtime_message(result) {
				if (result.length === 0){
                    document.getElementById('result').innerText = '\nYou are yet to check in today !';
                }else if (result[1] === 'Check - OUT'){
                    var date = new Date(null);
                    date.setSeconds(result[0]);
                    var timer = date.toISOString().substr(11, 8);
                    var firstCheckin = string_to_date(result[2]);

                    document.getElementById('result').innerText = 'Today you first checked in at :    \t\t\t|' + result[2].substr(0, 10) + ' ' + firstCheckin.toString().substr(16, 8) + '\nTotal amount of time spent today : \t\t\t| ' + timer + '.' + '\n\nYou are checked out !';
                }else{
                    var timer = time(result[0],result[3]);
                    var firstCheckin = string_to_date(result[2]);
                    var currentTimer = time(0,result[3]);
                    var currentCheckin = string_to_date(result[3]);

                    document.getElementById('result').innerText = 'You are checked in starting from : \t\t\t|' + result[3].substr(0, 10) + ' ' + currentCheckin.toString().substr(16, 8) + '\nTotal amount of time spent from current checkin : \t| ' + currentTimer + '\n' + 'Today you first checked in at : \t\t\t|' + result[2].substr(0, 10) + ' ' + firstCheckin.toString().substr(16, 8) + '\nTotal amount of time spent today : \t\t\t| ' + timer + '';

                    setInterval(function(){
                    timer = self.time(result[0],result[3]);
                    currentTimer = time(0,result[3]);
                    document.getElementById('result').innerText = 'You are checked in starting from : \t\t\t|' + result[3].substr(0, 10) + ' ' + currentCheckin.toString().substr(16, 8) + '\nTotal amount of time spent from current checkin : \t| ' + currentTimer + '\n' + 'Today you first checked in at : \t\t\t|' + result[2].substr(0, 10) + ' ' + firstCheckin.toString().substr(16, 8) + '\nTotal amount of time spent today : \t\t\t| ' + timer + '';},1000);
                }
			}

			function time(totalSeconds,startTime) {
	            var plusDifference = this.get_seconds(startTime);
	            var date = new Date(null);
	            date.setSeconds(totalSeconds + plusDifference);
	            var result = date.toISOString().substr(11, 8);
	            return result;
	        }

	        function get_seconds(startTime) {
	            const currentTime = new Date();
	            const startDate = this.string_to_date(startTime);
	            const plusDifference = Math.round(Math.abs(((currentTime - startDate) / 1000)));
	            return plusDifference;
	        }

	        function string_to_date(strDate) {
	            const [dateValues, timeValues] = strDate.split(' ');
	            const [year, month, day] = dateValues.split('-');
	            const [hours, minutes, seconds] = timeValues.split(':');
	            const date = new Date(year, month-1, day, hours, minutes, seconds);
	            date.setHours(date.getHours() + 2);
	            return date;
	        }
		</script>
	</head>
	<body>
		<div style="display: grid; height: 150px; background-color: #DBDBDB; padding-bottom: 100px;grid-template-columns: 450px 1fr 1fr; grid-template-rows: 100px 100px;">

			<div class="box1">
				<img src="./img/company_logo.png" >
			</div>
			<div class="box2">
				<?php
				ini_set('session.gc_maxlifetime', 35600);
				session_start();
				require_once __DIR__ . '/src/OpenERP.php';
				include 'settings.php';

				// Check if username and password was given
				if(isset($_GET["username"]) and isset($_GET["password"])){
					$_SESSION["login"] = $_GET["username"];
					$_SESSION["password"] = $_GET["password"];
					$login = $_SESSION['login'];
					$password = $_SESSION['password'];
				}elseif(isset($_SESSION['login']) and isset($_SESSION['password'])){
					$login = $_SESSION['login'];
					$password = $_SESSION['password'];
				}else{
					echo"Session expired or no username / password given !";
				}

				// login 
				$oe = new OpenERP($url, $db);
				$oe->login($login, $password);
				$context = array(
					'lang' => "en_US",
					'from_rpc' => 1
				);

				// Get user id 
				$user_id = array(
					'model' => 'res.users',
					'fields' => array('id'),
					'domain' => array(array('login', '=', $login)),
				);
				$value_user_id = $oe->read($user_id);
				$user_id = $value_user_id['records'][0]['id'];

				// Get admin group id 
				$group_id = array(
					'model' => 'res.groups',
					'fields' => array('id'),
					'domain' => array(array('name', '=', 'Admin')),
				);
				$group_id = $oe->read($group_id);
				$group_id = $group_id['records'][0]['id'];

				// Get if user is admin or not
				$access_right = array(
					'model' => 'res.users',
					'fields' => array('groups_id'),
					'domain' => array(array('id', '=', $user_id)),
				);
				$access_right = $oe->read($access_right);
				$access_right = $access_right['records'][0]['groups_id'];
				$access_right = in_array(43,$access_right);

				// Get company logo
				// $web_logo = array(
				// 	'model' => 'res.company',
				// 	'fields' => array('logo_web'),
				// 	'domain' => array(),
				// );
				// $logo = $oe->read($web_logo);
				// print_r($logo['records'][0]);

				// Get person name and location name
				$query = array(
					'model' => 'configurations.persons',
					'fields' => array('name' , 'location_id'),
					'domain' => array(array('user_id', '=', $user_id)),
				);
				$value = $oe->read($query);

				// Get current status 
				$ean = $oe->call(array(
					'model' => 'attendance.logs',
					'method' => 'is_check_in',
					'args' => array($user_id),
					'context' => $context,
				));
				$status = $ean;

				// Get datetime and total hours spent 
				$ean = $oe->call(array(
					'model' => 'attendance.logs',
					'method' => 'get_total_hours_spent',
					'args' => array($user_id),
					'context' => $context,
				));
				$total_hours_spent = $ean;

				// Get periods for selection
				$ean = $oe->call(array(
					'model' => 'list.attendance.sheet.reporting',
					'method' => 'get_periods',
					'args' => array($user_id),
					'context' => $context,
				));
				$periods = $ean;

				// Print Data
				echo "<h2>Attendance</h2>";
				echo "<pre>";
				echo "Person : \t\t\t\t\t\t    |";
				print_r($value['records'][0]['name']);
				echo "<br/>";
				echo "Default Location :  \t\t\t\t\t    |";
				print_r($value['records'][0]['location_id'][1]);
				echo "<br/>";
				echo "Status : \t\t\t\t\t\t    |$status";
				echo "<br/>";
				echo "</pre>";
				echo "<pre id='result' > </pre>";
				echo "<script type='text/javascript'>"."realtime_message(" . json_encode($total_hours_spent) .");"."</script>";

				// Call button functions 
				if($_SERVER['REQUEST_METHOD'] == 'POST' and isset($_POST['checking_in'])){
					checking_in($user_id, $oe, $context, $login, $password);
				}
				if($_SERVER['REQUEST_METHOD'] == 'POST' and isset($_POST['checking_out'])){
					checking_out($user_id, $oe, $context, $login, $password);
				}
				if($_SERVER['REQUEST_METHOD'] == 'POST' and isset($_POST['export_attendance_sheet'])){
					printing_attendance_sheet($user_id, $oe, $context,$periods);
				}


				function checking_in($user_id, $oe, $context, $login, $password){
					$ean = $oe->call(array(
						'model' => 'attendance.logs',
						'method' => 'check_in',
						'args' => array($user_id, $context),
						'context' => $context,
					));
					header("Location:attendance.php?username=".$login."&password=".$password);
					exit();
				}

				function checking_out($user_id, $oe, $context, $login, $password){
					$ean = $oe->call(array(
						'model' => 'attendance.logs',
						'method' => 'check_out',
						'args' => array($user_id, $context),
						'context' => $context,
					));
					header("Location:attendance.php?username=".$login."&password=".$password);
					exit();
				}

				function printing_attendance_sheet($user_id, $oe, $context, $periods){
					$pos = $_POST['periods'];
					if($_POST['periods'] == NULL){
						echo "You need to choose a period in order to export attendance sheet !";
						return ;
					}
					$period = $periods[$pos];
					$context['period_id'] = $period[1];
					$context['date_sart'] = $period[2];
					$context['date_stop'] = $period[3];

					$data = $oe->call(array(
						'model' => 'list.attendance.sheet.reporting',
						'method' => 'reload_data',
						'args' => array($user_id, [], $context),
						'context' => $context,
					));

					$result = $oe->call(array(
						'model' => 'list.attendance.sheet.reporting',
						'method' => 'xls_export_web',
						'args' => array($user_id, $data, $context),
						'context' => $context,
					));

					ob_clean();
					$file = 'AttendanceSheet.xls';
					header("Content-type:application/xls");
					header('Content-Disposition: attachment; filename=' . $file);
					$report_file = base64_decode($result);
					echo $report_file;
					die();
				}
				?>
				<form action="attendance.php" method="post">
					<input id="checking_in" type="submit" <?php if($status == 'Check - IN') {?> style="display: none;" <?php } ?> class="button" name="checking_in" value="Checking-in" style="height:25px; width:100px; background-color: red; border-color: black; color: white;"/>
					<input id="checking_out" type="submit" <?php if($status == 'Check - OUT') {?> style="display: none;" <?php } ?> class="button" name="checking_out" value="Checking-out" style="height:25px; width:100px; background-color: red; border-color: black; color: white;"/>
				</form>
			</div>
			<div class="box3">
				<form action="attendance.php" method="post" <?php if($access_right != 1) {?> style="display: none;" <?php } ?>>
					<p>Period: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|
						<select name="periods" id="periods">
						<option value="" disabled selected>Choose Period</option>
						<?php
						foreach($periods as $key => $value):
						echo '<option value="'.$key.'">'.$value[0].'</option>';
						endforeach;
						?>
						</select>
					</p>

					<pre></pre>

					<input id="export_attendance_sheet" type="submit" <?php if($key == '') {?> style="display: none;" <?php } ?> class="button" name="export_attendance_sheet" value="Export attendance sheet" style="height:25px; width:160px; background-color: #b5b5b5; border-color: black;"/>
				</form>
			</div>
		</div>
	</body>
</html>