import datetime
import calendar
import pandasdmx
from flask import Flask, render_template, request
import socket
import logging


#https://www.datacareer.de/blog/accessing-ecb-exchange-rate-data-in-python/
#https://pandasdmx.readthedocs.io/en/v1.0/

werkzeuglog=logging.getLogger('werkzeug')
werkzeuglog.setLevel(logging.ERROR)

logging.basicConfig(filename='record.log', level=logging.INFO)
app = Flask(__name__, template_folder='src/htmltemplates')

@app.route("/")
def index():
	class MonthlyAverageCalculator (object):
		def calculateRefAvg (self, year, month):
			return 2022, 5, 385

		def calculate (self, year, month):
			ecb = pandasdmx.Request('ECB')
			monthStr = f'{month}' if month > 9 else f'0{month}'
			startPeriod = f'{year}-{monthStr}-01'
			endPeriod = f'{year}-{monthStr}-{calendar.monthrange (year=year, month=month)[1]}'
			data_response = ecb.data(resource_id = 'EXR', key={'CURRENCY': ['HUF', 'EUR']}, params = {'startPeriod': startPeriod, 'endPeriod': endPeriod, 'use_cache': True}, dsd=ecb.dataflow('EXR').structure.ECB_EXR1)
			data = data_response.data
			sum = 0.0
			for s in data[0].series[0] :
				sum += float (s.value)
			return sum / len (data[0].series[0]) if len (data) > 0 and len (data[0].series[0]) > 0 else 0

	monthlyAverageCalculator = MonthlyAverageCalculator ()

	now = datetime.datetime.now ()
	relevantMonth = now.month - 2 if now.month > 2 else 12
	relevantYear = now.year if relevantMonth < 12 else now.year - 1
	
	refYear, refMonth, refAvg = monthlyAverageCalculator.calculateRefAvg (year=relevantYear, month=relevantMonth)
	relevantAvg = monthlyAverageCalculator.calculate (year=relevantYear, month=relevantMonth)
	currAvg = monthlyAverageCalculator.calculate (year=now.year, month=now.month)

	prevMonth = now.month - 1 if now.month > 1 else 12
	prevYear = now.year if prevMonth < 12 else now.year - 1
	prevAvg = monthlyAverageCalculator.calculate (year=prevYear, month=prevMonth)
	
	
	refMonthName = datetime.date(refYear, refMonth, 1).strftime("%B")
	relevantMonthName = datetime.date(relevantYear, relevantMonth, 1).strftime("%B")
	prevMonthName = datetime.date(prevYear, prevMonth, 1).strftime("%B")
	monthName =  now.strftime("%B")

	'''relevantMcopMultiplier = 0.0
	if refAvg >= relevantAvg :
		print('Monthly Currency Offset Payment is: 0!!! HUF rocks! Orban is the king!')
	else:
		relevantMcopMultiplier = (relevantAvg - refAvg) / refAvg
		print(f'Monthly Currency Offset Payment Multiplier in {relevantYear}.{relevantMonthName} is: {relevantMcopMultiplier}')

	prevMcopMultiplier = 0.0
	if refAvg >= prevAvg :
		print('Monthly Currency Offset Payment is: 0!!! HUF rocks! Orban is the king!')
	else:
		prevMcopMultiplier = (prevAvg - refAvg) / refAvg
		print(f'Monthly Currency Offset Payment Multiplier in {prevYear}.{prevMonthName} is: {prevMcopMultiplier}')'''

	ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
	try:
		addr = socket.gethostbyaddr(ip)[0]
	except:
		addr = ip

	app.logger.info(f'[{now.strftime ("%d/%b/%y %H:%M:%S")}] Request from machine {addr}')
	return render_template(
		"index.html",
		refYear=refYear, refMonth=refMonthName, refAvg=refAvg,
		relevantYear=relevantYear, relevantMonth=relevantMonthName, relevantAvg=relevantAvg,
		prevYear=prevYear,prevMonth=prevMonthName, prevAvg=prevAvg,
		currYear=now.year, currMonth=monthName, currAvg=currAvg,
		addr=addr);  


app.run (host="0.0.0.0", threaded=True,port="33333")


