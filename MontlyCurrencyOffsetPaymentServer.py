import datetime
import calendar
import pandasdmx
from flask import Flask, render_template#, request
#import socket
import logging

#https://www.datacareer.de/blog/accessing-ecb-exchange-rate-data-in-python/
#https://pandasdmx.readthedocs.io/en/v1.0/

werkzeuglog=logging.getLogger('werkzeug')
werkzeuglog.setLevel(logging.ERROR)

#logging.basicConfig(filename='record.log', level=logging.INFO)
app = Flask(__name__, template_folder='src/htmltemplates')

class MonthlyAverageCalculator (object):
	def __init__ (self):
		self._dict = dict ()

	def calculateRefAvg (self, year, month):
		return 2022, 5, 385

	def calculate (self, year, month, useCache=False):
		if useCache:
			if not str(year) in self._dict: self._dict[str(year)] = dict ()
			if str (month) in self._dict[str (year)]: return self._dict[str (year)][str (month)]

		return self._calculate_with_retries (retryCount=10, year=year, month=month, useCache=useCache)

	def _calculate_with_retries (self, retryCount, year, month, useCache) :
		monthStr = f'{month}' if month > 9 else f'0{month}'
		startPeriod = f'{year}-{monthStr}-01'
		endPeriod = f'{year}-{monthStr}-{calendar.monthrange (year=year, month=month)[1]}'
		print (f'Requesting data from European Central Bank for year {year}. {datetime.date(year, month, 1).strftime("%B")}...')
		for i in range (retryCount) :
			try:
				print (f'pandasdmx.Request: {i+1}.try')
				ecb = pandasdmx.Request('ECB', backend='memory', timeout=2)
				data_response = ecb.data(resource_id = 'EXR', key={'CURRENCY': ['HUF', 'EUR']}, params = {'startPeriod': startPeriod, 'endPeriod': endPeriod, 'use_cache': True}, dsd=ecb.dataflow('EXR').structure.ECB_EXR1)
				data = data_response.data
				sum = 0.0
				for s in data[0].series[0] : sum += float (s.value)
				retVal = sum / len (data[0].series[0]) if len (data) > 0 and len (data[0].series[0]) > 0 else 0
				if useCache: self._dict[str(year)][str (month)]= retVal
				return retVal
			except Exception as e:
				print (e)
		return -1
		

monthlyAverageCalculator = MonthlyAverageCalculator ()

@app.route("/")
def index():
	now = datetime.datetime.now ()
	relevantMonth = now.month - 2 if now.month > 2 else 12
	relevantYear = now.year if relevantMonth < 12 else now.year - 1
	
	refYear, refMonth, refAvg = monthlyAverageCalculator.calculateRefAvg (year=relevantYear, month=relevantMonth)
	relevantAvg = monthlyAverageCalculator.calculate (year=relevantYear, month=relevantMonth, useCache=True)
	currAvg = -1 if relevantAvg == -1 else monthlyAverageCalculator.calculate (year=now.year, month=now.month)

	prevMonth = now.month - 1 if now.month > 1 else 12
	prevYear = now.year if prevMonth < 12 else now.year - 1
	prevAvg = -1 if relevantAvg == -1 else monthlyAverageCalculator.calculate (year=prevYear, month=prevMonth, useCache=True)
	
	refMonthName = datetime.date(refYear, refMonth, 1).strftime("%B")
	relevantMonthName = datetime.date(relevantYear, relevantMonth, 1).strftime("%B")
	prevMonthName = datetime.date(prevYear, prevMonth, 1).strftime("%B")
	monthName =  now.strftime("%B")

	return render_template(
		"index.html",
		refYear=refYear, refMonth=refMonthName, refAvg=refAvg,
		relevantYear=relevantYear, relevantMonth=relevantMonthName, relevantAvg=relevantAvg,
		prevYear=prevYear,prevMonth=prevMonthName, prevAvg=prevAvg,
		currYear=now.year, currMonth=monthName, currAvg=currAvg)


app.run (host="0.0.0.0", threaded=False,port="33333")


