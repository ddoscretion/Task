#Read before running the code:

#This is best case where everything is working fine, no need for exception handling

#Safari browser is used for this code as default

#I have limited download of PDF files to 5, but if we have everything in database we can use 
# LIMIT for limiting number of records

import requests
from bs4 import BeautifulSoup
import pdfplumber
import re
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time

# Main function to scrape the website and process PDFs
def main():
    driver = webdriver.Safari()
    driver.get("https://programs.iowadnr.gov/documentsearch/Home/NextPage?page=1")
    select = Select(driver.find_element(By.ID, 'Program'))
    select.select_by_visible_text('Enforcement Orders')
    search_button = driver.find_element(By.ID, 'searchSubmit')
    search_button.click()
    time.sleep(5) # Wait for the page to load

    # Parse the results
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Extract the database of records from the table
    records = []
    rows = soup.find_all('tr')  # Find all table rows
    for row in rows:
        columns = row.find_all('th')  # Use 'th' to match table headers
        if len(columns) >= 10:  # Ensure there are enough columns
            facility_name = columns[5].text.strip()  # Defendant
            document_date = columns[2].text.strip()  # Extract document date
            pdf_link = columns[0].find('a')['href']  # hyperlink-link
            year = int(document_date.split('/')[-1])  # Extract the year, just the year

            # Add the record to the list
            records.append({
                'Defendant': facility_name,
                'Plaintiff': 'Iowa DoNR',  # constant value
                'Year': year,
                'Violation Type': 'Environmental',  # constant value
                'Data Source Link': pdf_link
            })

    # Loop for downloading PDFs, if not running, change the range from 0 to 1 as starting point
    for record in records[:5]:
        pdf_url = record['Data Source Link']

        # Download the PDF,extrract, add, insert into database
        response = requests.get(pdf_url)
        pdf_path = 'alem.pdf'
        with open(pdf_path, 'wb') as f:
            f.write(response.content)

        settlement = extract_settlement_from_pdf(pdf_path)
        record['Settlement'] = settlement
        insert_into_db(record)
        print(f"Inserted record: {record}")

    driver.quit()

# Func for extracting settlement from PDF
def extract_settlement_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()

        # re pattern for matching
        pattern = r'\$\s*[\d,]+\.\d{2}|\b[\d,]+\.\d{2}\b'
        matches = re.findall(pattern, text)
        if matches:
            # Cleaning to get just a value, not necessarily needed
            settlement = matches[0].replace('$', '').replace(',', '')
            return float(settlement)
        return None

# Func for database
def insert_into_db(record):
    conn = sqlite3.connect('records.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS records
                 (Defendant text, Plaintiff text, Year integer, Settlement real, ViolationType text, DataSourceLink text)''')
    c.execute("INSERT INTO records VALUES (?, ?, ?, ?, ?, ?)",
              (record['Defendant'], record['Plaintiff'], record['Year'], record['Settlement'],
               record['Violation Type'], record['Data Source Link']))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()
