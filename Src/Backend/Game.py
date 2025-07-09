
import math
from datetime import datetime
from Price import Price

class Game:
	title: str = ""
	steam_id: int = -1					# Steam's app ID
	prices = {}							# Prices per region (country code as key, Price object as value)
	delisted = {}						# Delisted countries (country code as key)
	steam_rating: float = 0				# 0.0–1.0 float (e.g., 0.85)
	number_of_reviews: int = 0
	release_date: str = None			# Date time
	couch_players: int = 0				# Supported couch players
	lan_players: int = 0				# Supported LAN players
	online_players: int = 0				# Supported online players
	cooptimus_url: str = ""
	steam_url: str = ""
	header_image: str = None
	short_description: str = ""
	tags = []

	is_released: bool = True
	is_removed: bool = True
	score: float = 0					# Algorithm scoring
	
	def compute_score(self, rating_weight, price_weight, sale_weight, number_of_reviews_weight, high_price, country_code):
		price = self.get_price(country_code)
		rating_score = (self.steam_rating ** 2) * rating_weight
		price_score = -(price.final / 100.0 / high_price) * price_weight
		sale_score = (1 - price.final / price.initial) * sale_weight if price.initial > 0 else 0
		high_number_of_reviews = 10000
		number_of_reviews_score = (math.log(self.number_of_reviews + 1) / math.log(high_number_of_reviews)) * number_of_reviews_weight

		self.score = rating_score + price_score + sale_score + number_of_reviews_score
		#return review_score ** 2 / math.log(price + 2)  # your scoring formula

	def get_price(self, country_code):
		if country_code in self.prices:
			return self.prices[country_code]
		else:
			return Price(0, 0)
		
	def is_listed_in_country(self, country_code):
		if country_code in self.delisted:
			return False
		return True
	
	def to_dict(self):
		return {
			"title": self.title,
			"steam_id": self.steam_id,
			"score": self.score,
			"prices": {country_code: price.to_dict() for country_code, price in self.prices.items()},
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
	
	def sendable_dict(self, country_code):
		sendable = self.to_dict()
		price = self.prices[country_code] if country_code in self.prices else None
		sendable.pop("prices", None)
		sendable.pop("delisted", None)
		sendable["price"] = price.to_dict() if price else None
		return sendable

	@classmethod
	def from_dict(cls, data):
		obj = cls()
		obj.title = data["title"]
		obj.steam_id = int(data["steam_id"])
		obj.prices = {country_code: Price.from_dict(price_data) for country_code, price_data in data["prices"].items()}
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