# Realestate.com.au rental search scraper

import re
import requests
from lxml import html

# ---

# Set scraper parameters here
scrapeDescriptions  = True
outputFilename      = 'scraper_output.tsv'
pagesToLoad         = 25

# Set search parameters here
propertyType        = 'house'
bedsMin             = 1
bedsMax             = 3
rentMin             = 200
rentMax             = 800
postcodes           = ['3000', '3005', '3011', '3016', '3021']
includeSurrounding  = False

# ---

# Set headers to bypass user agent filtering 
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

# Define the seperator used between each postcode in the URL.
# If this script has stopped returning any results, it's probably 
# because a change has been made to the site, and the server now 
# expects a different seperator. This has happened once before, 
# and updating this variable (by manually performing a search and
# observing which seperator was used) was enough to fix it.
seperator = '%3b+'

# ---

def loadPage (url):

  # Send a request and parse the content
  return html.fromstring(requests.get(url, headers=headers).content)

# ---

def getSearchResults (url, pageNumber):

  # Load the search page and extract the search results
  return loadPage(url.format(pageNumber)).findall('.//div[@class="tiered-results tiered-results--exact"]//article')

# ---

def buildURLString ():

  # Create a template for the URL, as well as for a search description string
  url = 'http://www.realestate.com.au/rent/property-{}-with-{}-bedrooms-between-{}-{}-in-'
  searchDescription = \
    'Searching for {} - {} bedroom properties for rent, ' + \
    'within a price range of ${} - ${} per month, '       + \
    'in the following postcodes: '

  # Add the list of postcodes to both templates
  for postcode in postcodes:
    url               += postcode + seperator
    searchDescription += postcode + ', '
    
  # Add the remaining parameters to the URL
  url = url[:-len(seperator)] + '/list-{}?activeSort=price-asc&maxBeds={}&includeSurrounding={}'
  url = url.format(propertyType, bedsMin, rentMin, rentMax, '{}', bedsMax, 'true' if includeSurrounding else 'false')
  
  # Add the remaining parameters to the search description
  searchDescription = searchDescription[:-2] + (' and surrounding suburbs.' if includeSurrounding else '.')
  searchDescription = searchDescription.format(bedsMin, bedsMax, rentMin, rentMax)   
  
  # Print the search description
  print(searchDescription)
  
  # Return the complete URL
  return url

# ---

def parsePriceRange (listing):

  # Prices are listed in various different formats.
  # Here, we try to standardise the way they are displayed.
  # This works for most, but not all, cases
  
  price = listing['Price']
  price = price.replace(' - ', '-')
  price = price.replace(' to ', '-')
  price = price.replace('to', '-')
  price = price.replace('.00', '')
  price = '$' + re.sub('[^\d-]','', price)
  price = price.replace('-', ' - $')
  
  # Some listings include both a per-week and per-month price
  # Where the two have been concatenated, assume three figures and trim accordingly.
  if len(price) > 4 and '-' not in price:
    price = price[:4]
    
  # If the price is expressed as a range, price should reflect the higher end
  if '-' in price:
    price = price[-4:]

  # Record the property price
  listing['Price'] = price

# ---

def parseSuburb (listing):

  # Record the property suburb
  suburb = listing['Link'][listing['Link'].find(propertyType) + len(propertyType) + 5:]
  suburb = suburb[:suburb.find('-')].title()
  suburb = suburb.replace('+', ' ')
  listing['Suburb'] = suburb

# ---

def parseType (listing):
  
  # Record the property type
  propertyType = listing['Link'][len('/property-'):]
  propertyType = propertyType[:propertyType.find('-')].title()
  listing['Type'] = propertyType

# ---

def parseDescription (page):

  # Extract and parse the property description
  description = page.xpath('.//span[@class="property-description__content"]//text()')
  description = ' '.join(description)
  description = ' '.join(description.split()).strip()
  description = description.replace('*', '')
  description = description.replace('"', '\'')
  description = description.replace('“', '\'')
  description = description.replace('”', '\'')
  return description

# ---

