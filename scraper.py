import requests
requests.adapters.DEFAULT_RETRIES = 15 # increase retries number
import csv
import nltk
import re
import multiprocessing 

from time import sleep
from numpy.random import rand, randint
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
nltk.download('stopwords')

def soup_loader(url):
    ## Getting webpage content by http request
    ## Creating parser
    headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36'
        }
    response = requests.get(url, 
                            timeout=180, 
                            headers=headers, 
                            )
    soup = BeautifulSoup(response.text,  "html.parser")
    response.close()
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
        temp = re.sub(r"[^ a-zA-Z]+",' ', desc).lower().split(' ')
        temp = [word for word in temp if word not in stop_words if len(word) > 1]
        descriptions[n] = ' '.join(temp)
    return ' '.join(descriptions)

def run_scraper(file):

    ## Creating main soup
    url = 'https://www.dice.com/jobs/browsejobs/q-title-djt-A-jobs' ## Starting point
    main_soup,status = soup_loader(url)

    ## Getting job categories
    categories = get_categories(main_soup)[file]
    print(categories)

    ## Getting job category links
    categories_links = get_category_links(categories, url)

    ## Initializing contiainers
    jobs_descriptions=[]
    job_titles=[]
    base=100
    key=1
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
                job_link_descriptions = []
                
                ## Loading content of job title link
                job_title_soup,status = soup_loader(job_link)

                ## Getting number of pages
                num_pages = get_num_pages(job_title_soup)
                n=1; key+=1
                print(f'       {1} out of {num_pages} pages processed')
                if num_pages == 1: 
                    jobs_descriptions.append({'job_id':file*base+key,'job_title':job_titles[l],'job_description':get_job_descriptions(job_title_soup)})
                    print('       Only 1 page'); continue ## Next job title if only one page
                
                job_link_descriptions+= get_job_descriptions(job_title_soup)
                ## Generating pagination links
                page_links = get_page_links(num_pages, job_link)
                
                ## Getting job descriptions for page>1 in job title listing
                for page_link in page_links:

                    ## Loading content of job title link
                    job_title_soup,status = soup_loader(page_link)

                    ## Retrieving job descriptions
                    job_link_descriptions += get_job_descriptions(job_title_soup)
                    
                    print(f'       {n+1} out of {num_pages} pages processed')
                    ## Hard limiting number of jobs to scrape 
                    # if len(job_link_descriptions) > 20: jobs_descriptions = jobs_descriptions + [job_link_descriptions[:20]]
                    # else: jobs_descriptions = jobs_descriptions + [job_link_descriptions]
                    n+=1
                    # break
                    if n == 49: break ## Getting a maximum (n+1)*20 number of job description per title
                jobs_descriptions.append({'job_id':file*base+key,'job_title':job_titles[l],'job_description':get_job_descriptions(job_title_soup)})
                # jobs_descriptions.append([job_titles[l],job_link_descriptions])
                # break
                if l == 49 : break ## Testing code for 10 jobs
            # break ## Testing code
        except Exception as e:
            print(e)

    ## Saving as CSV
    fieldnames = ['job_id','job_title','job_description']
    with open(f'datasets//dice_jobs_{str(file)}.csv', 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(jobs_descriptions)


if __name__ == '__main__': 
    pool = multiprocessing.Pool() 
    result_async = [pool.apply_async(run_scraper, args = (i,)) for i in range(26)]
    results = [r.get() for r in result_async] 
    print("Output: {}".format(results)) 