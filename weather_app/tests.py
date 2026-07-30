from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
from .models import SearchHistory
from .services import WeatherService, get_weather_desc

class WeatherAppTests(TestCase):
    def test_wmo_code_mapping(self):
        """Test that WMO codes resolve to descriptions and emojis."""
        clear = get_weather_desc(0)
        self.assertEqual(clear["desc"], "Clear sky")
        self.assertEqual(clear["emoji"], "☀️")
        
        unknown = get_weather_desc(999)
        self.assertIn("Unknown", unknown["desc"])

    def test_search_history_model(self):
        """Test the SearchHistory model creation and string representation."""
        history = SearchHistory.objects.create(city_name="Rome")
        self.assertEqual(history.city_name, "Rome")
        self.assertIn("Rome", str(history))

    @patch('weather_app.services.requests.get')
    def test_geocode_city_success(self, mock_get):
        """Test successful geocoding API parsing."""
        mock_response = {
            "results": [{
                "name": "Paris",
                "latitude": 48.8534,
                "longitude": 2.3488,
                "country": "France"
            }]
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response
        
        result = WeatherService.geocode_city("Paris")
        self.assertIsNotNone(result)
        self.assertEqual(result["city"], "Paris")
        self.assertEqual(result["latitude"], 48.8534)
        self.assertEqual(result["longitude"], 2.3488)

    @patch('weather_app.services.requests.get')
    def test_geocode_city_not_found(self, mock_get):
        """Test geocoding returns None when city doesn't exist."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"results": []}
        
        result = WeatherService.geocode_city("FakeCity12345")
        self.assertIsNull = self.assertIsNone(result)

    @patch('weather_app.views.WeatherService.geocode_city')
    @patch('weather_app.views.WeatherService.get_weather_data')
    def test_index_view_success(self, mock_weather, mock_geocode):
        """Test index view returns 200 and renders template with weather data."""
        mock_geocode.return_value = {
            "latitude": 35.6895,
            "longitude": 139.6917,
            "city": "Tokyo",
            "country": "Japan"
        }
        mock_weather.return_value = {
            "current": {
                "temp": 28.5,
                "feels_like": 30.2,
                "humidity": 70,
                "wind_speed": 12.5,
                "pressure": 1008.2,
                "desc": "Partly cloudy",
                "emoji": "⛅",
                "sunrise": "05:12 AM",
                "sunset": "06:45 PM"
            },
            "forecast": [
                {"day": "Wednesday", "date": "Jul 29", "max_temp": 30, "min_temp": 23, "desc": "Slight rain", "emoji": "🌧️"}
            ]
        }
        
        response = self.client.get(reverse('index'), {'city': 'Tokyo'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tokyo")
        self.assertContains(response, "Japan")
        self.assertContains(response, "28.5")
        self.assertContains(response, "Partly cloudy")
        self.assertContains(response, "70%")
        
        # Verify SearchHistory log
        self.assertEqual(SearchHistory.objects.count(), 1)
        self.assertEqual(SearchHistory.objects.first().city_name, "Tokyo")

    @patch('weather_app.views.WeatherService.geocode_city')
    def test_index_view_invalid_city_fallback(self, mock_geocode):
        """Test that searching an invalid city sets an error message and falls back."""
        # Set geocode to return None for searched city, then succeed for London fallback
        mock_geocode.side_effect = lambda city: None if city == "InvalidCity" else {
            "latitude": 51.5085, "longitude": -0.1257, "city": "London", "country": "United Kingdom"
        }
        
        response = self.client.get(reverse('index'), {'city': 'InvalidCity'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "City &#x27;InvalidCity&#x27; not found. Please check the spelling.")
        self.assertContains(response, "London")