def parseListingDetails (article):
  
  # Scrape the data included in the preview article
  listing = {
    'Address'     : scrape(article, './/h2[@class="residential-card__address-heading"]//text()'),
    'Price'       : scrape(article, './/span[@class="property-price "]//text()'),
    'Link'        : scrape(article, './/a[@class="details-link residential-card__details-link"]//@href'),
    'Bedrooms'    : scrape(article, './/ul/li[1]/span'),
    'Bathrooms'   : scrape(article, './/ul/li[2]/span'),
    'Car Spaces'  : scrape(article, './/ul/li[3]/span'),
    'Description' : '',
    'Inspections' : '',
  }
  
  # Parse various additional details
  parsePriceRange(listing)
  parseSuburb(listing)
  parseType(listing)
  
  # Remove the suburb from the address
  listing['Address'] = listing['Address'][:listing['Address'].find(',')]
  
  # Append the top-level domain to create a full link
  listing['Link'] = 'http://www.realestate.com.au' + listing['Link']   
  
  # Assume there are no car spaces if the field is empty
  if listing['Car Spaces'] == '':
    listing['Car Spaces'] = '0' 

  # Follow the link and scrape the property description
  if scrapeDescriptions:
    page = loadPage(listing['Link'])
    listing['Description'] = parseDescription(page)

  # Sometimes, the property is labelled as a house, despite the description saying
  # it's actually an apartment. In these cases, the description is updated accordingly.
  # It's possible for this check to produce false positives, so it's best not to remove
  # these resulte entirely.
  if propertyType == 'house' and listing['Description'].lower() in ['apartment', 'unit', 'flat', 'townhouse']:
    listing['Type'] = 'Apartment'

  # Return the listing details
  return listing
  
# ---

def scrape (article, xpath):

  # Scrape a certain piece of data from the provided HTML snippet
  result = article.xpath(xpath)
  if len(result) > 0:
    # If the xpath matches an element/attribute, return the result as a string
    if type(result[0]) is html.HtmlElement:
      return result[0].text_content()
    else:
      return result[0]
  else:
    # If no data was found, return an empty string
    return ''
  
# ---

try:
  
  # Create or load the output file
  outputFile = open(outputFilename, 'w')

  # Construct the base URL
  searchURL = buildURLString()

  # Print the search parameters
  print('(' + ('Also' if scrapeDescriptions else 'Not' ) + ' scraping property descriptions)')
  print('\nOutputting to ' + outputFile.name + '.')

  # Record the number of pages and results returned
  totalResults = 0
  pageNumber   = 1
      
  # Create the column headers
  outputFile.write(
    'Link'        + '\t' + \
    'Address'     + '\t' + \
    'Suburb'      + '\t' + \
    'Price'       + '\t' + \
    'Bedrooms'    + '\t' + \
    'Bathrooms'   + '\t' + \
    'Car Spaces'  + '\t' + \
    'Description' + '\n' 
  )

  # Begin requesting each page sequentially
  while pageNumber <= pagesToLoad:

    # Send a request, parse the response and retrieve the search results
    print('\nRequesting page ' + str(pageNumber) + '...')
    searchResults = getSearchResults(searchURL, pageNumber)
    pageNumber += 1
    
    # Record the number of results returned
    print(str(len(searchResults)) + ' results returned')
    totalResults += len(searchResults)
    
    # If no results were returned, stop searching
    if len(searchResults) == 0:
      break
    
    # Iterate through the search results
    for article in searchResults:
    
      # Extract the listing details from the result article
      listing = parseListingDetails(article)
      
      # Write the full details to the output file
      outputFile.write(
        listing['Link']        + '\t' + \
        listing['Type']        + '\t' + \
        listing['Address']     + '\t' + \
        listing['Suburb']      + '\t' + \
        listing['Price']       + '\t' + \
        listing['Bedrooms']    + '\t' + \
        listing['Bathrooms']   + '\t' + \
        listing['Car Spaces']  + '\t' + \
        listing['Description'] + '\n'
      )
      
      # Only print a partial address to the console
      maxLen  = 15
      address = listing['Address'].ljust(maxLen) if len(listing['Address']) <= maxLen else listing['Address'][:maxLen]
      
      # Print a trimmed version to the console
      print(
        address                         + '\t' + \
        listing['Suburb'].ljust(maxLen) + '\t' + \
        listing['Price']                + '\t' + \
        listing['Bedrooms']             + '\t' + \
        listing['Bathrooms']
      )
    
  # Finally, display the total number of search results returned
  print('\nTotal results returned: ' + str(totalResults))
  
except KeyboardInterrupt:
  print('Search cancelled.')
except PermissionError:
  print('Couldn\'t write to output file (make sure you don\'t have the file open!)')
except requests.exceptions.ConnectionError:
  print('Couldn\'t connect.')