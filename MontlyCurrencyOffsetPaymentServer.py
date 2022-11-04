import datetime
import calendar
import pandasdmx
from flask import Flask, render_template

#https://www.datacareer.de/blog/accessing-ecb-exchange-rate-data-in-python/
#https://pandasdmx.readthedocs.io/en/v1.0/

app = Flask(__name__, template_folder='src/htmltemplates')


@app.route("/")
def index():
	class MonthlyAverageCalculator (object):
		def calculateRefAvg (self, year, month):
			#megnezni, hogy a 400 ala esik valaha az euro. ha igen, akkor ez lesz az uj reference. Ezt mondta ugyanis Huw...
			refYear=2022
			refMonth=5
			refAvg=self.calculate(refYear, refMonth)
			launchYear=2022
			launchMonth=10
			for y in range (launchYear, year + 1) :
				for m in range (launchMonth, month + 1) :
					avg = self.calculate(y, m)
					if refAvg is None or avg < 400 :
						refYear=y
						refMonth=m
						refAvg = avg
						#SD: vajon itt return-olni kellene, azaz: az elso ilyet kellene hasznalni? Vagy, hagyni vegigfutni?
			return refYear, refMonth, refAvg

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

	return render_template("index.html", refYear=refYear, refMonth=refMonthName, year=year, month=monthName, refAvg=refAvg, actAvg=actAvg);  


app.run (host="0.0.0.0", threaded=True,port="33334")


