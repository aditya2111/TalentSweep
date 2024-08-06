import requests
from bs4 import BeautifulSoup
import psycopg2
import cloudscraper
import re
def find_substring_index(text, substring):
    # Use the find method to locate the index of the substring
    start_index = text.find(substring)
    
    if start_index == -1:
        raise ValueError(f"Substring '{substring}' not found in the text.")
    
    return start_index
def get_description(soup):
        list_items = soup.find_all('li')
        qualifications = []
        current_qualification = []
        # Iterate through each list item
        for item in list_items:
            text = item.get_text(strip=True)
            if text == 'linkCopy link':
                # When separator is found, finalize the current qualification
                if current_qualification:
                    qualifications.append(" ".join(current_qualification))
                    current_qualification = []
            else:
                # Append the text to the current qualification
                current_qualification.append(text)

        # Add the last qualification if there's any
        if current_qualification:
            qualifications.append(" ".join(current_qualification))



        # Print the results
        del qualifications[-1]
        for i in range(len(qualifications)):
            text = qualifications[i]
            substring = "qualifications"
            start_index = find_substring_index(text,substring)
            end_index = text.find("Learn")
            text_section = text[start_index + len("qualifications"):end_index]
            qualifications[i] = text_section
        return qualifications

def get_links(soup):
    link_list = soup.find_all('a', class_ = 'WpHeLc VfPpkd-mRLv6 VfPpkd-RLmnJb')
    for i in range(len(link_list)):
        link_list[i] = 'https://www.google.com/about/careers/applications/' + link_list[i].get('href')
    return link_list

def scrape_indeed_google(url):
    response = requests.get(url)
    jobs = []
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        job_titles = soup.find_all('h3', class_='QJPWVe')
        qualifications = get_description(soup)
        links = get_links(soup)
        for i in range(len(job_titles)):
            jobs.append({'title': job_titles[i], 'company': 'Google', 'location': 'India', 'ctc_inr_lpa': 0, 'description':qualifications[i], 'apply_link':links[i]})
    else:
        print('Failed to retrieve the webpage. Status code:', response.status_code)
    return jobs

def store_jobs(jobs):
    conn = psycopg2.connect(
        dbname='job_scraper', user='postgres', password='Adi@2111', host='localhost'
    )
    cursor = conn.cursor()

    for job in jobs:
        # Ensure each job field is a string or appropriate type
        title = job['title'].get_text() if hasattr(job['title'], 'get_text') else job['title']
        company = job['company'].get_text() if hasattr(job['company'], 'get_text') else job['company']
        location = job['location'].get_text() if hasattr(job['location'], 'get_text') else job['location']
        description = job['description'].get_text() if hasattr(job.get('description', ''), 'get_text') else job.get('description', '')
        ctc_inr_lpa = job['ctc_inr_lpa']
        apply_link = job['apply_link'].get_text() if hasattr(job['apply_link'], 'get_text') else job['apply_link']

        cursor.execute(
            """
            INSERT INTO jobs (title, company, location, description, ctc_inr_lpa, apply_link)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (title, company, location, description, ctc_inr_lpa, apply_link)
        )
    
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    url = 'https://www.google.com/about/careers/applications/jobs/results/?q=%22Software%20Engineer%22&location=India&page='
    for i in range(8):
        url = url + str(i)
        jobs = scrape_indeed_google(url)
        store_jobs(jobs)
        print("Jobs Stored in DB for page" + i)