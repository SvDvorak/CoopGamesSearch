import asyncio
import threading
import time
from Scraper import Scraper

class ScrapingThread:
	def __init__(self, scraper: Scraper, scrape_interval_hours: int):
		self.scraper = scraper
		self.scrape_interval_hours = scrape_interval_hours
		self.scraping_in_progress = False
		self.last_scrape_time: float = time.time()
		self.has_done_full_scrape = False

		self.continuous_thread = None

	def get_status(self):
		return {
			"scraping_in_progress": self.scraping_in_progress,
			"scraping_state": self.scraper.scraping_state,
			"last_scrape_hours_ago": self.last_scrape_hours_ago(),
			"scrape_interval_hours": self.scrape_interval_hours,
		}

	def last_scrape_hours_ago(self):
		return (time.time() - self.last_scrape_time) / 3600 # Convert to hours

	def scrape_games_background(self):
		try:
			self.scraping_in_progress = True
			print("\n=== Starting background scraping ===")
			
			# Run the scraping (this takes hours)
			last_scrape = None if self.has_done_full_scrape == False else self.last_scrape_time
			total_games_count, new_games_count = asyncio.run(self.scraper.scrape_games(last_scrape))
			asyncio.run(self.scraper.scrape_country_data())
			
			self.last_scrape_time = time.time()
			self.has_done_full_scrape = True
			print(f"\n=== Background scraping completed. Found {new_games_count} new games. New total is {total_games_count} ===\n")
		except Exception as e:
			raise e
		finally:
			self.scraping_in_progress = False
			self.scraper.scraping_state = "None"

	def continuous_scraping_thread(self):
		print(f"\n=== Starting continuous scraping thread (every {self.scrape_interval_hours} hours) ===\n")

		while True:
			try:
				if not self.scraping_in_progress and self.last_scrape_hours_ago() >= self.scrape_interval_hours:
					self.scrape_games_background()
				
				# Check every 10 minutes
				time.sleep(600)
				
			except Exception as e:
				print(f"\nError in continuous scraping thread: {e}")
				time.sleep(300)  # 5 minutes
	
	def start_continuous_scraping(self):
		if self.continuous_thread is None or not self.continuous_thread.is_alive():
			self.continuous_thread = threading.Thread(target=self.continuous_scraping_thread, daemon=True)
			self.continuous_thread.start()
	
	def manual_scrape(self):
		if self.scraping_in_progress:
			return False, "Scraping is already in progress"
		
		print("\nManual scraping triggered\n")
		scraping_thread = threading.Thread(target=self.scrape_games_background, daemon=True)
		scraping_thread.start()
		return True, "Scraping started"