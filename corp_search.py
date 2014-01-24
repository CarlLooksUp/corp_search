from selenium import webdriver
from selenium.webdriver.support import ui
import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import psycopg2
import re
import string
from datetime import datetime

url = "http://corp.sec.state.ma.us/CorpWeb/CorpSearch/CorpSearch.aspx" 
driver = webdriver.Firefox()
wait = ui.WebDriverWait(driver, 120)
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
    try:
        wait.until( EC.presence_of_element_located((By.ID, "MainContent_UpdatePanelGrid")))
    except:
        print "problem loading results for " + searchString
        return


    next_page = 2 

    #loop through pagesets (separated by ... links)
    while not finished:
        #first page of set
        table = driver.find_element_by_id("MainContent_UpdatePanelGrid")
        soup = BeautifulSoup(table.get_attribute("innerHTML"), "lxml")
        f = open('test.txt', 'w')
        f.write(str(soup))
        f.close()
        processResultsPage(soup)

        #loop through pages within set
        while soup.find('a', text=str(next_page)):
            next_link =  driver.find_element_by_link_text(str(next_page))
            next_link.click()
            wait.until(EC.staleness_of(next_link))
            table = driver.find_element_by_id("MainContent_UpdatePanelGrid")
            next_page = next_page + 1
            soup = BeautifulSoup(table.get_attribute("innerHTML"), "lxml")
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

        prev_link = driver.find_element_by_link_text(str(next_page - 2))    
        next_link.click()

        #instead of waiting for link to phase out, wait for new set of links
        next_page = next_page + 1
        wait.until(EC.staleness_of(prev_link))


            

        
    
def processResultsPage(soup):
    rows = soup.findAll('tr', class_=re.compile("Grid(Alt)?Row"))
    for row in rows:
        ID = unicode(row.findAll('td')[1].string)
        name = unicode(row.find('a').string).encode('ascii', 'xmlcharrefreplace')
        profile_url = row.find('a')['href']
        address1 = unicode(row.findAll('td')[3].contents[0]).encode('ascii', 'xmlcharrefreplace')
        try:
            address2 = unicode(row.findAll('td')[3].contents[2]).encode('ascii', 'xmlcharrefreplace')
        except IndexError:
            address2 = ""

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
#need to do co-cz (r?) also so-sz/r, uq-?
for char in 'csu':
    for char2 in string.lowercase[14:]:
        for char3 in string.lowercase:
            search_string = char + char2 + char3
            getSearchResults(search_string)

driver.close()
cur.close()
db.close()
log.close()
