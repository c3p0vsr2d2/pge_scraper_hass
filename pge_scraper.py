from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import datetime
import pytz
import sys
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# Configuration InfluxDB2
INFLUX_URL = '<enter influx2 (IP + port)>'
INFLUX_DB = '<enter influx2 DB name>'
INFLUX_TOKEN = "<enter influx2 DB token>"
INFLUX_ORG = "<enter influx organization>"

# Selenium
SELENIUM_URL = "<enter selenium (IP + port)>"

MAX_RETRIES = 4;

bucket = INFLUX_DB
client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--user-agent= Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:70.0) Gecko/20100101 Firefox/70.0');

no_of_tries = 0
while no_of_tries < MAX_RETRIES:
    try:
        driver = webdriver.Remote(f"http://{SELENIUM_URL}/wd/hub", {'browserName': 'chrome'})

        # LOGIN
        # -----------------------------------------------------------------------------------------------------------------------------------------------------------------
        print("Opening Selenium Session")
        driver.get("https://www.pge.com/")
        #this was written before I remembered getpass().
        user = "<enter PGE username>"
        passwd = "<enter PGE password>"
        elems = driver.find_element_by_id("username")
        elems.send_keys(user)
        elems = driver.find_element_by_id("password")
        elems.send_keys(passwd)
        driver.implicitly_wait(1)
        elems.send_keys(Keys.RETURN)
        print("Logging in...")
        driver.implicitly_wait(30)
        # -----------------------------------------------------------------------------------------------------------------------------------------------------------------


        # ENERGY USAGE PAGE
        # -----------------------------------------------------------------------------------------------------------------------------------------------------------------
        print("Energy Usage Page")
        ####### Open Energy Usage page
        driver.get("https://m.pge.com/index.html#myusage/<enter PGE account#>")
        driver.implicitly_wait(60)
        print(f"Retrieved URL: {driver.current_url}")
        # driver.find_element_by_xpath("/html/body/div[3]/div/div[3]/div/div/div[2]/div/div[2]/div/div[2]/div/div[2]/div/div/div[3]/div/div/div/div[1]/div/div[2]/div/div[1]/a/p[1]").click()
        # driver.implicitly_wait(10)
        ####### Click on day-view


        # 1. HOURLY ELEC kWh (PAST DAY)
        # -----------------------------------------------------------------------------------------------------------------------------------------------------------------
        ####### Click on "Day View"
        # driver.save_screenshot("screenshot.png")
        driver.find_element_by_xpath("/html/body/div[2]/div/div[1]/div[2]/div/div/div/opower-shadow-html/opower-shadow-body/div/div/div/div/div/div[1]/div/div[2]/div/select/option[3]").click()
        driver.implicitly_wait(30)

        print("Date Referencing")

        print("Finding date on electricity usage page")
        date_str = driver.find_element_by_xpath("/html/body/div[2]/div/div[1]/div[2]/div/div/div/opower-shadow-html/opower-shadow-body/div/div/div/div/div/div[1]/div/div[3]/div/span").get_attribute('innerHTML')

        elec_hourly_usage_table = driver.find_element_by_xpath("/html/body/div[2]/div/div[1]/div[2]/div/div/div/opower-shadow-html/opower-shadow-body/div/div/div/div/div/div[2]/div/div[1]/table").get_attribute('innerHTML')
        # -----------------------------------------------------------------------------------------------------------------------------------------------------------------

        # 2. DAILT ELEC kWh, DAILY GAS THERMS (TWO WEEKS)
        # -----------------------------------------------------------------------------------------------------------------------------------------------------------------
        print("Daily Electricity/Gas Usage")
        driver.get("https://m.pge.com/index.html#myusage/<enter PGE account#>")
        driver.implicitly_wait(30)
        ####### Click on "Combined"
        # driver.find_element_by_xpath("//*[@id=\"widget-data-browser\"]/div/opower-shadow-html/opower-shadow-body/div/div/div/div/div/div[1]/div/div[1]/div[2]/div/ul/li[1]/button").click()
        driver.find_element_by_xpath("/html/body/div[2]/div/div[1]/div[2]/div/div/div/opower-shadow-html/opower-shadow-body/div/div/div/div/div/div[1]/div/div[1]/div[2]/div/ul/li[1]/button").click()
        driver.implicitly_wait(30)
        # ####### Click on "Bill View"
        # driver.find_element_by_xpath("//*[@id=\"widget-data-browser\"]/div/opower-shadow-html/opower-shadow-body/div/div/div/div/div/div[1]/div/div[2]/div/select/option[2]").click()
        # driver.implicitly_wait(40)

        elec_gas_daily_usage_table = driver.find_element_by_xpath("/html/body/div[2]/div/div[1]/div[2]/div/div/div/opower-shadow-html/opower-shadow-body/div/div/div/div/div/div[2]/div/div[1]/table").get_attribute('innerHTML')

        ####### Click on "Previous Week"
        # driver.find_element_by_xpath("/html/body/div[2]/div/div[1]/div[2]/div/div/div/opower-shadow-html/opower-shadow-body/div/div/div/div/div/div[1]/div/div[3]/div/button[1]/svg").click()
        # driver.implicitly_wait(40)
        # elec_gas_daily_usage_table_prev_week = driver.find_element_by_xpath("/html/body/div[2]/div/div[1]/div[2]/div/div/div/opower-shadow-html/opower-shadow-body/div/div/div/div/div/div[2]/div/div[1]/table").get_attribute('innerHTML')
        # -----------------------------------------------------------------------------------------------------------------------------------------------------------------
        
        no_of_tries = MAX_RETRIES
    except Exception as e:
        print(e)
        driver.save_screenshot("pge_screenshot_err.png")
        driver.quit()
        
        no_of_tries = no_of_tries + 1

