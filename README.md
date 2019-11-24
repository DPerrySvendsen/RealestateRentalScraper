# RealestateRentalScraper
A scraper for Realestate.com.au, a popular Australian property listing website. 

Can be used to quickly scrape the details of rental properties, aggregating the data into a TSV (tab-seperated values) file that can be viwed in Excel or a text-editor.

The following parameters can be set at the top of the script:

Parameter | Decription
--- | ---
`scrapeDescriptions` | Should the scraper also record the description of each property? This takes longer, as each property page need to be loaded. 
`outputFilename` | Where should the results be stored? By default, the output is a `.TSV` file, but technically it could be a `.TXT` file, or something else entirely. 
`pagesToLoad` | How many pages should be loaded before the scraper stops? The scraper will automatically stop once no more results are returned.
`propertyType` | What sort of property are we searching for? Common options are `house`, `unit+apartment` and `townhouse`.
`bedsMin `, `bedsMax` | How many bedrooms?
`rentMin`, `rentMax` | How much rent per week?
`postcodes` | Which areas?
`includeSurrounding` | Should the surrounding suburbs be included?
