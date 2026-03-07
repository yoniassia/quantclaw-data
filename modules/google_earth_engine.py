#!/usr/bin/env python3
"""
Google Earth Engine — Satellite & Geospatial Alternative Data
Platform for analyzing petabyte-scale satellite imagery for quant trading signals.

Data includes:
- NDVI timeseries: Vegetation health (agriculture proxy)
- Land use changes: Development patterns (commercial real estate)
- Nighttime lights: Economic activity proxy (VIIRS/DMSP)
- Surface temperature: Climate impact on commodities
- Water extent: Drought/flood indicators (insurance, agriculture)

Usage:
  python modules/google_earth_engine.py --lat 37.7749 --lon -122.4194 --start 2025-01-01 --end 2025-12-31
  python modules/google_earth_engine.py --function nighttime_lights --region "california" --json

Data source: https://earthengine.google.com/ + fallback to NASA POWER, USGS
Free tier: Unlimited non-commercial use with quotas
"""

import requests
import json
import sys
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import time

# Try to import Earth Engine API
try:
    import ee
    EE_AVAILABLE = True
except ImportError:
    EE_AVAILABLE = False

class GoogleEarthEngine:
    """
    Google Earth Engine satellite data with fallback to alternative APIs.
    
    Primary: earthengine-api (requires authentication)
    Fallback: NASA POWER API, USGS Earth Explorer, open satellite data APIs
    """
    
    # NASA POWER API for weather/climate data
    NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
    
    # USGS Earth Explorer (public, no key needed for some datasets)
    USGS_BASE_URL = "https://earthexplorer.usgs.gov/inventory/json/v/1.4.1"
    
    def __init__(self, ee_credentials_path: Optional[str] = None):
        """
        Initialize Google Earth Engine client.
        
        Args:
            ee_credentials_path: Path to service account JSON (optional)
        """
        self.ee_authenticated = False
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'QuantClaw/1.0 (Earth Engine Data Client)'
        })
        
        if EE_AVAILABLE:
            try:
                if ee_credentials_path:
                    credentials = ee.ServiceAccountCredentials(None, ee_credentials_path)
                    ee.Initialize(credentials)
                else:
                    ee.Initialize()
                self.ee_authenticated = True
            except Exception as e:
                print(f"⚠️  Earth Engine auth failed: {e}. Using fallback APIs.", file=sys.stderr)
                self.ee_authenticated = False
    
    def get_ndvi_timeseries(
        self, 
        lat: float, 
        lon: float, 
        start_date: str, 
        end_date: str,
        interval_days: int = 16
    ) -> Dict[str, Any]:
        """
        Get NDVI (Normalized Difference Vegetation Index) timeseries.
        
        NDVI measures vegetation health (0-1 scale). Useful for:
        - Agriculture: Crop health, yield prediction
        - Commodities: Wheat, corn, soy production forecasts
        - Climate risk: Drought detection
        
        Args:
            lat: Latitude
            lon: Longitude
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval_days: Data interval (default 16 for MODIS)
        
        Returns:
            {
                'location': {'lat': float, 'lon': float},
                'timeseries': [{'date': str, 'ndvi': float, 'quality': str}, ...],
                'summary': {'mean': float, 'std': float, 'min': float, 'max': float},
                'source': str,
                'timestamp': str
            }
        """
        if self.ee_authenticated:
            return self._get_ndvi_ee(lat, lon, start_date, end_date, interval_days)
        else:
            return self._get_ndvi_fallback(lat, lon, start_date, end_date, interval_days)
    
    def _get_ndvi_ee(self, lat, lon, start_date, end_date, interval_days) -> Dict[str, Any]:
        """Get NDVI using Earth Engine API (MODIS Terra)"""
        try:
            point = ee.Geometry.Point([lon, lat])
            
            # MODIS Terra Vegetation Indices 16-Day Global 250m
            collection = ee.ImageCollection('MODIS/006/MOD13Q1') \
                .filterDate(start_date, end_date) \
                .filterBounds(point)
            
            def extract_ndvi(image):
                ndvi = image.select('NDVI').multiply(0.0001)  # Scale factor
                date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
                value = ndvi.reduceRegion(
                    reducer=ee.Reducer.first(),
                    geometry=point,
                    scale=250
                ).get('NDVI')
                return ee.Feature(None, {'date': date, 'ndvi': value})
            
            features = collection.map(extract_ndvi).getInfo()['features']
            
            timeseries = []
            for feat in features:
                props = feat['properties']
                if props.get('ndvi') is not None:
                    timeseries.append({
                        'date': props['date'],
                        'ndvi': round(props['ndvi'], 4),
                        'quality': 'good' if props['ndvi'] > 0 else 'low'
                    })
            
            # Calculate summary stats
            ndvi_values = [x['ndvi'] for x in timeseries if x['ndvi'] is not None]
            summary = {}
            if ndvi_values:
                summary = {
                    'mean': round(sum(ndvi_values) / len(ndvi_values), 4),
                    'min': round(min(ndvi_values), 4),
                    'max': round(max(ndvi_values), 4),
                    'std': round(self._std_dev(ndvi_values), 4)
                }
            
            return {
                'location': {'lat': lat, 'lon': lon},
                'timeseries': timeseries,
                'summary': summary,
                'source': 'Google Earth Engine (MODIS/006/MOD13Q1)',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {'error': f'Earth Engine NDVI error: {str(e)}', 'location': {'lat': lat, 'lon': lon}}
    
    def _get_ndvi_fallback(self, lat, lon, start_date, end_date, interval_days) -> Dict[str, Any]:
        """
        Fallback NDVI using NASA POWER API (estimates from temperature/radiation).
        Note: This is a proxy, not true NDVI. For production, use authenticated EE.
        """
        try:
            # Use NASA POWER to get vegetation-relevant parameters
            params = {
                'parameters': 'T2M,PRECTOTCORR,ALLSKY_SFC_SW_DWN',  # Temp, precip, solar radiation
                'community': 'AG',
                'longitude': lon,
                'latitude': lat,
                'start': start_date.replace('-', ''),
                'end': end_date.replace('-', ''),
                'format': 'JSON'
            }
            
            response = self.session.get(self.NASA_POWER_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'properties' not in data or 'parameter' not in data['properties']:
                return {'error': 'NASA POWER API returned invalid data', 'location': {'lat': lat, 'lon': lon}}
            
            params_data = data['properties']['parameter']
            
            # Estimate NDVI proxy from temperature, precipitation, and solar radiation
            # This is a simplified model: NDVI correlates with moisture and warmth
            timeseries = []
            dates = sorted(params_data.get('T2M', {}).keys())
            
            for date in dates:
                temp = params_data.get('T2M', {}).get(date, 0)
                precip = params_data.get('PRECTOTCORR', {}).get(date, 0)
                solar = params_data.get('ALLSKY_SFC_SW_DWN', {}).get(date, 0)
                
                # Simple NDVI proxy: (normalized temp + precip factor + solar factor) / 3
                # Real NDVI would use near-infrared and red bands
                ndvi_proxy = min(1.0, max(0.0, (
                    (temp + 20) / 60 * 0.4 +  # Temp contribution (scaled to 0-1)
                    min(precip / 10, 1.0) * 0.3 +  # Precip contribution
                    (solar / 300) * 0.3  # Solar contribution
                )))
                
                if len(timeseries) % interval_days == 0:  # Sample at interval
                    timeseries.append({
                        'date': f"{date[:4]}-{date[4:6]}-{date[6:]}",
                        'ndvi': round(ndvi_proxy, 4),
                        'quality': 'estimated'
                    })
            
            ndvi_values = [x['ndvi'] for x in timeseries]
            summary = {
                'mean': round(sum(ndvi_values) / len(ndvi_values), 4) if ndvi_values else 0,
                'min': round(min(ndvi_values), 4) if ndvi_values else 0,
                'max': round(max(ndvi_values), 4) if ndvi_values else 0,
                'std': round(self._std_dev(ndvi_values), 4) if ndvi_values else 0
            }
            
            return {
                'location': {'lat': lat, 'lon': lon},
                'timeseries': timeseries,
                'summary': summary,
                'source': 'NASA POWER API (NDVI proxy - use EE for real NDVI)',
                'timestamp': datetime.utcnow().isoformat(),
                'warning': 'This is an NDVI proxy based on temperature/precip. Authenticate Earth Engine for true NDVI from satellite imagery.'
            }
            
        except Exception as e:
            return {'error': f'Fallback NDVI error: {str(e)}', 'location': {'lat': lat, 'lon': lon}}
    
    def get_land_use_change(
        self,
        lat: float,
        lon: float,
        radius_km: float,
        start_year: int,
        end_year: int
    ) -> Dict[str, Any]:
        """
        Detect land use changes (urban expansion, deforestation, agriculture).
        
        Useful for:
        - Real estate: Development patterns
        - Commodities: Deforestation impact on timber/palm oil
        - Infrastructure: New road/building construction
        
        Args:
            lat: Center latitude
            lon: Center longitude
            radius_km: Search radius in kilometers
            start_year: Start year
            end_year: End year
        
        Returns:
            {
                'location': {'lat': float, 'lon': float, 'radius_km': float},
                'changes': [{'type': str, 'area_km2': float, 'confidence': float}, ...],
                'summary': {'total_change_km2': float, 'change_pct': float},
                'source': str,
                'timestamp': str
            }
        """
        if self.ee_authenticated:
            return self._get_land_use_ee(lat, lon, radius_km, start_year, end_year)
        else:
            return self._get_land_use_fallback(lat, lon, radius_km, start_year, end_year)
    
    def _get_land_use_ee(self, lat, lon, radius_km, start_year, end_year) -> Dict[str, Any]:
        """Get land use change using Earth Engine (MODIS Land Cover)"""
        try:
            point = ee.Geometry.Point([lon, lat])
            region = point.buffer(radius_km * 1000)  # Convert km to meters
            
            # MODIS Land Cover Type (yearly)
            start_img = ee.ImageCollection('MODIS/006/MCD12Q1') \
                .filterDate(f'{start_year}-01-01', f'{start_year}-12-31') \
                .select('LC_Type1') \
                .first()
            
            end_img = ee.ImageCollection('MODIS/006/MCD12Q1') \
                .filterDate(f'{end_year}-01-01', f'{end_year}-12-31') \
                .select('LC_Type1') \
                .first()
            
            # Calculate area change by class
            def calc_area(image, label):
                mask = image.eq(label)
                area = mask.multiply(ee.Image.pixelArea()).reduceRegion(
                    reducer=ee.Reducer.sum(),
                    geometry=region,
                    scale=500,
                    maxPixels=1e9
                ).get('LC_Type1')
                return area
            
            # Land cover classes (IGBP)
            classes = {
                1: 'Evergreen Needleleaf Forest',
                2: 'Evergreen Broadleaf Forest',
                10: 'Grasslands',
                12: 'Croplands',
                13: 'Urban and Built-up',
                16: 'Barren'
            }
            
            changes = []
            for class_id, class_name in classes.items():
                start_area = calc_area(start_img, class_id)
                end_area = calc_area(end_img, class_id)
                
                start_val = start_area.getInfo() if start_area else 0
                end_val = end_area.getInfo() if end_area else 0
                
                if start_val or end_val:
                    change_m2 = end_val - start_val
                    change_km2 = change_m2 / 1e6
                    
                    if abs(change_km2) > 0.1:  # Filter small changes
                        changes.append({
                            'type': class_name,
                            'area_km2': round(change_km2, 2),
                            'confidence': 0.8  # MODIS typical accuracy
                        })
            
            total_change = sum(abs(c['area_km2']) for c in changes)
            area_km2 = 3.14159 * (radius_km ** 2)
            
            return {
                'location': {'lat': lat, 'lon': lon, 'radius_km': radius_km},
                'period': {'start_year': start_year, 'end_year': end_year},
                'changes': changes,
                'summary': {
                    'total_change_km2': round(total_change, 2),
                    'change_pct': round(total_change / area_km2 * 100, 2) if area_km2 > 0 else 0
                },
                'source': 'Google Earth Engine (MODIS/006/MCD12Q1)',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {'error': f'Earth Engine land use error: {str(e)}', 'location': {'lat': lat, 'lon': lon}}
    
    def _get_land_use_fallback(self, lat, lon, radius_km, start_year, end_year) -> Dict[str, Any]:
        """Fallback: Return graceful error for land use (requires satellite imagery)"""
        return {
            'error': 'Land use change requires satellite imagery access. Please authenticate Google Earth Engine.',
            'location': {'lat': lat, 'lon': lon, 'radius_km': radius_km},
            'period': {'start_year': start_year, 'end_year': end_year},
            'recommendation': 'Install earthengine-api and authenticate with: ee.Authenticate()',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_nighttime_lights(
        self,
        region: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Get VIIRS nighttime lights data (economic activity proxy).
        
        Nighttime lights correlate with:
        - GDP growth
        - Industrial production
        - Retail activity
        - Post-disaster recovery
        
        Args:
            region: Region name or bounding box
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            {
                'region': str,
                'timeseries': [{'date': str, 'avg_radiance': float}, ...],
                'summary': {'mean': float, 'trend': str},
                'source': str,
                'timestamp': str
            }
        """
        if self.ee_authenticated:
            return self._get_nightlights_ee(region, start_date, end_date)
        else:
            return self._get_nightlights_fallback(region, start_date, end_date)
    
    def _get_nightlights_ee(self, region, start_date, end_date) -> Dict[str, Any]:
        """Get nighttime lights using Earth Engine (VIIRS)"""
        try:
            # VIIRS Nighttime Day/Night Band Composites
            collection = ee.ImageCollection('NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG') \
                .filterDate(start_date, end_date)
            
            # Define region (simplified - use country boundaries or bbox)
            # For demo, use a point-based approach
            # In production, resolve region name to geometry
            roi = ee.Geometry.Rectangle([-180, -90, 180, 90])  # Global (placeholder)
            
            def extract_avg(image):
                avg_radiance = image.select('avg_rad').reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=roi,
                    scale=1000,
                    maxPixels=1e9
                ).get('avg_rad')
                
                date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
                return ee.Feature(None, {'date': date, 'avg_radiance': avg_radiance})
            
            features = collection.map(extract_avg).getInfo()['features']
            
            timeseries = []
            for feat in features:
                props = feat['properties']
                if props.get('avg_radiance') is not None:
                    timeseries.append({
                        'date': props['date'],
                        'avg_radiance': round(props['avg_radiance'], 4)
                    })
            
            # Calculate trend
            values = [x['avg_radiance'] for x in timeseries]
            trend = 'increasing' if values and values[-1] > values[0] else 'decreasing' if values else 'stable'
            
            return {
                'region': region,
                'timeseries': timeseries,
                'summary': {
                    'mean': round(sum(values) / len(values), 4) if values else 0,
                    'trend': trend
                },
                'source': 'Google Earth Engine (NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG)',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {'error': f'Earth Engine nighttime lights error: {str(e)}', 'region': region}
    
    def _get_nightlights_fallback(self, region, start_date, end_date) -> Dict[str, Any]:
        """Fallback: Graceful error for nighttime lights"""
        return {
            'error': 'Nighttime lights require VIIRS satellite data. Please authenticate Google Earth Engine.',
            'region': region,
            'period': {'start_date': start_date, 'end_date': end_date},
            'recommendation': 'Install earthengine-api and authenticate with: ee.Authenticate()',
            'alternative': 'Contact NOAA for VIIRS data downloads or use EOG VIIRS downloads',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_surface_temperature(
        self,
        lat: float,
        lon: float,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Get land surface temperature timeseries.
        
        Useful for:
        - Commodities: Heat stress on crops
        - Energy: Cooling/heating demand
        - Climate risk: Extreme temperature events
        
        Args:
            lat: Latitude
            lon: Longitude
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            {
                'location': {'lat': float, 'lon': float},
                'timeseries': [{'date': str, 'temp_c': float, 'temp_k': float}, ...],
                'summary': {'mean_c': float, 'min_c': float, 'max_c': float},
                'source': str,
                'timestamp': str
            }
        """
        # Use NASA POWER regardless (more reliable for temperature)
        return self._get_temperature_nasa(lat, lon, start_date, end_date)
    
    def _get_temperature_nasa(self, lat, lon, start_date, end_date) -> Dict[str, Any]:
        """Get surface temperature using NASA POWER API"""
        try:
            params = {
                'parameters': 'T2M,T2M_MAX,T2M_MIN',  # 2m temp, max, min
                'community': 'AG',
                'longitude': lon,
                'latitude': lat,
                'start': start_date.replace('-', ''),
                'end': end_date.replace('-', ''),
                'format': 'JSON'
            }
            
            response = self.session.get(self.NASA_POWER_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'properties' not in data or 'parameter' not in data['properties']:
                return {'error': 'NASA POWER API returned invalid data', 'location': {'lat': lat, 'lon': lon}}
            
            params_data = data['properties']['parameter']
            
            timeseries = []
            dates = sorted(params_data.get('T2M', {}).keys())
            
            for date in dates:
                temp = params_data.get('T2M', {}).get(date)
                if temp is not None:
                    timeseries.append({
                        'date': f"{date[:4]}-{date[4:6]}-{date[6:]}",
                        'temp_c': round(temp, 2),
                        'temp_k': round(temp + 273.15, 2)
                    })
            
            temps = [x['temp_c'] for x in timeseries]
            summary = {
                'mean_c': round(sum(temps) / len(temps), 2) if temps else 0,
                'min_c': round(min(temps), 2) if temps else 0,
                'max_c': round(max(temps), 2) if temps else 0,
                'std_c': round(self._std_dev(temps), 2) if temps else 0
            }
            
            return {
                'location': {'lat': lat, 'lon': lon},
                'timeseries': timeseries,
                'summary': summary,
                'source': 'NASA POWER API',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {'error': f'Temperature API error: {str(e)}', 'location': {'lat': lat, 'lon': lon}}
    
    def get_water_extent(
        self,
        region: str,
        date: str
    ) -> Dict[str, Any]:
        """
        Get water body extent (drought/flood indicator).
        
        Useful for:
        - Agriculture: Irrigation availability
        - Insurance: Flood risk assessment
        - Commodities: Water-intensive crop impacts
        
        Args:
            region: Region name or coordinates
            date: Date (YYYY-MM-DD)
        
        Returns:
            {
                'region': str,
                'date': str,
                'water_extent_km2': float,
                'change_vs_baseline': float,
                'status': str,
                'source': str,
                'timestamp': str
            }
        """
        if self.ee_authenticated:
            return self._get_water_ee(region, date)
        else:
            return self._get_water_fallback(region, date)
    
    def _get_water_ee(self, region, date) -> Dict[str, Any]:
        """Get water extent using Earth Engine (JRC Global Surface Water)"""
        try:
            # JRC Global Surface Water Mapping Layers
            # Use occurrence layer for baseline + monthly water history
            jrc = ee.Image('JRC/GSW1_4/GlobalSurfaceWater')
            
            # For demo, use a bounding box (in production, resolve region name)
            roi = ee.Geometry.Rectangle([-180, -90, 180, 90])
            
            # Calculate water extent
            water_mask = jrc.select('occurrence').gt(50)  # >50% water occurrence
            water_area = water_mask.multiply(ee.Image.pixelArea()).reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=roi,
                scale=30,
                maxPixels=1e10
            ).get('occurrence')
            
            water_km2 = water_area.getInfo() / 1e6 if water_area else 0
            
            return {
                'region': region,
                'date': date,
                'water_extent_km2': round(water_km2, 2),
                'change_vs_baseline': 0.0,  # Would need historical comparison
                'status': 'normal',
                'source': 'Google Earth Engine (JRC/GSW1_4/GlobalSurfaceWater)',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {'error': f'Earth Engine water extent error: {str(e)}', 'region': region}
    
    def _get_water_fallback(self, region, date) -> Dict[str, Any]:
        """Fallback: Graceful error for water extent"""
        return {
            'error': 'Water extent requires satellite imagery. Please authenticate Google Earth Engine.',
            'region': region,
            'date': date,
            'recommendation': 'Install earthengine-api and authenticate with: ee.Authenticate()',
            'alternative': 'Use USGS WaterWatch for US rivers or contact ESA for Sentinel-2 water masks',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if not values or len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5


def main():
    parser = argparse.ArgumentParser(
        description='Google Earth Engine — Satellite & Geospatial Alternative Data'
    )
    parser.add_argument('--function', type=str, default='ndvi',
                       choices=['ndvi', 'land_use', 'nighttime_lights', 'temperature', 'water'],
                       help='Function to execute')
    parser.add_argument('--lat', type=float, help='Latitude')
    parser.add_argument('--lon', type=float, help='Longitude')
    parser.add_argument('--region', type=str, help='Region name')
    parser.add_argument('--radius', type=float, default=10.0, help='Radius in km')
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--start-year', type=int, help='Start year')
    parser.add_argument('--end-year', type=int, help='End year')
    parser.add_argument('--json', action='store_true', help='Output raw JSON')
    parser.add_argument('--credentials', type=str, help='Path to EE service account JSON')
    
    args = parser.parse_args()
    
    # Set defaults if not provided
    if not args.start:
        args.start = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    if not args.end:
        args.end = datetime.now().strftime('%Y-%m-%d')
    
    gee = GoogleEarthEngine(ee_credentials_path=args.credentials)
    
    # Execute function
    if args.function == 'ndvi':
        if not args.lat or not args.lon:
            print("❌ Error: --lat and --lon required for NDVI")
            sys.exit(1)
        data = gee.get_ndvi_timeseries(args.lat, args.lon, args.start, args.end)
    
    elif args.function == 'land_use':
        if not args.lat or not args.lon or not args.start_year or not args.end_year:
            print("❌ Error: --lat, --lon, --start-year, --end-year required")
            sys.exit(1)
        data = gee.get_land_use_change(args.lat, args.lon, args.radius, args.start_year, args.end_year)
    
    elif args.function == 'nighttime_lights':
        if not args.region:
            print("❌ Error: --region required for nighttime lights")
            sys.exit(1)
        data = gee.get_nighttime_lights(args.region, args.start, args.end)
    
    elif args.function == 'temperature':
        if not args.lat or not args.lon:
            print("❌ Error: --lat and --lon required for temperature")
            sys.exit(1)
        data = gee.get_surface_temperature(args.lat, args.lon, args.start, args.end)
    
    elif args.function == 'water':
        if not args.region:
            print("❌ Error: --region required for water extent")
            sys.exit(1)
        data = gee.get_water_extent(args.region, args.start)
    
    else:
        print(f"❌ Unknown function: {args.function}")
        sys.exit(1)
    
    # Output
    if args.json:
        print(json.dumps(data, indent=2))
        return
    
    # Pretty print
    if 'error' in data:
        print(f"\n❌ Error: {data['error']}")
        if 'recommendation' in data:
            print(f"💡 {data['recommendation']}")
        sys.exit(1)
    
    print(f"\n{'='*70}")
    print(f"🛰️  Google Earth Engine — {args.function.upper()}")
    print(f"{'='*70}\n")
    
    if args.function == 'ndvi':
        print(f"📍 Location: {data['location']['lat']}, {data['location']['lon']}")
        print(f"📊 Data points: {len(data.get('timeseries', []))}")
        if data.get('summary'):
            s = data['summary']
            print(f"\n🌿 NDVI Summary:")
            print(f"  Mean:  {s.get('mean', 0):.4f}")
            print(f"  Min:   {s.get('min', 0):.4f}")
            print(f"  Max:   {s.get('max', 0):.4f}")
            print(f"  Std:   {s.get('std', 0):.4f}")
        if data.get('warning'):
            print(f"\n⚠️  {data['warning']}")
    
    elif args.function == 'temperature':
        print(f"📍 Location: {data['location']['lat']}, {data['location']['lon']}")
        print(f"📊 Data points: {len(data.get('timeseries', []))}")
        if data.get('summary'):
            s = data['summary']
            print(f"\n🌡️  Temperature Summary:")
            print(f"  Mean:  {s.get('mean_c', 0):.2f}°C")
            print(f"  Min:   {s.get('min_c', 0):.2f}°C")
            print(f"  Max:   {s.get('max_c', 0):.2f}°C")
            print(f"  Std:   {s.get('std_c', 0):.2f}°C")
    
    elif args.function == 'land_use':
        print(f"📍 Location: {data['location']['lat']}, {data['location']['lon']}")
        print(f"🔍 Radius: {data['location']['radius_km']} km")
        if data.get('changes'):
            print(f"\n🏗️  Land Use Changes ({args.start_year} → {args.end_year}):")
            for change in data['changes']:
                print(f"  {change['type']}: {change['area_km2']:+.2f} km²")
    
    print(f"\n📡 Source: {data.get('source', 'Unknown')}")
    print(f"🕐 Timestamp: {data.get('timestamp', 'Unknown')}")
    print()

if __name__ == '__main__':
    main()
