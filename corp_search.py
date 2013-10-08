from selenium import webdriver
from selenium.webdriver.support import ui
import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import psycopg2
import re
from datetime import datetime

url = "http://corp.sec.state.ma.us/CorpWeb/CorpSearch/CorpSearch.aspx" 
driver = webdriver.Firefox()
wait = ui.WebDriverWait(driver, 20)
db = psycopg2.connect("dbname=corp_search user=corp_search password=corp_search")
cur = db.cursor()
log = open('error.log', 'a')

def getSearchResults(searchString):
    driver.get(url)
    first_set = True
    finished = False

    driver.find_element_by_id("MainContent_rdoByEntityName").click()
    search_field = driver.find_element_by_id("MainContent_txtEntityName")
    search_field.send_keys(searchString)
    driver.find_element_by_id("MainContent_btnSearch").click()
    wait.until( EC.presence_of_element_located((By.ID, "MainContent_UpdatePanelGrid")))


    next_page = 2 

    #len check runs with old soup
    while not finished:
        #first page of set
        soup =  BeautifulSoup(driver.page_source, "html5lib")
        processResultsPage(soup)

        while soup.find('a', text=str(next_page)):
            next_link =  driver.find_element_by_link_text(str(next_page))
            next_link.click()
            wait.until_not(EC.element_to_be_clickable((By.LINK_TEXT, str(next_page))))
            next_page = next_page + 1
            soup = BeautifulSoup(driver.page_source, "html5lib")
            processResultsPage(soup)

        next_links = soup.findAll('a', text="...")
        #after first 20, only one '...' link 
        if first_set and len(next_links) == 1:
            next_link = driver.find_element_by_link_text("...")
            first_set = False
        elif len(next_links) == 2:
            next_link = driver.find_elements_by_link_text("...")[1]
        else: #no continuation links
            finished = True
            continue
            
        next_link.click()

        #instead of waiting for link to phase out, wait for new set of links
        next_page = next_page + 1
        wait.until(EC.element_to_be_clickable((By.LINK_TEXT, str(next_page))))


            

        
    
def processResultsPage(soup):
    rows = soup.findAll('tr', class_=re.compile("Grid(Alt)?Row"))
    for row in rows:
        ID = unicode(row.findAll('td')[1].string)
        name = unicode(row.find('a').string)
        profile_url = row.find('a')['href']
        address1 = unicode(row.findAll('td')[3].contents[0])
        address2 = unicode(row.findAll('td')[3].contents[2])
	address = address1 + "\n" + address2

        try: 
            cur.execute("INSERT INTO corp_name (ID, name, address, profile_url) \
                         VALUES (%s, %s, %s, %s)", (ID, name, address, profile_url))
        except psycopg2.IntegrityError as e:
            log.write("\tproblem with entry\n\tID: " + ID + "\n\tname: " + name + "\n")
            log.write("\t" + e.pgerror)
            db.rollback()
        else:
            db.commit()


log.write('Starting at ' + str(datetime.now().ctime()) + ':\n')
getSearchResults("aa")
driver.close()
cur.close()
db.close()
log.close()
