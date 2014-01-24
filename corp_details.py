from selenium import webdriver
from selenium.webdriver.support import ui
import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import urllib
import urllib2
import psycopg2
import re
import string
from datetime import datetime

url_prefix="http://corp.sec.state.ma.us/CorpWeb/CorpSearch/"
driver = webdriver.Firefox()
wait = ui.WebDriverWait(driver, 300)
db = psycopg2.connect("dbname=corp_search user=corp_search password=corp_search")
cur = db.cursor()
progress = 0

offset = 0
cur.execute("SELECT * FROM corp_name limit 2000 offset %s;", (offset,))
while cur.rowcount > 0:
    updates = []
    for biz in cur:
        url = url_prefix + biz[6]
        page = driver.get(url)
        
        try:
            soup = BeautifulSoup(driver.page_source, "lxml")
            org_date = soup.find(id="MainContent_lblOrganisationDate").string
            org_date = datetime.strptime(org_date, "%m-%d-%Y")
            exact_name = soup.find(id="MainContent_lblEntityName").string
            org_type = soup.find(id="MainContent_lblEntityType").string

            biz_id = biz[0]

            updates.append((org_date, exact_name, org_type, biz_id))
        
        except:
           pass 
        progress = progress + 1
        if progress % 100 == 1:
            print str(progress) + " "

    
    cur.executemany("UPDATE corp_name SET (org_date, exact_name, org_type) = (%s, %s, %s) where id=%s;",
                    updates)
    offset = offset + 2000
    cur.execute("SELECT * FROM corp_name limit 2000 offset %s;", (offset,))
driver.close()
