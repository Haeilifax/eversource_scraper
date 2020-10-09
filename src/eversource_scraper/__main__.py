"""Main process for Eversource Scraper"""
from eversource_scraper import selenium_scraper, mysql_inserter

def main():
    utility_data = selenium_scraper.main()
    mysql_inserter.main(utility_data)

if __name__ == "__main__":
    main()
