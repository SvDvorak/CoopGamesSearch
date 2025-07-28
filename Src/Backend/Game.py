
import math
from datetime import datetime, date
from Price import Price

class Game:
	title: str = ""
	steam_id: int = -1					# Steam's app ID
	price: Price = None					# Price for region that was requested. Used during game retrieval.
	steam_rating: float = 0				# 0.0–1.0 float (e.g., 0.85)
	number_of_reviews: int = 0
	release_date: date = None			# Date time
	couch_players: int = 0				# Supported couch players
	lan_players: int = 0				# Supported LAN players
	online_players: int = 0				# Supported online players
	cooptimus_url: str = ""
	steam_url: str = ""
	header_image: str = None
	short_description: str = ""
	tags: list[str] = []
	is_released: bool = True
	score: float = 0  					# Calculated score when retrieved

	is_removed: bool = True 			# Only used temporarily while scraping, games with this set to true will be discarded
	
	def to_dict(self):
		return {
			"title": self.title,
			"steam_id": self.steam_id,
			"score": self.score,
			"price": self.price.to_dict() if self.price != None else None,
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

	# TODO Remove when JSON persistance is removed
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