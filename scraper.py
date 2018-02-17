import requests
from bs4 import BeautifulSoup
import link_and_category
import urllib.parse
import urllib.request
import urllib.error
import json
import re
import database

amazon_domain = "http://www.amazon.in"
subcategory_counter = 0
printed_flag = 0
queued = set()
crawled = set()
JSONArray = {}
''' This user_agent signals where the request is coming from. By default python request will contain user agent as robot
    which might lead to incorrect rendering of pages. In order to correct this and make the server respond with the page which
    will be shown if a normal browser requests the page we modify this user agent to make the server think that the request is
    actually coming from a browser
'''
user_agent = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}


def crawl_url(url):
    source_code = requests.get(url,headers = user_agent)
    plain_text = source_code.text
    bsObject = BeautifulSoup(plain_text, "html.parser")
    menu_list = bsObject.find('a', {'id': 'nav-link-shopall', 'class': 'nav-a-2'})
    categories_link = menu_list.get('href')
    print(menu_list)
    return categories_link


# This method takes all the links on the shop by category page of amazon.in and finds the subcategory links
def subcategory_crawler(url):
    BOLD = '\033[1m'
    END = '\033[0m'
    global amazon_domain, subcategory_counter, queued
    subcategory_page = requests.get(url)
    subcategory_text = subcategory_page.text
    bsObject = BeautifulSoup(subcategory_text, "html.parser")
    # On the amazon website all the subcategory links are inside a div with id siteDirectory
    subcategory_container = bsObject.find('div', {'id': 'siteDirectory'})
    for div in subcategory_container.findAll('div', {'class': 'popover-grouping'}):
        category_title = div.contents[0]
        text = str(category_title.string)
        # Ignore the categories Kindle and Amazon Apps
        if not text.__contains__("Kindle") and not text.__contains__("Amazon Apps"):
            print(BOLD + category_title.string + END)
            for link in div.findAll("a"):
                href = link.get('href')
                link_title = link.string
                # The All Products page does not actually list the products so ignore it
                if not str(link_title).__contains__("All"):
                    subcategory_counter += 1
                    complete_url = amazon_domain + href
                    # print('\t', link_title, '\t', complete_url)
                    # Build the SetStructure object with the subcategory link and the subcategory name
                    x = link_and_category.SetStructure(complete_url, link_title)
                    # Add the object to the queued set to crawl in the future
                    queued.add(x)
        else:
            continue


def get_product_details(url, product_category,filter_name):
    global printed_flag, user_agent,JSONArray
    # Create the empty dictionary which holds a list in it.The key will be the list name(Example:"price-ascending":[])
    temp={filter_name:[]}
    # This dictionary holds the details like title,price,ratings of the products etc.
    product_details_dictionary = {}
    filter_list=[]
    BOLD = '\033[1m'
    END = '\033[0m'
    if url is not None:
        source_code = requests.get(url, headers=user_agent)
        plain_text = source_code.text
        bsObject = BeautifulSoup(plain_text, "html.parser")
        ctr = 0
        product_limit = 5 # This is the number of products which have to be extracted. For eg:- After applying a filter get only top 10
        # items then set limit to 10
        if bsObject.findAll('li', {'class': 's-result-item'}):
            if not printed_flag == 1:
                print(BOLD + product_category + END)
            for li in bsObject.findAll('li', {'class': 's-result-item'}):
                for div in li.findAll('div', {'class': 's-item-container'}):
                    if ctr < product_limit:
                        product_title = div.find('h2', {'class': 's-access-title'})
                        product_rating = div.find('i', {'class': 'a-icon-star'})
                        product_price = div.find('span', {'class': 's-price'})
                        product_url = div.find('a', {'class': 's-access-detail-page'}).get('href')
                        product_img_url = div.find('img', {'class': 's-access-image'}).get('src')
                        if product_title is not None and product_rating is not None and product_price is not None:
                            product_details_dictionary['title'] = product_title.string
                            # Replace the Rs. symbol with a blank space and store it in the dictionary
                            product_details_dictionary['price'] = re.sub('\u00a0','',product_price.text)
                            product_details_dictionary['rating'] = product_rating.text[0:product_rating.text.find(" ")]
                            product_details_dictionary['url'] = product_url
                            product_details_dictionary['image'] = product_img_url
                            x = json.dumps(product_details_dictionary)
                            # Add the encoded json object to the list
                            filter_list.append(x)
                            ctr += 1
        # print("Filter List:\n",filter_list)
        # Add the JSON encoded list to the temp dictionary which is a dictionary with the filter_name as the key
        temp[filter_name]=filter_list
        # print("Encoded JSON Object:\n",temp)
        return temp[filter_name]

