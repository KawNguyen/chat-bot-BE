"""
Web search service for finding real headphone products
"""
import os
import httpx
from typing import List, Dict, Optional


class WebSearchClient:
    """Web search client using Tavily API or fallback methods"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.tavily_api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.use_tavily = bool(self.tavily_api_key)
    
    async def search_headphones(self, brand: str, product_type: str = "bluetooth", limit: int = 5) -> List[Dict]:
        """
        Tìm kiếm tai nghe thực tế trên mạng
        
        Args:
            brand: Tên hãng (e.g., "Samsung", "Sony", "Apple")
            product_type: Loại tai nghe (e.g., "bluetooth", "wireless", "gaming")
            limit: Số lượng kết quả tối đa
            
        Returns:
            List of products with name, price, description
        """
        query = f"{brand} {product_type} headphones latest models 2024 2025"
        
        if self.use_tavily:
            return await self._search_with_tavily(query, limit)
        else:
            # Fallback: trả về danh sách hardcoded dựa trên knowledge
            return self._get_fallback_products(brand, product_type, limit)
    
    async def _search_with_tavily(self, query: str, limit: int) -> List[Dict]:
        """Search using Tavily API"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": self.tavily_api_key,
                        "query": query,
                        "max_results": limit,
                        "search_depth": "advanced",
                        "include_answer": True,
                        "include_domains": [
                            "gsmarena.com",
                            "rtings.com", 
                            "thegioididong.com",
                            "fptshop.com.vn",
                            "cellphones.com.vn"
                        ]
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                # Parse kết quả từ Tavily
                products = []
                if "results" in data:
                    for result in data["results"][:limit]:
                        product = self._extract_product_info(result)
                        if product:
                            products.append(product)
                
                return products
        except Exception as e:
            print(f"Tavily search error: {e}")
            return []
    
    def _extract_product_info(self, search_result: Dict) -> Optional[Dict]:
        """Extract product information from search result"""
        try:
            title = search_result.get("title", "")
            content = search_result.get("content", "")
            
            # Extract product name from title
            name = title.split("|")[0].strip() if "|" in title else title.strip()
            
            # Try to extract price (simplified - can be improved)
            import re
            price_match = re.search(r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)\s*(?:đ|VND|USD|\$)', content)
            price = None
            if price_match:
                price_str = price_match.group(1).replace(",", "").replace(".", "")
                try:
                    price = int(price_str)
                except:
                    pass
            
            return {
                "name": name,
                "price": price,
                "description": content[:200]  # Limit description length
            }
        except:
            return None
    
    def _get_fallback_products(self, brand: str, product_type: str, limit: int) -> List[Dict]:
        """
        Fallback: Return hardcoded popular products when API is not available
        Updated with 2024-2025 models
        """
        products_db = {
            "samsung": {
                "bluetooth": [
                    {"name": "Samsung Galaxy Buds 3 Pro", "price": 5490000, "description": "ANC cao cấp, âm thanh Hi-Fi"},
                    {"name": "Samsung Galaxy Buds 2 Pro", "price": 4490000, "description": "ANC 360 Audio, IPX7"},
                    {"name": "Samsung Galaxy Buds FE", "price": 2490000, "description": "Giá rẻ, ANC tốt"},
                ],
                "wireless": [
                    {"name": "Samsung Galaxy Buds 3 Pro", "price": 5490000, "description": "ANC cao cấp"},
                    {"name": "Samsung Galaxy Buds Live", "price": 2990000, "description": "Thiết kế Bean độc đáo"},
                ]
            },
            "sony": {
                "bluetooth": [
                    {"name": "Sony WH-1000XM5", "price": 8990000, "description": "ANC hàng đầu thế giới"},
                    {"name": "Sony WF-1000XM5", "price": 6990000, "description": "True wireless cao cấp"},
                    {"name": "Sony LinkBuds S", "price": 4490000, "description": "Nhẹ, ANC thông minh"},
                ],
                "wireless": [
                    {"name": "Sony WH-1000XM5", "price": 8990000, "description": "Over-ear ANC tốt nhất"},
                    {"name": "Sony WH-CH720N", "price": 2990000, "description": "ANC giá rẻ"},
                ],
                "gaming": [
                    {"name": "Sony INZONE H9", "price": 7990000, "description": "Gaming wireless ANC"},
                    {"name": "Sony INZONE H7", "price": 5990000, "description": "Gaming wireless"},
                ]
            },
            "apple": {
                "bluetooth": [
                    {"name": "Apple AirPods Pro 2 (USB-C)", "price": 6490000, "description": "ANC, Spatial Audio, USB-C"},
                    {"name": "Apple AirPods 3", "price": 4990000, "description": "Spatial Audio, chống nước"},
                    {"name": "Apple AirPods Max", "price": 13990000, "description": "Over-ear cao cấp nhất"},
                ],
                "wireless": [
                    {"name": "Apple AirPods Max", "price": 13990000, "description": "Over-ear premium"},
                    {"name": "Apple AirPods Pro 2", "price": 6490000, "description": "In-ear ANC"},
                ]
            },
            "asus": {
                "gaming": [
                    {"name": "Asus ROG Delta S Wireless", "price": 5490000, "description": "Gaming wireless hi-res"},
                    {"name": "Asus ROG Cetra True Wireless", "price": 3990000, "description": "Gaming TWS ANC"},
                    {"name": "Asus ROG Delta S Animate", "price": 6990000, "description": "RGB AniMe Matrix"},
                ],
                "bluetooth": [
                    {"name": "Asus ROG Cetra True Wireless", "price": 3990000, "description": "Gaming TWS"},
                ]
            },
            "jbl": {
                "bluetooth": [
                    {"name": "JBL Tour Pro 2", "price": 5490000, "description": "Smart case touchscreen"},
                    {"name": "JBL Live Pro 2", "price": 3990000, "description": "ANC, âm JBL Pro"},
                    {"name": "JBL Tune 760NC", "price": 1990000, "description": "ANC giá rẻ"},
                ],
                "wireless": [
                    {"name": "JBL Quantum 910", "price": 6990000, "description": "Gaming wireless ANC"},
                    {"name": "JBL Tour One M2", "price": 7490000, "description": "Over-ear ANC cao cấp"},
                ]
            },
            "bose": {
                "bluetooth": [
                    {"name": "Bose QuietComfort Ultra Earbuds", "price": 7990000, "description": "ANC tốt nhất"},
                    {"name": "Bose QuietComfort Earbuds II", "price": 6490000, "description": "ANC cá nhân hóa"},
                ],
                "wireless": [
                    {"name": "Bose QuietComfort Ultra Headphones", "price": 9990000, "description": "Over-ear ANC premium"},
                    {"name": "Bose 700", "price": 7990000, "description": "ANC + mic tốt"},
                ]
            },
            "beats": {
                "bluetooth": [
                    {"name": "Beats Studio Pro", "price": 7990000, "description": "ANC, USB-C, Hi-Res"},
                    {"name": "Beats Fit Pro", "price": 4990000, "description": "ANC, chip H1"},
                ],
                "wireless": [
                    {"name": "Beats Studio Pro", "price": 7990000, "description": "Over-ear ANC"},
                ]
            },
            "sennheiser": {
                "bluetooth": [
                    {"name": "Sennheiser Momentum 4 Wireless", "price": 8990000, "description": "60h pin, ANC"},
                    {"name": "Sennheiser Momentum True Wireless 3", "price": 5990000, "description": "Audiophile TWS"},
                ],
                "wireless": [
                    {"name": "Sennheiser Momentum 4 Wireless", "price": 8990000, "description": "60h pin"},
                ]
            }
        }
        
        brand_lower = brand.lower()
        type_lower = product_type.lower()
        
        if brand_lower in products_db and type_lower in products_db[brand_lower]:
            return products_db[brand_lower][type_lower][:limit]
        elif brand_lower in products_db:
            # Fallback to first available type for this brand
            first_type = list(products_db[brand_lower].keys())[0]
            return products_db[brand_lower][first_type][:limit]
        
        return []