# 1. HOURLY ELEC kWh (PAST DAY)
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------
try:
    date_pge = datetime.datetime.strptime(date_str, '%A, %b %d')
    date_pge_str = date_pge.strftime('%A, %b %-d')

    today = datetime.date.today()
    today_str = today.strftime('%A, %b %-d')

    yesterday = today - datetime.timedelta(days=1)
    yest_str = yesterday.strftime('%A, %b %-d')

    daybefore = datetime.date.today() - datetime.timedelta(days=2)
    daybefore_str = daybefore.strftime('%A, %b %-d')

    if ((date_str == today_str) | (date_str == yest_str) | (date_str == daybefore_str)):

        # print(table_text)
        soup = BeautifulSoup(elec_hourly_usage_table,'html.parser')
        # table = soup.select("tbody")
        elec_hourly_table_data = [i.text for i in soup.select('td')]
        
        elec_hourly_time_start = elec_hourly_table_data[0::4]
        elec_hourly_time_end = elec_hourly_table_data[1::4]
        elec_hourly_usage  = elec_hourly_table_data[2::4]
        elec_hourly_weather_data = elec_hourly_table_data[3::4]
        
        # time_start = [w.replace('Time start: ', '') for w in time_start]
        # time_start = [w.replace('.', '') for w in time_start]
        
        # time_end = [w.replace('Time end: ', '') for w in time_end]
        # time_end = [w.replace('.', '') for w in time_end]
        
        elec_hourly_usage = [w.replace('Usage: ', '') for w in elec_hourly_usage]
        elec_hourly_usage = [w.replace('kWh.', '') for w in elec_hourly_usage]
        
        elec_hourly_weather_data = [w.replace('Temperature: ', '') for w in elec_hourly_weather_data]
        elec_hourly_weather_data = [w.replace('°.', '') for w in elec_hourly_weather_data]
    else:
        print("Date (" + date_str + ") does not match today's date (" + today_str + "), or yesterday's date (" + yest_str + "), or the day before's date (" + daybefore_str + ")")


    writePoints_hourly = []
    for j in range(24):
        timestamp = datetime.datetime.combine((yesterday if (date_str == yest_str) else daybefore), datetime.time(j, 0, 0))
        timestamp = timestamp.replace(tzinfo=pytz.timezone('America/Los_Angeles')).isoformat()
        # writePoints.append(Point("measurement_name").tag("homeprice", "data").field(key, hp_dict[key]))
        writePoints_hourly.append(Point("pge_elec_hourly_meas").field("elec_usage_kWh", float(elec_hourly_usage[j])).time(timestamp))
        writePoints_hourly.append(Point("pge_elec_hourly_meas").field("weather_temp", float(elec_hourly_weather_data[j])).time(timestamp))
    # print(writePoints)
    write_api.write(bucket=INFLUX_DB, record=writePoints_hourly)
except Exception as e:
    print(e)
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------


# 1. HOURLY ELEC kWh (PAST DAY)
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------
# print(table_text)
soup = BeautifulSoup(elec_gas_daily_usage_table,'html.parser')
elec_gas_daily_table_data = [i.text for i in soup.select('td')]
elec_gas_daily_table_data1 = [ x for x in elec_gas_daily_table_data if "Additional Information" not in x ]

elec_gas_daily_date_str = elec_gas_daily_table_data1[0::5]
# print(elec_gas_daily_date_str)
elec_gas_daily_date_str = [w.replace('Date: ', '') for w in elec_gas_daily_date_str]
elec_gas_daily_date_str = [w.replace('.', '') for w in elec_gas_daily_date_str]
elec_gas_daily_date_str = [w.replace('th,', ',') for w in elec_gas_daily_date_str]
elec_gas_daily_date_str = [w.replace('st,', ',') for w in elec_gas_daily_date_str]
elec_gas_daily_date_str = [w.replace('rd,', ',') for w in elec_gas_daily_date_str]
elec_gas_daily_date_str = [w.replace('nd,', ',') for w in elec_gas_daily_date_str]
# print(elec_gas_daily_date_str)

