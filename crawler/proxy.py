"""
Proxy rotation for avoiding IP blocking
"""
import logging
import random
import requests
from typing import Dict, List, Any, Optional
from config.settings import PROXY_ROTATION_FREQUENCY

logger = logging.getLogger(__name__)

class ProxyManager:
    """Manage proxy rotation for crawler"""
    
    def __init__(self):
        """Initialize the proxy manager"""
        self.proxies = []
        self.current_proxy = None
        self.request_count = 0
        self.fetch_proxies()
    
    def fetch_proxies(self) -> None:
        """
        Fetch a list of free proxies from various sources
        """
        try:
            # Try multiple free proxy sources
            sources = [
                self._fetch_from_free_proxy_list(),
                self._fetch_from_proxy_nova(),
                self._fetch_from_geonode()
            ]
            
            # Combine proxies from all sources
            all_proxies = []
            for source_proxies in sources:
                if source_proxies:
                    all_proxies.extend(source_proxies)
            
            if all_proxies:
                # Filter and verify proxies
                verified_proxies = self._verify_proxies(all_proxies)
                if verified_proxies:
                    self.proxies = verified_proxies
                    logger.info(f"Loaded {len(self.proxies)} verified proxies")
                    return
                    
            # Fallback: add some hardcoded free proxies if no other sources worked
            self._add_fallback_proxies()
            
        except Exception as e:
            logger.error(f"Error fetching proxies: {e}")
            self._add_fallback_proxies()
    
    def _fetch_from_free_proxy_list(self) -> List[Dict[str, Any]]:
        """Fetch proxies from free-proxy-list.net"""
        try:
            response = requests.get('https://free-proxy-list.net/', timeout=10)
            if response.status_code != 200:
                return []
                
            # Basic parsing - in production, use BeautifulSoup for better parsing
            proxies = []
            rows = response.text.split('<tr><td>')[1:]
            for row in rows:
                try:
                    parts = row.split('</td><td>')
                    if len(parts) >= 7:
                        ip = parts[0]
                        port = parts[1]
                        https = 'yes' in parts[6].lower()
                        protocol = 'https' if https else 'http'
                        
                        proxies.append({
                            'ip': ip,
                            'port': port,
                            'protocol': protocol
                        })
                except:
                    continue
                    
            return proxies
        except:
            return []
    
    def _fetch_from_proxy_nova(self) -> List[Dict[str, Any]]:
        """Fetch proxies from proxynova.com"""
        try:
            response = requests.get('https://www.proxynova.com/proxy-server-list/', timeout=10)
            if response.status_code != 200:
                return []
            
            # Simplified parsing - in production, use BeautifulSoup
            proxies = []
            for line in response.text.split('\n'):
                if 'data-ip=' in line and '<td>' in line:
                    try:
                        ip_part = line.split('data-ip=')[1].split('>')[1].split('<')[0].strip()
                        port_part = line.split('</td>')[1].split('<td>')[1].split('</td>')[0].strip()
                        
                        if ip_part and port_part.isdigit():
                            proxies.append({
                                'ip': ip_part,
                                'port': port_part,
                                'protocol': 'http'
                            })
                    except:
                        continue
            
            return proxies
        except:
            return []
    
    def _fetch_from_geonode(self) -> List[Dict[str, Any]]:
        """Fetch proxies from geonode.com API"""
        try:
            url = "https://proxylist.geonode.com/api/proxy-list?limit=50&page=1&sort_by=lastChecked&sort_type=desc"
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                return []
            
            data = response.json()
            proxies = []
            
            if 'data' in data:
                for proxy in data['data']:
                    try:
                        proxies.append({
                            'ip': proxy['ip'],
                            'port': proxy['port'],
                            'protocol': proxy['protocols'][0].lower() if proxy['protocols'] else 'http'
                        })
                    except:
                        continue
            
            return proxies
        except:
            return []
    
    def _verify_proxies(self, proxy_list: List[Dict[str, Any]], max_verify: int = 20) -> List[Dict[str, Any]]:
        """
        Verify proxies are working by testing them
        
        Args:
            proxy_list: List of proxy dictionaries
            max_verify: Maximum number of proxies to verify (to avoid long startup times)
            
        Returns:
            List of working proxies
        """
        working_proxies = []
        
        # Shuffle and limit to avoid always checking the same proxies
        random.shuffle(proxy_list)
        proxy_list = proxy_list[:max_verify]
        
        for proxy in proxy_list:
            try:
                proxy_url = f"{proxy['protocol']}://{proxy['ip']}:{proxy['port']}"
                
                # Test proxy with a 5-second timeout
                test_request = requests.get(
                    'https://httpbin.org/ip',
                    proxies={'http': proxy_url, 'https': proxy_url},
                    timeout=5
                )
                
                if test_request.status_code == 200:
                    working_proxies.append(proxy)
                    logger.debug(f"Verified working proxy: {proxy_url}")
            except:
                # Proxy didn't work, skip it
                continue
        
        return working_proxies
    
    def _add_fallback_proxies(self) -> None:
        """Add fallback proxies if no other sources work"""
        # Note: These are example proxies and will likely not work in production
        # In a real system, you would use a paid proxy service with an API
        fallback_proxies = [
            {'ip': '165.225.114.76', 'port': '10605', 'protocol': 'http'},
            {'ip': '165.225.208.76', 'port': '10605', 'protocol': 'http'},
            {'ip': '165.225.39.90', 'port': '10605', 'protocol': 'https'},
            {'ip': '112.245.48.74', 'port': '9002', 'protocol': 'http'},
            {'ip': '45.77.107.242', 'port': '3128', 'protocol': 'http'}
        ]
        
        # Try to verify these fallback proxies
        verified = self._verify_proxies(fallback_proxies)
        
        if verified:
            self.proxies = verified
            logger.info(f"Using {len(verified)} fallback proxies")
        else:
            # Last resort: no proxies available, just add the fallback ones anyway
            self.proxies = fallback_proxies
            logger.warning("No working proxies available, using unverified fallback proxies")
    
    def get_proxy(self) -> Optional[Dict[str, Any]]:
        """
        Get the next proxy in rotation
        
        Returns:
            Dictionary with proxy information or None if no proxies available
        """
        if not self.proxies:
            self.fetch_proxies()
            
        if not self.proxies:
            logger.warning("No proxies available")
            return None
        
        # Check if we need to rotate proxy
        if self.request_count >= PROXY_ROTATION_FREQUENCY or self.current_proxy is None:
            self.current_proxy = random.choice(self.proxies)
            self.request_count = 0
            logger.debug(f"Rotating to new proxy: {self.current_proxy['ip']}:{self.current_proxy['port']}")
            
        self.request_count += 1
        return self.current_proxy