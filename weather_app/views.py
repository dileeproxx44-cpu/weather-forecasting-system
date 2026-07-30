from django.shortcuts import render
from .services import WeatherService
from .models import SearchHistory

def index(request):
    query = request.GET.get('city', 'London').strip()
    if not query:
        query = 'London'
        
    error_message = None
    weather_data = None
    city_display = None
    country_display = None

    # Step 1: Geocode the search query
    geo_info = WeatherService.geocode_city(query)
    
    if geo_info:
        # Step 2: Fetch weather using coordinates
        weather_data = WeatherService.get_weather_data(geo_info['latitude'], geo_info['longitude'])
        if weather_data:
            city_display = geo_info['city']
            country_display = geo_info['country']
            # Save valid search to database
            SearchHistory.objects.create(city_name=city_display)
        else:
            error_message = f"Could not retrieve weather details for '{query}'."
    else:
        error_message = f"City '{query}' not found. Please check the spelling."

    # If the current search failed, fall back to default 'London' weather
    if not weather_data:
        fallback_geo = WeatherService.geocode_city('London')
        if fallback_geo:
            weather_data = WeatherService.get_weather_data(fallback_geo['latitude'], fallback_geo['longitude'])
            city_display = fallback_geo['city']
            country_display = fallback_geo['country']
        else:
            # Absolute fallback if API is completely down
            city_display = 'London'
            country_display = 'United Kingdom'
            weather_data = {
                "current": {
                    "temp": "--", "feels_like": "--", "humidity": "--",
                    "wind_speed": "--", "pressure": "--", "desc": "API Offline",
                    "emoji": "⚠️", "sunrise": "--", "sunset": "--"
                },
                "forecast": []
            }

    # Fetch recent unique search history
    recent_db = SearchHistory.objects.all()[:15]
    seen = set()
    history = []
    for item in recent_db:
        name = item.city_name.title()
        if name not in seen:
            seen.add(name)
            history.append(name)
        if len(history) >= 5:
            break

    context = {
        'city': city_display,
        'country': country_display,
        'current': weather_data.get('current'),
        'forecast': weather_data.get('forecast'),
        'history': history,
        'error': error_message,
        'search_query': query if error_message else city_display
    }
    
    return render(request, 'weather_app/index.html', context)

