from selenium import webdriver
from selenium.webdriver.support import ui
import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import psycopg2
import re

url = "http://corp.sec.state.ma.us/CorpWeb/CorpSearch/CorpSearch.aspx" 
driver = webdriver.Firefox()
wait = ui.WebDriverWait(driver, 20)
db = psycopg2.connect("dbname=corp_search user=corp_search password=corp_search")
cur = db.cursor()

def getSearchResults(searchString):
    driver.get(url)

    driver.find_element_by_id("MainContent_rdoByEntityName").click()
    search_field = driver.find_element_by_id("MainContent_txtEntityName")
    search_field.send_keys(searchString)
    driver.find_element_by_id("MainContent_btnSearch").click()
    wait.until( EC.presence_of_element_located((By.ID, "MainContent_UpdatePanelGrid")))

#    print "".join(i for i in driver.page_source if ord(i)<128 )
    soup =  BeautifulSoup(driver.page_source, "html5lib")
    processResultsPage(soup)

    nextpage = 2 

    while soup.find('a', text=str(nextpage)):
        next_link =  driver.find_element_by_link_text(str(nextpage))
        next_link.click()
        wait.until_not(EC.element_to_be_clickable((By.LINK_TEXT, str(nextpage))))
        nextpage = nextpage + 1
        soup = BeautifulSoup(driver.page_source, "html5lib")
        processResultsPage(soup)
	if nextpage > 4:
            return
    
def processResultsPage(soup):
    rows = soup.findAll('tr', class_=re.compile("Grid(Alt)?Row"))
    for row in rows:
        ID = unicode(row.findAll('td')[1].string)
        name = unicode(row.find('a').string)
        profile_url = row.find('a')['href']
        address1 = unicode(row.findAll('td')[3].contents[0])
        address2 = unicode(row.findAll('td')[3].contents[2])
	address = address1 + "\n" + address2

        cur.execute("INSERT INTO corp_name (ID, name, address, profile_url) \
                     VALUES (%s, %s, %s, %s)", (ID, name, address, profile_url))

    db.commit()

def getURLinfo(url):

    driver.get(url)
    html = driver.page_source
    next25 = "ctl00_ContentPlaceHolder1_RestRatings_Next"
    soup = BeautifulSoup(html)

    while soup.find(id=re.compile(next25)):            
        driver.find_element_by_id(next25).click()
        html = html + driver.page_source
        soup = BeautifulSoup(driver.page_source)

    soup = BeautifulSoup(html)
    comment = soup.findAll(id=re.compile("divComment"))

    for entry in comment:
        print entry.div.contents #for comments

    driver.close()


getSearchResults("aa")
driver.close()
cur.close()
db.close()

