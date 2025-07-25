import threading
import time
from GameStorage import save_games_to_file, load_games_from_file

class ScrapingThread:
	def __init__(self, scraper, games_file, scrape_interval_hours):
		self.scraper = scraper
		self.games_file = games_file
		self.scrape_interval_hours = scrape_interval_hours
		self.scraping_in_progress = False
		self.last_scrape_time = time.time()
		self.games_lock = threading.RLock()
		self.games = []

		self.continuous_thread = None
		
	def load_games(self):
		initial_games = load_games_from_file(self.games_file)
		self.set_games(initial_games)
	
	def get_games(self):
		"""Get current games list (thread-safe)"""
		with self.games_lock:
			return self.games.copy()

	def set_games(self, new_games):
		"""Set games list (thread-safe)"""
		with self.games_lock:
			self.games = new_games

	def get_status(self):
		return {
			"scraping_in_progress": self.scraping_in_progress,
			"scraping_state": self.scraper.scraping_state,
			"last_scrape_hours_ago": self.last_scrape_hours_ago() if self.last_scrape_time > 0 else None,
			"scrape_interval_hours": self.scrape_interval_hours,
			"number_of_games": len(self.games) if self.games else 0
		}

	def last_scrape_hours_ago(self):
		return (time.time() - self.last_scrape_time) / 3600 # Convert to hours

	def scrape_games_background(self):
		try:
			self.scraping_in_progress = True
			print("\n=== Starting background scraping ===")
			
			# Run the scraping (this takes hours)
			last_time = self.last_scrape_time if len(self.games) > 0 else None
			new_games = self.scraper.scrape_games(last_time)
			
			merged_games = self.merge_games(new_games)

			merged_games = self.scraper.scrape_prices(merged_games)

			save_games_to_file(merged_games, self.games_file)
			
			self.set_games(merged_games)
			
			self.last_scrape_time = time.time()
			print(f"\n=== Background scraping completed. Found {len(new_games)} new games. New total is {len(merged_games)} ===\n")
		except Exception as e:
			raise e
		finally:
			self.scraping_in_progress = False
			self.scraper.scraping_state = "None"

	def merge_games(self, new_games):
		existing_games_dict = {game.steam_id: game for game in self.games}
		
		# Update existing games with new data or add new games
		for new_game in new_games:
			existing_games_dict[new_game.steam_id] = new_game
		
		return list(existing_games_dict.values())

	def continuous_scraping_thread(self):
		print(f"\n=== Starting continuous scraping thread (every {self.scrape_interval_hours} hours) ===\n")
		
		while True:
			try:
				time_since_last = self.last_scrape_hours_ago()
				if not self.scraping_in_progress and time_since_last >= self.scrape_interval_hours:
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