elec_gas_daily_combined_usage = elec_gas_daily_table_data1[1::5]
elec_gas_daily_combined_usage = [w.replace('Total combined usage: ', '') for w in elec_gas_daily_combined_usage]
elec_gas_daily_combined_usage = [w.replace(' units.', '') for w in elec_gas_daily_combined_usage]
elec_gas_daily_combined_usage = [w.replace('Not available', '0') for w in elec_gas_daily_combined_usage]

elec_gas_daily_gas_usage = elec_gas_daily_table_data1[2::5]
elec_gas_daily_gas_usage = [w.replace('Gas usage: ', '') for w in elec_gas_daily_gas_usage]
elec_gas_daily_gas_usage = [w.replace(' therms', '') for w in elec_gas_daily_gas_usage]
elec_gas_daily_gas_usage = [w.replace('Not available', '0') for w in elec_gas_daily_gas_usage]

elec_gas_daily_elec_usage = elec_gas_daily_table_data1[3::5]
elec_gas_daily_elec_usage = [w.replace('Electricity usage: ', '') for w in elec_gas_daily_elec_usage]
elec_gas_daily_elec_usage = [w.replace(' kWh', '') for w in elec_gas_daily_elec_usage]
elec_gas_daily_elec_usage = [w.replace('Not available', '0') for w in elec_gas_daily_elec_usage]

elec_gas_daily_temp = elec_gas_daily_table_data1[4::5]
# 'Temperature: 66°, High - 81°, Low - 55°.'
elec_gas_daily_temp_avg = [w.split(',')[0] for w in elec_gas_daily_temp]
elec_gas_daily_temp_avg = [w.replace('Temperature: ', '') for w in elec_gas_daily_temp_avg]
elec_gas_daily_temp_avg = [w.replace('°', '') for w in elec_gas_daily_temp_avg]
elec_gas_daily_temp_avg = [w.replace('Not available', '0') for w in elec_gas_daily_temp_avg]
elec_gas_daily_temp_hi = [w.split(',')[1] for w in elec_gas_daily_temp]
elec_gas_daily_temp_hi = [w.replace('High - ', '') for w in elec_gas_daily_temp_hi]
elec_gas_daily_temp_hi = [w.replace('°', '') for w in elec_gas_daily_temp_hi]
elec_gas_daily_temp_hi = [w.replace('Not available', '0') for w in elec_gas_daily_temp_hi]
elec_gas_daily_temp_lo = [w.split(',')[2] for w in elec_gas_daily_temp]
elec_gas_daily_temp_lo = [w.replace('Low - ', '') for w in elec_gas_daily_temp_lo]
elec_gas_daily_temp_lo = [w.replace('°.', '') for w in elec_gas_daily_temp_lo]
elec_gas_daily_temp_lo = [w.replace('Not available', '0') for w in elec_gas_daily_temp_lo]

# print(elec_gas_daily_gas_usage)

writePoints_daily = []
for j in range(len(elec_gas_daily_date_str)):
    timestamp = datetime.datetime.combine(datetime.datetime.strptime(elec_gas_daily_date_str[j], '%B %d, %Y'), datetime.time(12, 0, 0))
    timestamp = timestamp.replace(tzinfo=pytz.timezone('America/Los_Angeles')).isoformat()
    # writePoints.append(Point("measurement_name").tag("homeprice", "data").field(key, hp_dict[key]))
    writePoints_daily.append(Point("pge_elec_gas_daily_meas").field("combined_usage_units", float(elec_gas_daily_combined_usage[j])).time(timestamp))
    writePoints_daily.append(Point("pge_elec_gas_daily_meas").field("gas_usage_therms", float(elec_gas_daily_gas_usage[j])).time(timestamp))
    writePoints_daily.append(Point("pge_elec_gas_daily_meas").field("elec_usage_kWh", float(elec_gas_daily_elec_usage[j])).time(timestamp))
    
    writePoints_daily.append(Point("pge_elec_gas_daily_meas").field("weather_temp_avg", float(elec_gas_daily_temp_avg[j])).time(timestamp))
    writePoints_daily.append(Point("pge_elec_gas_daily_meas").field("weather_temp_hi", float(elec_gas_daily_temp_hi[j])).time(timestamp))
    writePoints_daily.append(Point("pge_elec_gas_daily_meas").field("weather_temp_lo", float(elec_gas_daily_temp_lo[j])).time(timestamp))
# print(writePoints)
write_api.write(bucket=INFLUX_DB, record=writePoints_daily)
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------
