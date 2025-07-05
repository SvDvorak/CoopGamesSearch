
import math
from datetime import datetime

class Game:
	title = ""
	steam_id = -1					# Steam's app ID
	price = 0						# Price in cents (e.g., 499 for 4.99 euro)
	steam_rating = 0				# 0.0–1.0 float (e.g., 0.85)
	number_of_reviews = 0
	release_date = None				# Date time
	couch_players = 0				# Supported couch players
	lan_players = 0					# Supported LAN players
	online_players = 0				# Supported online players
	cooptimus_url = ""
	steam_url = ""
	header_image = None
	short_description = ""
	tags = []

	is_delisted = False
	is_released = True
	score = 0						# Algorithm scoring
	
	def compute_score(self, weight_rating, weight_price, high_price):
		price = self.price / 100.0  # convert cents to Euro
		a = (self.steam_rating ** 2) * weight_rating
		b = (price / high_price) * weight_price
		self.score = a - b
		#return review_score ** 2 / math.log(price + 2)  # your scoring formula

	def __str__(self):
		return (
			f"{self.title}\n"
			f"  Price: ${self.price / 100:.2f}\n"
			f"  Steam Rating: {self.steam_rating * 100:.2f}%\n"
			f"  Couch Players: {self.couch_players}\n"
			f"  LAN Players: {self.lan_players}\n"
			f"  Online Players: {self.online_players}\n"
			f"  Score: {self.score:.2f}\n"
			f"  URL: {self.steam_url}\n"
		)
	
	def to_dict(self):
		return {
			"title": self.title,
			"steam_id": self.steam_id,
			"score": self.score,
			"price": self.price,
			"steam_rating": self.steam_rating,
			"number_of_reviews": self.number_of_reviews,
			"is_released": self.is_released,
			"release_date": self.release_date.strftime("%d %b, %Y") if self.is_released else None,
			"couch_players": self.couch_players,
			"lan_players": self.lan_players,
			"online_players": self.online_players,
			"cooptimus_url": self.cooptimus_url,
			"steam_url": self.steam_url,
			"header_image": self.header_image,
			"short_description": self.short_description,
			"tags": self.tags,
		}

	@classmethod
	def from_dict(cls, data):
		obj = cls()
		obj.title = data["title"]
		obj.steam_id = int(data["steam_id"])
		obj.price = float(data["price"])
		obj.steam_rating = float(data["steam_rating"])
		obj.number_of_reviews = int(data["number_of_reviews"])
		obj.is_released = bool(data["is_released"])
		date_string = data.get("release_date")
		if obj.is_released and date_string:
			obj.release_date = datetime.strptime(date_string, "%d %b, %Y").date()
		else:
			obj.release_date = None
		obj.couch_players = int(data["couch_players"])
		obj.lan_players = int(data["lan_players"])
		obj.online_players = int(data["online_players"])
		obj.cooptimus_url = data["cooptimus_url"]
		obj.steam_url = data["steam_url"]
		obj.header_image = data["header_image"]
		obj.short_description = data["short_description"]
		obj.tags = data.get("tags", [])
		return obj