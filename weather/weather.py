import requests
from config import config  # 新增

def get_weather(is_future:bool):
    try:
        # 从配置获取API密钥和城市编码
        api_key = config.get("weather.api_key")
        city_code = config.get("weather.city_code")

        if not api_key or not city_code:
            return {"error": "天气API配置不完整（缺少api_key或city_code）"}
        
        # 获取天气数据
        if is_future==0:
            weather_response = requests.get(
                f"https://restapi.amap.com/v3/weather/weatherInfo?city={city_code}&key={api_key}",
                params={"output": "json"}
            )

        elif is_future==1:
            weather_response = requests.get(
                f"https://restapi.amap.com/v3/weather/weatherInfo?city={city_code}&key={api_key}&extensions=all",
                params={"output": "json"}
            )     

        weather_response.raise_for_status()
        weather_data = weather_response.json()
        print(weather_data)
        
        if weather_data.get("status") != "1" or "lives" not in weather_data:
            return {"error": "天气数据获取失败", "detail": weather_data}
        
        return weather_data["lives"][0]
        
    except Exception as e:
        return {"error": f"获取天气出错：{str(e)}"}