def construct_encoded_url(url):
    global amazon_domain, user_agent
    # Create a new dictionary which will hold the rh and qid values of the hidden inputs on a particular page
    dict = {}
    # Spoof the header of the request so that the form is actually loaded on the page
    source = requests.get(url, headers = user_agent)
    plain_text = source.text
    bsObject = BeautifulSoup(plain_text, "html.parser")
    inp = bsObject.find('form', {'id': 'searchSortForm'})
    if inp is not None:
        form_action = inp.get('action')
        inp = bsObject.findAll('form', {'id': 'searchSortForm'})
        for i in inp:
            for x in i.findAll('input', {'type': 'hidden'}):
                # Add the (name,value) pair of the input to the dictionary.
                # This produces something like dict['rh']=lp_32342189_srtx
                dict[x.get('name')] = x.get('value')
        # Encode only the rh and qid values
        rh = urllib.parse.quote(dict['rh'].encode('utf-8)'))
        qid = urllib.parse.quote(dict['qid'].encode('utf-8)'))
        encoded_url = amazon_domain + form_action + "?rh=" + rh + "&qid=" + qid
        return encoded_url


def apply_url_filter(url, filter):
    if url is not None:
        filtered_url = url + "&sort=" + filter
        return filtered_url


href = crawl_url(amazon_domain)
category_links = amazon_domain + href + '/ref=nav_shopall_button'
print("Value of the categories link", amazon_domain + href)

subcategory_crawler(category_links)

price_ascending = "price-asc-rank"
price_descending = "price-desc-rank"
average_review = "review-rank"
popularity = "popularity-rank"

print("Number of subcategories:", subcategory_counter)

# This is the crawling depth
depth = 0
BOLD = '\033[1m'
END = '\033[0m'
crawled_categories = set()
database.connect()
database.delete_database()
while queued and depth < 2:
    product_page_url = queued.pop()
    if not crawled_categories.__contains__(product_page_url.get_category()) and product_page_url.get_link() is not None:
        product_link = product_page_url.get_link()
        product_category = product_page_url.get_category()
        # Create the empty json node so that the database node can be created
        database_node = {product_category:{}}
        crawled_categories.add(product_category)
        new_and_popular = get_product_details(product_link, product_category,"new")
        printed_flag = 1
        encoded_url = construct_encoded_url(product_link)
        if encoded_url is not None:
            print("Sorted By:Ratings", "\tURL:", apply_url_filter(encoded_url, average_review))
            ratings=get_product_details(apply_url_filter(encoded_url, average_review), product_category,"ratings")
            print("Sorted By:Price High to Low", "\tURL:", apply_url_filter(encoded_url, price_descending))
            price_asc=get_product_details(apply_url_filter(encoded_url, price_descending), product_category,"price-ascending")
            print("Sorted By:Price Low to High", "\tURL:", apply_url_filter(encoded_url, price_ascending))
            price_desc=get_product_details(apply_url_filter(encoded_url, price_ascending), product_category,"price-descending")
            printed_flag = 0
            database_node=database.construct_database_node(new_and_popular,ratings,price_asc,price_desc,product_category)
            print("Database node:\n",database_node)
            database.insert(json.loads(database_node))
            depth += 1