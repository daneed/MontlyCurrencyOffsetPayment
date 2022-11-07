import datetime
import calendar
from distutils.log import debug
import pandasdmx
from flask import Flask, render_template, request
import socket
import logging


#https://www.datacareer.de/blog/accessing-ecb-exchange-rate-data-in-python/
#https://pandasdmx.readthedocs.io/en/v1.0/

logging.basicConfig(filename='record.log', level=logging.INFO)
app = Flask(__name__, template_folder='src/htmltemplates')

@app.route("/")
def index():
	class MonthlyAverageCalculator (object):
		def calculateRefAvg (self, year, month):
			#megnezni, hogy a 400 ala esik valaha az euro. ha igen, akkor 400 lesz az uj reference. Ezt mondta ugyanis Huw...
			for y in range (2022, year + 1) :
				for m in range (10, month + 1) :
					avg = self.calculate(y, m)
					if avg < 400 :
						return y, m, 400
			return 2022, 5, 385

		def calculate (self, year, month):
			ecb = pandasdmx.Request('ECB')
			monthStr = f'{month}' if month > 9 else f'0{month}'
			startPeriod = f'{year}-{monthStr}-01'
			endPeriod = f'{year}-{monthStr}-{calendar.monthrange (year=year, month=month)[1]}'
			data_response = ecb.data(resource_id = 'EXR', key={'CURRENCY': ['HUF', 'EUR']}, params = {'startPeriod': startPeriod, 'endPeriod': endPeriod, 'use_cache': True})
			data = data_response.data
			sum = 0.0
			for s in data[0].series[0] :
				sum += float (s.value)
			avg = sum / len (data[0].series[0])
			return avg

	monthlyAverageCalculator = MonthlyAverageCalculator ()

	now = datetime.datetime.now ()
	month = now.month - 1 if now.month > 1 else 12
	year = now.year if month < 12 else now.year - 1
	
	refYear, refMonth, refAvg = monthlyAverageCalculator.calculateRefAvg (year=year, month=month)
	actAvg = monthlyAverageCalculator.calculate (year=year, month=month)
	
	mcop_multiplier = 0.0
	monthName = datetime.date(year, month, 1).strftime("%B")
	refMonthName = datetime.date(refYear, refMonth, 1).strftime("%B")

	if refAvg >= actAvg :
		print('Monthly Currency Offset Payment is: 0!!! HUF rocks! Orban is the king!')
	else:
		mcop_multiplier = (actAvg - refAvg) / refAvg
		print(f'Monthly Currency Offset Payment Multiplier in {year}.{monthName} is: {mcop_multiplier}')
	
	ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
	try:
		addr = socket.gethostbyaddr(ip)[0]
	except:
		addr = ip

	app.logger.info(f'[{now.strftime ("%d/%b/%y %H:%M:%S")}] Request from machine {addr}')
	return render_template("index.html", refYear=refYear, refMonth=refMonthName, year=year, month=monthName, refAvg=refAvg, actAvg=actAvg, addr=addr);  


app.run (host="0.0.0.0", threaded=True,port="33333")


