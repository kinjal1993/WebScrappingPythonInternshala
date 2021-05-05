import requests
from datetime import datetime
from bs4 import BeautifulSoup
import re
from urllib.parse import unquote
from time import sleep
import pandas as pd

DELAY_TIME = 0.5
RECORDS_PER_PAGE = 40 
TOTAL_RECORDS_TO_FETCH = 100
BASE_URL = 'https://internshala.com'
URL = BASE_URL+'/internships/'

# define column headers for the excel/csv file
column_headers = [
    'Internship name',
    'Internship details page link',
    'Internship organization',
    'Internship organization page link',
    'Location of internship',
    'Start date of internship',
    'Duration',
    'Stipend',
    'Application deadline',
    'Number of applicants',
    'Number of openings',
]
df = pd.DataFrame([],columns=column_headers,dtype=object) # initialise empty dataframe with column headers

page_no = 0
total_records_fetched = 0
total_pages = TOTAL_RECORDS_TO_FETCH // RECORDS_PER_PAGE

# begin while loop
while page_no <= total_pages:
    
    page_no += 1
    # fetching next page
    url = URL+'page-'+str(page_no)
    page = requests.get(url) #here also ya different page no so new page okat y
    soup = BeautifulSoup(page.content, 'html.parser')
    # fetch the listing by main id
    results = soup.find(id='list_container') 
    # find all individual elements from the above id
    internship_elements = results.find_all('div', class_='individual_internship')

    # begin for loop
    for ie in internship_elements:

        # Internship name & page link 
        title_element = ie.find('div', class_='heading_4_5')
        title_text = title_element.text # name
        page_link = BASE_URL + unquote(title_element.find('a')['href']) # link

        # Internship organization name & page link
        org_title_element = ie.find('div', class_='company_name')
        org_title_text = org_title_element.text # name
        org_page_link = BASE_URL + unquote(org_title_element.find('a')['href']) # link
        
        # Internship locations
        locations_div = ie.find('a', class_='location_link')
        locations = []

        for le in locations_div:
            locations.append(le)

        location_text = ', '.join(locations)

        # Internship start date - 3 variants present in the html hence fetch whichever is present
        start_date_div = ie.find(id='start-date-first')
        if start_date_div.find('span',class_='start_immediately_desktop'):
            start_date_text = start_date_div.find('span',class_='start_immediately_desktop').text
        elif start_date_div.find('span',class_='start_immediately_mobile'):
            start_date_text = start_date_div.find('span',class_='start_immediately_mobile').text
        else:
            start_date_text = start_date_div.text

        # Internship Duration
        duration_text = ie.find(string='Duration').find_next('div',class_='item_body').contents[0]

        # Stipend
        stipend_text = ie.find('span',class_='stipend').text
        
        # deadline
        deadline_element = ie.find('div',class_='apply_by')
        deadline_string = deadline_element.find('div',class_='item_body').text
        # converting string (ex. 19 May' 21) to date 
        deadline_date = datetime.strptime(deadline_string, "%d %b' %y")
        # format date into dd/mm/yyyy
        deadline_text = deadline_date.strftime("%d/%m/%Y")

        # fetch no of openings & applicants from the detail page
        sleep(DELAY_TIME) # delay before every new page request
        url = page_link
        page = requests.get(url)  #are those diff page ya
        detail_soup = BeautifulSoup(page.content, 'html.parser')
        detail_result = detail_soup.find(id='content')
        
        # fetch no of applicants
        no_of_applicant_text = detail_result.find('div',class_='applications_message').text
        if no_of_applicant_text == 'Be an early applicant':
            no_of_applicant_text = 'No applicants yet'
        
        # fetch no of openings
        no_of_openings_parent = detail_soup.find('div',class_='section_heading',string='Number of openings')
        no_of_openings_text = "NULL"
        if no_of_openings_parent is not None:
            no_of_openings_text = no_of_openings_parent.find_next('div',class_='text-container').contents[0]

        data = [title_text,page_link,org_title_text,org_page_link,location_text,start_date_text,duration_text,stipend_text,deadline_text,no_of_applicant_text,no_of_openings_text]
        # remove white spaces, new lines and tabs
        row = [ re.sub('\s+',' ',string) for string in data ]

        df.loc[len(df.index)] = row # dumping data into the dataframe

        total_records_fetched += 1
        
        # terminate loop if record limit reached
        if(total_records_fetched == TOTAL_RECORDS_TO_FETCH):
            break

    # end for loop

    sleep(DELAY_TIME) # delay before every new page request

# end while loop

df.to_csv('internship.csv',index=False) # generate csv from data
df.to_excel('internship.xlsx',index=False) # generate excel from data
