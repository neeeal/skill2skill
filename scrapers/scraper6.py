import requests
import csv
import nltk
import re

from numpy import savetxt, array
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
nltk.download('stopwords')


def soup_loader(url):
    ## Getting webpage content by http request
    ## Creating parser
    response = requests.get(url)
    soup = BeautifulSoup(response.text,  "html.parser")
    return soup, response.status_code

def get_categories(soup):
    ## Getting job categories
    return [category.text for category in soup.find_all(class_='mR5') if len(category.text) == 1]

def get_category_links(categories_list, url):
    return [url.replace(url.split('-')[-2],category) for category in categories_list]

def get_job_title_and_link(soup):
    ## Getting job titles and job links
    ## Output is a list with array of each element (job_title,job_title_link)
    return [(job_title.text,job_title['href']) for job_title in soup.find_all(class_='mR5 browse-job-detail')]

def get_job_links(list):
    ## Generating job links
    root_url = 'https://www.dice.com'
    return [root_url+job_title[1] for job_title in list]


def get_num_pages(soup):
    ## Getting number of pages
    checker = soup.find(class_='sc-dhi-seds-pagination')
    if checker == None or checker == 1: return 1 ## Checking if no pages
    return int(soup.find(class_='sc-dhi-seds-pagination').text.split(' ')[-1])

def get_page_links(num_pages, job_title_url):
    ## Generating pagination links
    base_page_link = '?page='
    return [job_title_url+base_page_link+str(page) for page in range(2,num_pages+1)]

def get_job_descriptions(soup, stop_words = stopwords.words('english')):
    ## Retrieving job descriptions
    ## Applying NLP: lowercase, remove non-alphanum, remove stopwords
    descriptions = [description.text for description in soup.find_all(class_='job-summary-full p-reg-100 sc-dhi-job-search-job-card-layout-full')] 
    for n,desc in enumerate(descriptions):
        temp = re.sub(r"[^ a-zA-Z0-9]+",'', desc).lower().split(' ')
        temp = [word for word in temp if word not in stop_words]
        descriptions[n] = ' '.join(temp)
    return descriptions



## Creating main soup
url = 'https://www.dice.com/jobs/browsejobs/q-title-djt-A-jobs' ## Starting point
main_soup,status = soup_loader(url)

## Getting job categories
categories = get_categories(main_soup)[14:17]
print(categories)

## Getting job category links
categories_links = get_category_links(categories, url)

## Initializing contiainers
jobs_descriptions=[]
job_titles=[]

for category in categories_links:
    try:
        print('Category:', category)
            
        ## Getting job titles per category link
        category_soup,status = soup_loader(category)

        ## Getting job titles and job links
        ## Output is a list with array of each element (job_title,job_title_link)
        job_titles_in_category = get_job_title_and_link(category_soup)
        job_titles += [job_title[0] for job_title in job_titles_in_category]
        
        ## Generating job links
        job_titles_links = get_job_links(job_titles_in_category)

        for l,job_link in enumerate(job_titles_links): ## remove l after testing
            print(' Job Link:',job_link)
            
            ## Loading content of job title link
            job_title_soup,status = soup_loader(job_link)

            ## Retrieving job descriptions
            job_link_descriptions = get_job_descriptions(job_title_soup)
            
            ## Getting number of pages
            num_pages = get_num_pages(job_title_soup)
            
            print(f'       {1} out of {num_pages} pages processed')
            if num_pages == 1: 
                jobs_descriptions += [job_link_descriptions]
                print('       Only 1 page'); continue ## Next job title if only one page
            
            ## Generating pagination links
            page_links = get_page_links(num_pages, job_link)

            ## Getting job descriptions for page>1 in job title listing
            for n,page_link in enumerate(page_links):
                ## Loading content of job title link
                job_title_soup,status = soup_loader(page_link)

                ## Retrieving job descriptions
                job_link_descriptions += f' {get_job_descriptions(job_title_soup)}'
                
                print(f'       {n+2} out of {num_pages} pages processed')
                # if n+1 == 4: break ## Testing code for pages 2-5
            
            ## Hard limiting number of jobs to scrape 
            if len(job_link_descriptions) > 20: jobs_descriptions += [job_link_descriptions[:20]]
            else: jobs_descriptions += [job_link_descriptions]
            
        #     if l > 2 : break ## Testing code for 4 jobs
        # break ## Testing code
    except Exception as e:
        print(e)



## Saving as CSV
with open('datasets//dice_jobs_6.csv', 'w') as f:
     
    # using csv.writer method from CSV package
    write = csv.writer(f)
     
    write.writerow(job_titles) ## columns
    write.writerow(jobs_descriptions) ## rows
